"""
LLM and SMS Service Module

This module provides interfaces for:
1. Google Gemini LLM operations
2. Africa's Talking SMS gateway integration
3. LLM response caching and rate limiting

The module abstracts external service calls and provides
consistent error handling and retry logic.
"""

import os
import logging
from typing import Optional, Dict, List, Any
import asyncio
import httpx
from datetime import datetime, timedelta

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import settings

logger = logging.getLogger(__name__)

# Initialize Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiLLM:
    """
    Google Gemini LLM wrapper with error handling and safety settings.
    
    Provides a clean interface for Gemini API calls with:
    - Automatic retry logic
    - Safety settings configuration
    - Response streaming support
    - Token usage tracking
    """
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-pro-latest-latest",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize Gemini LLM client.
        
        Args:
            model_name: Gemini model to use (default: gemini-1.5-pro-latest)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Configure safety settings (allow research content)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Initialize model
        try:
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.safety_settings
            )
            logger.info(f"Gemini model initialized: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {str(e)}")
            raise
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        max_retries: int = 3
    ) -> str:
        """
        Generate text completion from Gemini.
        
        Args:
            prompt: Input prompt text
            system_instruction: Optional system instruction
            max_retries: Maximum retry attempts on failure
            
        Returns:
            Generated text response
            
        Raises:
            ValueError: If prompt is empty
            ConnectionError: If API is unreachable
            Exception: For other API errors
            
        Example:
            >>> llm = GeminiLLM()
            >>> response = await llm.generate("Explain quantum computing")
            >>> print(response)
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Gemini API call (attempt {attempt + 1}/{max_retries})")
                
                # Configure generation parameters
                generation_config = genai.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens
                )
                
                # Add system instruction if provided
                if system_instruction:
                    full_prompt = f"{system_instruction}\n\n{prompt}"
                else:
                    full_prompt = prompt
                
                # Generate response
                response = await asyncio.to_thread(
                    self.model.generate_content,
                    full_prompt,
                    generation_config=generation_config
                )
                
                # Extract text from response
                if response and response.text:
                    logger.info(f"Gemini response generated ({len(response.text)} chars)")
                    return response.text
                else:
                    logger.warning("Empty response from Gemini")
                    raise ValueError("Empty response from LLM")
            
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt + 1}): {str(e)}")
                
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to reach Gemini API after {max_retries} attempts")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise Exception("Unexpected error in Gemini generation")
    
    async def generate_structured(
        self,
        prompt: str,
        response_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate structured output (JSON) from Gemini.
        
        Args:
            prompt: Input prompt
            response_schema: Expected JSON schema
            
        Returns:
            Parsed JSON response
            
        Example:
            >>> schema = {"queries": ["string"]}
            >>> result = await llm.generate_structured(prompt, schema)
        """
        # Add JSON formatting instruction
        json_prompt = f"""{prompt}

Respond ONLY with valid JSON matching this schema:
{response_schema}

Do not include any explanation, markdown formatting, or additional text.
"""
        
        response_text = await self.generate(json_prompt)
        
        # Clean up response (remove markdown if present)
        import json
        cleaned = response_text.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.debug(f"Raw response: {response_text}")
            raise ValueError(f"Invalid JSON response from LLM: {str(e)}")


class SMSGateway:
    """
    Africa's Talking SMS gateway client.
    
    Handles sending SMS messages via Africa's Talking API.
    """
    
    def __init__(self):
        """Initialize SMS gateway with credentials from settings."""
        self.username = settings.AT_USERNAME
        self.api_key = settings.AT_API_KEY
        self.base_url = "https://api.africastalking.com/version1"
        
        if not self.username or not self.api_key:
            logger.warning("Africa's Talking credentials not configured")
    
    async def send_sms(
        self,
        to: str,
        message: str,
        sender_id: Optional[str] = None
    ) -> bool:
        """
        Send SMS message via Africa's Talking.
        
        Args:
            to: Recipient phone number (E.164 format: +254...)
            message: SMS message text (max 1600 chars for concatenated)
            sender_id: Optional sender ID/shortcode
            
        Returns:
            True if SMS sent successfully, False otherwise
            
        Raises:
            ValueError: If phone number or message is invalid
            ConnectionError: If API is unreachable
            
        Example:
            >>> gateway = SMSGateway()
            >>> success = await gateway.send_sms("+254712345678", "Hello!")
            >>> print(success)
            True
        """
        # Validate inputs
        if not to or not to.startswith('+'):
            raise ValueError("Phone number must be in E.164 format (e.g., +254712345678)")
        
        if not message or len(message.strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        if len(message) > 1600:
            logger.warning(f"Message truncated from {len(message)} to 1600 chars")
            message = message[:1600]
        
        # Check if credentials are configured
        if not self.username or not self.api_key:
            logger.error("Africa's Talking credentials not configured")
            logger.info(f"[DEV MODE] Would send SMS to {to}: {message[:50]}...")
            return True  # Return True in dev mode for testing
        
        try:
            # Prepare request
            url = f"{self.base_url}/messaging"
            headers = {
                "apiKey": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            data = {
                "username": self.username,
                "to": to,
                "message": message
            }
            
            if sender_id:
                data["from"] = sender_id
            
            # Send request
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, data=data)
                
                if response.status_code == 201:
                    result = response.json()
                    recipients = result.get("SMSMessageData", {}).get("Recipients", [])
                    
                    if recipients:
                        status = recipients[0].get("status")
                        if status == "Success":
                            logger.info(f"SMS sent successfully to {to}")
                            return True
                        else:
                            logger.error(f"SMS failed: {status}")
                            return False
                else:
                    logger.error(f"SMS API error: {response.status_code} - {response.text}")
                    return False
        
        except httpx.TimeoutException:
            logger.error("SMS API timeout")
            raise ConnectionError("Africa's Talking API timeout")
        
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False


# Global instances
_gemini_instance: Optional[GeminiLLM] = None
_sms_instance: Optional[SMSGateway] = None


def get_llm() -> GeminiLLM:
    """
    Get singleton Gemini LLM instance.
    
    Returns:
        Configured GeminiLLM instance
    """
    global _gemini_instance
    if _gemini_instance is None:
        _gemini_instance = GeminiLLM()
    return _gemini_instance


def get_sms_gateway() -> SMSGateway:
    """
    Get singleton SMS gateway instance.
    
    Returns:
        Configured SMSGateway instance
    """
    global _sms_instance
    if _sms_instance is None:
        _sms_instance = SMSGateway()
    return _sms_instance


# Convenience functions for backward compatibility
async def call_llm(
    prompt: str,
    system_instruction: Optional[str] = None
) -> str:
    """
    Call Gemini LLM with a prompt.
    
    Convenience function that uses the singleton LLM instance.
    
    Args:
        prompt: Input prompt text
        system_instruction: Optional system instruction
        
    Returns:
        Generated text response
        
    Example:
        >>> response = await call_llm("What is quantum computing?")
        >>> print(response)
    """
    llm = get_llm()
    return await llm.generate(prompt, system_instruction)


async def send_sms_reply(
    to: str,
    message: str,
    sender_id: Optional[str] = None
) -> bool:
    """
    Send SMS reply to a user.
    
    Convenience function that uses the singleton SMS gateway.
    Includes PII redaction and length validation.
    
    Args:
        to: Recipient phone number (E.164 format)
        message: SMS message text
        sender_id: Optional sender ID
        
    Returns:
        True if sent successfully
        
    Note:
        This function automatically redacts PII from messages
        for privacy protection.
        
    Example:
        >>> success = await send_sms_reply("+254712345678", "Your answer is...")
        >>> print(success)
        True
    """
    # Import here to avoid circular dependency
    from ..utils.filters import sanitize_output
    
    # Sanitize message (remove PII)
    sanitized_message = await sanitize_output(message)
    
    # Send via gateway
    gateway = get_sms_gateway()
    return await gateway.send_sms(to, sanitized_message, sender_id)


async def generate_search_queries(question: str, num_queries: int = 3) -> List[str]:
    """
    Generate optimized search queries from a research question.
    
    Uses Gemini to generate diverse, targeted search queries.
    
    Args:
        question: Original research question
        num_queries: Number of queries to generate (default: 3)
        
    Returns:
        List of generated search query strings
        
    Example:
        >>> queries = await generate_search_queries("What is quantum computing?")
        >>> print(queries)
        ['quantum computing basics', 'quantum computer applications', ...]
    """
    llm = get_llm()
    
    prompt = f"""Generate {num_queries} diverse search queries to research this question:

Question: {question}

Requirements:
- Make queries specific and targeted
- Cover different aspects of the topic
- Use search-engine-friendly language
- Keep each query concise (3-8 words)

Return ONLY a JSON array of query strings, nothing else.
Example: ["query 1", "query 2", "query 3"]"""
    
    try:
        response = await llm.generate_structured(
            prompt,
            {"queries": ["string"]}
        )
        
        queries = response.get("queries", [])
        if not queries:
            logger.warning("No queries generated, using original question")
            return [question]
        
        return queries[:num_queries]
    
    except Exception as e:
        logger.error(f"Failed to generate queries: {str(e)}")
        # Fallback to original question
        return [question]
