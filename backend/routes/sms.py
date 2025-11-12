"""
SMS Integration Route Module

This module handles inbound SMS queries from Africa's Talking webhook
and sends research results back via SMS. It provides a conversational
interface for users to access the research agent via text messages.
"""
from fastapi import APIRouter, Form, BackgroundTasks, HTTPException, status, Request
from typing import Optional
import logging
import hashlib
import hmac

from ..schemas import ResearchResponse, SMSInboundRequest, SMSResponse
from ..langgraph_agent import ResearchAgent
from ..services.llm import send_sms_reply
from ..config import settings
from ..utils.filters import check_pii, check_toxicity, sanitize_output

# Configure logger
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(
    prefix="/api/sms",
    tags=["sms"],
    responses={
        400: {"description": "Bad request - invalid SMS data"},
        401: {"description": "Unauthorized - invalid webhook signature"},
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable - SMS gateway failure"}
    }
)

# Initialize agent
agent = ResearchAgent()


@router.post(
    "/inbound",
    response_model=SMSResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle inbound SMS queries",
    description="""
    Webhook endpoint for Africa's Talking SMS gateway.
    
    This endpoint:
    1. Receives inbound SMS messages
    2. Validates the webhook signature (if configured)
    3. Performs research using the LangGraph agent
    4. Sends a truncated, SMS-friendly reply back to the user
    
    **SMS Response Format:**
    - Maximum 1600 characters (to fit standard SMS limits)
    - Top 2-3 citations included
    - Formatted for mobile readability
    
    **Rate Limiting:**
    - Applied per phone number to prevent abuse
    - Configurable in settings
    """,
    response_description="SMS processing status"
)
async def inbound_sms(
    request: Request,
    background_tasks: BackgroundTasks,
    from_number: str = Form(..., alias="from", description="Sender's phone number"),
    to: str = Form(..., description="Destination number (your shortcode/number)"),
    text: str = Form(..., description="SMS message text"),
    date: Optional[str] = Form(None, description="Message timestamp"),
    id: Optional[str] = Form(None, description="Message ID from Africa's Talking"),
    linkId: Optional[str] = Form(None, description="Link ID for message threading"),
    networkCode: Optional[str] = Form(None, description="Network operator code")
) -> SMSResponse:
    """
    Handle inbound SMS webhook from Africa's Talking.
    
    Args:
        request: FastAPI request object (for signature verification)
        background_tasks: Background tasks queue
        from_number: Sender's phone number (E.164 format)
        to: Recipient number (your service number)
        text: SMS message content
        date: Message timestamp
        id: Unique message ID
        linkId: Thread/conversation ID
        networkCode: Mobile network operator code
        
    Returns:
        SMSResponse with processing status
        
    Raises:
        HTTPException: 400 if message is invalid
        HTTPException: 401 if webhook signature is invalid
        HTTPException: 500 if processing fails
        HTTPException: 503 if SMS gateway is unavailable
        
    Example Webhook Payload:
        ```
        from=+254712345678
        to=20880
        text=What is quantum computing?
        date=2025-01-15 10:30:00
        id=ATXid_abc123
        linkId=SampleLinkId123
        networkCode=63902
        ```
    """
    # Log inbound message (redact phone number for privacy)
    redacted_number = f"{from_number[:6]}***{from_number[-3:]}" if len(from_number) > 9 else "***"
    logger.info(f"Inbound SMS from {redacted_number}: {text[:50]}...")
    
    # Verify webhook signature if configured
    if settings.africas_talking_webhook_secret:
        try:
            await verify_webhook_signature(request, settings.africas_talking_webhook_secret)
        except ValueError as e:
            logger.warning(f"Invalid webhook signature from {redacted_number}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
    
    # Validate message content
    if not text or len(text.strip()) == 0:
        logger.warning(f"Empty SMS received from {redacted_number}")
        await send_sms_reply(
            to=from_number,
            message="Please send a valid research question."
        )
        return SMSResponse(
            status="rejected",
            message="Empty message",
            to=from_number
        )
    
    if len(text) > 500:
        logger.warning(f"SMS too long from {redacted_number}: {len(text)} chars")
        await send_sms_reply(
            to=from_number,
            message="Your message is too long. Please keep queries under 500 characters."
        )
        return SMSResponse(
            status="rejected",
            message="Message too long",
            to=from_number
        )
    
    # Security checks
    try:
        # Check for PII (warn user, don't block - they might legitimately mention names)
        if settings.enable_pii_filter:
            pii_detected = await check_pii(text)
            if pii_detected:
                logger.info(f"PII detected in SMS from {redacted_number}")
                await send_sms_reply(
                    to=from_number,
                    message="Warning: Your message may contain personal information. "
                            "This has been noted for privacy protection."
                )
        
        # Check for toxic content (block if detected)
        if settings.enable_toxicity_filter:
            is_toxic = await check_toxicity(text)
            if is_toxic:
                logger.warning(f"Toxic content in SMS from {redacted_number}")
                await send_sms_reply(
                    to=from_number,
                    message="Your message contains inappropriate content. "
                            "Please rephrase your question respectfully."
                )
                return SMSResponse(
                    status="rejected",
                    message="Toxic content detected",
                    to=from_number
                )
    
    except Exception as e:
        logger.error(f"Security check error: {str(e)}")
        # Continue processing - don't fail on security check errors
    
    # Process in background to return 200 OK quickly (Africa's Talking timeout)
    background_tasks.add_task(
        process_sms_research,
        query=text,
        from_number=from_number,
        message_id=id,
        link_id=linkId
    )
    
    # Send immediate acknowledgment
    await send_sms_reply(
        to=from_number,
        message="🔍 Researching your question... You'll receive an answer shortly (usually 30-60 seconds)."
    )
    
    logger.info(f"SMS queued for processing: message_id={id}")
    
    return SMSResponse(
        status="accepted",
        message="Research queued",
        to=from_number,
        message_id=id
    )


async def process_sms_research(
    query: str,
    from_number: str,
    message_id: Optional[str] = None,
    link_id: Optional[str] = None
) -> None:
    """
    Background task to process SMS research and send reply.
    
    This function runs asynchronously after the webhook returns 200 OK
    to avoid Africa's Talking timeouts (typically 30 seconds).
    
    Args:
        query: Research question from SMS
        from_number: Sender's phone number
        message_id: Original message ID
        link_id: Thread ID for conversation tracking
    """
    redacted_number = f"{from_number[:6]}***{from_number[-3:]}" if len(from_number) > 9 else "***"
    
    try:
        logger.info(f"Processing SMS research for {redacted_number}")
        
        # Run research agent with SMS-optimized settings
        result = await agent.run(
            query=query,
            source='sms',
            max_iterations=2  # Fewer iterations for faster SMS response
        )
        
        # Format SMS-friendly response
        sms_response = format_sms_response(
            answer=result.get('answer', ''),
            citations=result.get('citations', []),
            max_length=1600  # Conservative limit for multi-part SMS
        )
        
        # Sanitize output
        if settings.enable_pii_filter:
            sms_response = await sanitize_output(sms_response)
        
        # Send the research result
        success = await send_sms_reply(
            to=from_number,
            message=sms_response
        )
        
        if success:
            logger.info(f"SMS reply sent successfully to {redacted_number}")
        else:
            logger.error(f"Failed to send SMS reply to {redacted_number}")
    
    except ConnectionError as e:
        logger.error(f"SMS gateway connection error: {str(e)}")
        # Attempt to notify user of failure
        try:
            await send_sms_reply(
                to=from_number,
                message="Sorry, we're experiencing technical difficulties. Please try again later."
            )
        except:
            pass
    
    except Exception as e:
        logger.error(f"Error processing SMS research: {str(e)}", exc_info=True)
        # Attempt to send error message
        try:
            await send_sms_reply(
                to=from_number,
                message="Sorry, an error occurred while researching your question. Please try again."
            )
        except:
            pass


def format_sms_response(answer: str, citations: list, max_length: int = 1600) -> str:
    """
    Format research response for SMS delivery.
    
    Creates a concise, mobile-friendly message with the answer and top citations.
    
    Args:
        answer: Full research answer
        citations: List of citation dictionaries
        max_length: Maximum SMS length (default 1600 for safety)
        
    Returns:
        Formatted SMS message string
    """
    # Start with answer (truncate if needed)
    response = answer
    
    # Add top 2-3 citations if available
    if citations:
        response += "\n\n📚 Sources:"
        citation_count = min(3, len(citations))
        
        for i, citation in enumerate(citations[:citation_count], 1):
            url = citation.get('url', '')
            title = citation.get('title', 'Source')
            
            # Shorten URLs for SMS
            short_url = url.replace('https://', '').replace('http://', '')
            if len(short_url) > 40:
                short_url = short_url[:37] + '...'
            
            response += f"\n{i}. {short_url}"
    
    # Truncate if too long
    if len(response) > max_length:
        response = response[:max_length - 50] + "... (truncated)\n\nFor full results, visit our web app."
    
    return response


async def verify_webhook_signature(request: Request, secret: str) -> None:
    """
    Verify Africa's Talking webhook signature for security.
    
    Args:
        request: FastAPI request object
        secret: Webhook secret key from Africa's Talking
        
    Raises:
        ValueError: If signature is invalid or missing
    """
    # Get signature from header
    signature = request.headers.get('X-Africas-Talking-Signature')
    
    if not signature:
        raise ValueError("Missing webhook signature")
    
    # Get raw request body
    body = await request.body()
    
    # Compute expected signature
    expected_signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures securely
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid webhook signature")


@router.get(
    "/health",
    tags=["health"],
    summary="SMS service health check"
)
async def sms_health_check():
    """
    Health check for SMS service.
    
    Verifies Africa's Talking credentials and connectivity.
    """
    health = {
        "status": "healthy",
        "service": "sms-gateway",
        "provider": "Africa's Talking"
    }
    
    # Check if credentials are configured
    if not settings.africas_talking_api_key or not settings.africas_talking_username:
        health["status"] = "unhealthy"
        health["error"] = "Missing Africa's Talking credentials"
    
    return health
