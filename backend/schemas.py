"""
Pydantic Schema Models

This module defines all request and response data models for the Research Agent API.
These schemas provide automatic validation, serialization, and OpenAPI documentation.

The schemas are organized by functionality:
- Research API models (ResearchRequest, ResearchResponse)
- SMS integration models (SMSInboundRequest, SMSResponse)
- Shared data models (Citation, TimelineStep)
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl
from datetime import datetime
from enum import Enum


class QuerySource(str, Enum):
    """Enumeration of possible query sources for tracking and analytics."""
    WEB_UI = "web_ui"
    SMS = "sms"
    API = "api"
    MOBILE_APP = "mobile_app"


class ResearchRequest(BaseModel):
    """
    Request model for research queries.
    
    Attributes:
        query: The research question or topic to investigate
        source: Origin of the request (web_ui, sms, api, mobile_app)
        max_iterations: Maximum number of reflection/iteration loops
        include_timeline: Whether to include detailed timeline in response
        
    Example:
        ```json
        {
            "query": "What are the latest developments in quantum computing?",
            "source": "web_ui",
            "max_iterations": 3,
            "include_timeline": true
        }
        ```
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Research question or query text",
        example="What are the latest developments in quantum computing?"
    )
    source: QuerySource = Field(
        default=QuerySource.WEB_UI,
        description="Source of the query for tracking purposes"
    )
    max_iterations: Optional[int] = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of research iteration loops"
    )
    include_timeline: bool = Field(
        default=True,
        description="Include step-by-step timeline in response"
    )
    
    @validator('query')
    def validate_query(cls, v):
        """Validate and sanitize query string."""
        # Remove leading/trailing whitespace
        v = v.strip()
        
        # Ensure query is not empty after stripping
        if not v:
            raise ValueError("Query cannot be empty or only whitespace")
        
        # Check for excessive newlines or special characters
        if v.count('\n') > 5:
            raise ValueError("Query contains too many line breaks")
        
        return v
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "query": "What are the environmental impacts of electric vehicles?",
                "source": "web_ui",
                "max_iterations": 3,
                "include_timeline": True
            }
        }


class Citation(BaseModel):
    """
    Citation/source reference model.
    
    Represents a source document or webpage that supports the research answer.
    
    Attributes:
        title: Title of the source document
        url: Web URL of the source
        snippet: Relevant excerpt or snippet from the source
        source: Source provider name (e.g., "Google", "Wikipedia")
        relevance_score: Confidence score for citation relevance (0.0-1.0)
        accessed_at: Timestamp when the source was accessed
        
    Example:
        ```json
        {
            "title": "Quantum Computing Breakthrough 2025",
            "url": "https://example.com/article",
            "snippet": "Recent developments show...",
            "source": "Tech News Daily",
            "relevance_score": 0.95,
            "accessed_at": "2025-01-15T10:30:00Z"
        }
        ```
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Title of the cited source",
        example="Quantum Computing Advances in 2025"
    )
    url: str = Field(
        ...,
        description="URL of the source document",
        example="https://example.com/quantum-computing-2025"
    )
    snippet: Optional[str] = Field(
        None,
        max_length=1000,
        description="Relevant excerpt from the source",
        example="Researchers have achieved a breakthrough in quantum error correction..."
    )
    source: Optional[str] = Field(
        None,
        max_length=200,
        description="Name of the source provider or publication",
        example="Nature Journal"
    )
    relevance_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Relevance score from 0.0 to 1.0"
    )
    accessed_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when source was accessed"
    )
    
    @validator('url')
    def validate_url(cls, v):
        """Ensure URL is properly formatted."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "title": "Quantum Computing Breakthrough",
                "url": "https://example.com/article",
                "snippet": "Recent developments show significant progress...",
                "source": "Tech News",
                "relevance_score": 0.92,
                "accessed_at": "2025-01-15T10:30:00Z"
            }
        }


class TimelineStep(BaseModel):
    """
    Timeline step model representing one stage in the research process.
    
    Tracks the agent's activities during research execution.
    
    Attributes:
        step: Name/type of the step
        description: Human-readable description
        details: Additional structured details about the step
        timestamp: When the step occurred
        duration_ms: How long the step took in milliseconds
        status: Status of the step (success, error, skipped)
        
    Example:
        ```json
        {
            "step": "query_generation",
            "description": "Generated 3 search queries",
            "details": {"queries": ["query1", "query2", "query3"]},
            "timestamp": "2025-01-15T10:30:00Z",
            "duration_ms": 1250,
            "status": "success"
        }
        ```
    """
    step: str = Field(
        ...,
        description="Step identifier or name",
        example="web_search"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the step",
        example="Performed web search with 3 queries"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional structured information about the step"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the step was executed"
    )
    duration_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Duration of the step in milliseconds"
    )
    status: str = Field(
        default="success",
        description="Step execution status",
        example="success"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "step": "reflection",
                "description": "Reflected on search results quality",
                "details": {
                    "decision": "sufficient_results",
                    "num_sources": 8
                },
                "timestamp": "2025-01-15T10:30:15Z",
                "duration_ms": 2100,
                "status": "success"
            }
        }


class ResearchResponse(BaseModel):
    """
    Response model for completed research queries.
    
    Contains the synthesized answer, supporting citations, and execution timeline.
    
    Attributes:
        answer: The synthesized research answer
        citations: List of sources supporting the answer
        timeline: Execution timeline showing agent steps
        query: The original query (echoed back)
        completed_at: Timestamp when research completed
        total_duration_ms: Total execution time in milliseconds
        metadata: Additional metadata about the research
        
    Example:
        ```json
        {
            "answer": "Quantum computing has seen major advances...",
            "citations": [...],
            "timeline": [...],
            "query": "What are quantum computing developments?",
            "completed_at": "2025-01-15T10:30:20Z",
            "total_duration_ms": 15000,
            "metadata": {"iterations": 2, "sources_found": 12}
        }
        ```
    """
    answer: str = Field(
        ...,
        min_length=1,
        description="Synthesized research answer with citations",
        example="Quantum computing has seen significant advances in 2025..."
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="List of source citations supporting the answer"
    )
    timeline: List[TimelineStep] = Field(
        default_factory=list,
        description="Detailed timeline of agent execution steps"
    )
    query: Optional[str] = Field(
        None,
        description="Original query (echoed back for reference)"
    )
    completed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when research completed"
    )
    total_duration_ms: Optional[int] = Field(
        None,
        ge=0,
        description="Total execution time in milliseconds"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the research process"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "answer": "Quantum computing has advanced significantly...",
                "citations": [
                    {
                        "title": "Quantum Breakthrough",
                        "url": "https://example.com/article",
                        "snippet": "Researchers achieved...",
                        "source": "Tech Journal"
                    }
                ],
                "timeline": [
                    {
                        "step": "query_generation",
                        "description": "Generated search queries",
                        "status": "success"
                    }
                ],
                "query": "What are quantum computing developments?",
                "completed_at": "2025-01-15T10:30:20Z",
                "total_duration_ms": 15000
            }
        }


class SMSInboundRequest(BaseModel):
    """
    SMS webhook request from Africa's Talking.
    
    Represents an inbound SMS message received via the webhook.
    
    Attributes:
        from_number: Sender's phone number (E.164 format)
        to: Destination number (your service number)
        text: SMS message content
        date: Message timestamp from provider
        id: Unique message ID from Africa's Talking
        linkId: Thread/conversation ID
        networkCode: Mobile network operator code
    """
    from_number: str = Field(
        ...,
        alias="from",
        description="Sender's phone number in E.164 format",
        example="+254712345678"
    )
    to: str = Field(
        ...,
        description="Destination number (your shortcode or long number)",
        example="20880"
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="SMS message text",
        example="What is quantum computing?"
    )
    date: Optional[str] = Field(
        None,
        description="Message timestamp from provider",
        example="2025-01-15 10:30:00"
    )
    id: Optional[str] = Field(
        None,
        description="Unique message ID from Africa's Talking",
        example="ATXid_abc123xyz"
    )
    linkId: Optional[str] = Field(
        None,
        description="Link ID for message threading",
        example="SampleLinkId123"
    )
    networkCode: Optional[str] = Field(
        None,
        description="Mobile network operator code",
        example="63902"
    )
    
    class Config:
        """Pydantic model configuration."""
        allow_population_by_field_name = True
        schema_extra = {
            "example": {
                "from": "+254712345678",
                "to": "20880",
                "text": "What is artificial intelligence?",
                "date": "2025-01-15 10:30:00",
                "id": "ATXid_abc123",
                "linkId": "SampleLinkId",
                "networkCode": "63902"
            }
        }


class SMSResponse(BaseModel):
    """
    Response model for SMS webhook processing.
    
    Indicates the status of SMS processing.
    
    Attributes:
        status: Processing status (accepted, rejected, failed)
        message: Human-readable status message
        to: Phone number the response pertains to
        message_id: Original message ID for tracking
        error: Error details if processing failed
    """
    status: str = Field(
        ...,
        description="Processing status",
        example="accepted"
    )
    message: str = Field(
        ...,
        description="Human-readable status message",
        example="Research queued successfully"
    )
    to: str = Field(
        ...,
        description="Phone number the response pertains to",
        example="+254712345678"
    )
    message_id: Optional[str] = Field(
        None,
        description="Original message ID for tracking"
    )
    error: Optional[str] = Field(
        None,
        description="Error details if processing failed"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "accepted",
                "message": "Research queued successfully",
                "to": "+254712345678",
                "message_id": "ATXid_abc123"
            }
        }


class HealthCheckResponse(BaseModel):
    """
    Health check response model.
    
    Provides service health status and component checks.
    
    Attributes:
        status: Overall health status (healthy, degraded, unhealthy)
        service: Service name
        components: Dictionary of component health statuses
        timestamp: Health check timestamp
        version: Application version
    """
    status: str = Field(
        ...,
        description="Overall health status",
        example="healthy"
    )
    service: str = Field(
        ...,
        description="Service name",
        example="research-api"
    )
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Component health statuses"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Health check timestamp"
    )
    version: Optional[str] = Field(
        None,
        description="Application version"
    )
    
    class Config:
        """Pydantic model configuration."""
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "research-api",
                "components": {
                    "database": "healthy",
                    "redis": "healthy",
                    "llm": "healthy"
                },
                "timestamp": "2025-01-15T10:30:00Z",
                "version": "1.0.0"
            }
        }
