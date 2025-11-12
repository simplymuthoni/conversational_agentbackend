"""
Research API Route Module

This module provides the main research endpoint for the conversational agent.
It accepts user queries, orchestrates the LangGraph research workflow, and returns
synthesized answers with citations and timeline steps.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, status
from typing import Dict, Any
import logging

from ..schemas import ResearchRequest, ResearchResponse, Citation, TimelineStep
from ..langgraph_agent import ResearchAgent
from ..config import settings
from ..utils.filters import (
    check_prompt_injection,
    check_pii,
    check_toxicity,
    sanitize_output
)

# Configure logger
logger = logging.getLogger(__name__)

# Initialize router with tags and prefix for OpenAPI documentation
router = APIRouter(
    prefix="/api",
    tags=["research"],
    responses={
        400: {"description": "Bad request - invalid query"},
        500: {"description": "Internal server error - agent failure"},
        503: {"description": "Service unavailable - external API failure"}
    }
)

# Initialize agent (singleton pattern - consider dependency injection for production)
agent = ResearchAgent()


@router.post(
    "/research",
    response_model=ResearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Run research query",
    description="""
    Execute a research query through the LangGraph-powered agent.
    
    The agent will:
    1. Generate optimized search queries
    2. Perform web searches
    3. Reflect on results and iterate if needed
    4. Synthesize a comprehensive answer with citations
    
    **Safety Features:**
    - Prompt injection detection
    - PII filtering
    - Toxicity checking
    - Hallucination validation
    
    **Response includes:**
    - Synthesized answer
    - List of source citations
    - Activity timeline showing agent steps
    """,
    response_description="Research results with answer, citations, and timeline"
)
async def run_research(
    req: ResearchRequest,
    background_tasks: BackgroundTasks
) -> ResearchResponse:
    """
    Run a research query and return synthesized results.
    
    Args:
        req: ResearchRequest containing the query and optional parameters
        background_tasks: FastAPI background tasks for async operations
        
    Returns:
        ResearchResponse with answer, citations, and timeline
        
    Raises:
        HTTPException: 400 if query is invalid or contains security issues
        HTTPException: 500 if agent execution fails
        HTTPException: 503 if external APIs are unavailable
        
    Example:
        ```json
        POST /api/research
        {
            "query": "What are the latest developments in quantum computing?",
            "source": "web_ui",
            "max_iterations": 3
        }
        ```
    """
    # Validate query presence and length
    if not req.query or len(req.query.strip()) == 0:
        logger.warning("Empty query received")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required and cannot be empty"
        )
    
    if len(req.query) > 1000:
        logger.warning(f"Query too long: {len(req.query)} characters")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query exceeds maximum length of 1000 characters"
        )
    
    # Security checks
    try:
        # Check for prompt injection attempts
        if settings.enable_prompt_injection_check:
            injection_detected = await check_prompt_injection(req.query)
            if injection_detected:
                logger.warning(f"Prompt injection detected in query: {req.query[:50]}...")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query contains potentially malicious content"
                )
        
        # Check for PII in query
        if settings.enable_pii_filter:
            pii_detected = await check_pii(req.query)
            if pii_detected:
                logger.warning("PII detected in query")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query contains personally identifiable information. Please remove sensitive data."
                )
        
        # Check for toxic content
        if settings.enable_toxicity_filter:
            is_toxic = await check_toxicity(req.query)
            if is_toxic:
                logger.warning("Toxic content detected in query")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Query contains inappropriate or harmful content"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during security checks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate query"
        )
    
    # Execute research agent
    try:
        logger.info(f"Starting research for query: {req.query[:50]}... (source: {req.source})")
        
        # Run agent synchronously for MVP
        # TODO: For production, implement async job queue with job IDs
        result = await agent.run(
            query=req.query,
            source=req.source,
            max_iterations=req.max_iterations
        )
        
        # Sanitize output (remove any PII that might have been scraped)
        if settings.enable_pii_filter:
            result['answer'] = await sanitize_output(result['answer'])
            for citation in result.get('citations', []):
                if 'snippet' in citation:
                    citation['snippet'] = await sanitize_output(citation['snippet'])
        
        logger.info(f"Research completed successfully with {len(result.get('citations', []))} citations")
        
        # Log to analytics/monitoring in background
        background_tasks.add_task(
            log_research_metrics,
            query=req.query,
            source=req.source,
            num_citations=len(result.get('citations', [])),
            num_steps=len(result.get('timeline', []))
        )
        
        return ResearchResponse(**result)
    
    except ValueError as e:
        logger.error(f"Invalid agent response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent returned invalid response: {str(e)}"
        )
    
    except ConnectionError as e:
        logger.error(f"External API connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External services are temporarily unavailable. Please try again later."
        )
    
    except Exception as e:
        logger.error(f"Unexpected error during research: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request"
        )


async def log_research_metrics(
    query: str,
    source: str,
    num_citations: int,
    num_steps: int
) -> None:
    """
    Log research metrics for monitoring and analytics.
    
    This is a background task that logs metrics without blocking the response.
    
    Args:
        query: The research query
        source: Source of the query (web_ui, sms, api)
        num_citations: Number of citations in the response
        num_steps: Number of timeline steps executed
    """
    try:
        # TODO: Implement actual metrics logging (Prometheus, DataDog, etc.)
        logger.info(
            f"Metrics - Query: {query[:30]}..., Source: {source}, "
            f"Citations: {num_citations}, Steps: {num_steps}"
        )
    except Exception as e:
        logger.error(f"Failed to log metrics: {str(e)}")


@router.get(
    "/health",
    tags=["health"],
    summary="Health check endpoint",
    description="Check if the research API is operational and can reach dependencies"
)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.
    
    Returns:
        Dictionary with health status and component checks
    """
    health_status = {
        "status": "healthy",
        "service": "research-api",
        "components": {}
    }
    
    try:
        # Check agent initialization
        health_status["components"]["agent"] = "healthy" if agent else "unavailable"
        
        # TODO: Add checks for:
        # - Database connection
        # - Redis connection
        # - External API availability (Gemini, search)
        
        return health_status
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return health_status
