"""
FastAPI Application - Research Agent Backend

This is the main entry point for the Research-Augmented Conversational Agent API.
It configures FastAPI with middleware, routes, and lifecycle management.

Features:
- RESTful API endpoints for research and SMS
- CORS middleware for frontend integration
- Database and cache initialization
- Health check endpoints
- Error handling and logging
- OpenAPI documentation
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .routes import research, sms
from .config import settings
from .utils.db import init_db, close_db, db_manager
from .utils.cache import init_cache, close_cache, cache_manager

# Configure logging
logging.basicConfig(
    level=settings.get_log_level_int(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application.
    Initializes database connections, cache, and other resources.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Control during application runtime
    """
    # Startup
    logger.info("=" * 60)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Search Provider: {settings.search_provider}")
    logger.info("=" * 60)
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {str(e)}")
        if settings.is_production:
            raise  # Fail fast in production
        logger.warning("Continuing without database in development mode")
    
    try:
        # Initialize cache
        logger.info("Initializing cache...")
        await init_cache()
        logger.info("✓ Cache initialized")
    except Exception as e:
        logger.error(f"✗ Cache initialization failed: {str(e)}")
        if settings.is_production:
            raise
        logger.warning("Continuing without cache in development mode")
    
    # Log feature flags
    logger.info("Feature flags:")
    logger.info(f"  - SMS: {settings.enable_sms}")
    logger.info(f"  - Caching: {settings.enable_caching}")
    logger.info(f"  - Metrics: {settings.enable_metrics}")
    logger.info(f"  - PII Filter: {settings.enable_pii_filter}")
    logger.info(f"  - Toxicity Filter: {settings.enable_toxicity_filter}")
    
    logger.info("=" * 60)
    logger.info("Application startup complete!")
    logger.info(f"API available at http://{settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"Docs available at http://{settings.APP_HOST}:{settings.APP_PORT}/docs")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("=" * 60)
    logger.info("Shutting down application...")
    logger.info("=" * 60)
    
    try:
        logger.info("Closing database connections...")
        await close_db()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing database: {str(e)}")
    
    try:
        logger.info("Closing cache connections...")
        await close_cache()
        logger.info("✓ Cache connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing cache: {str(e)}")
    
    logger.info("=" * 60)
    logger.info("Shutdown complete")
    logger.info("=" * 60)


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
    Research-Augmented Conversational Agent API
    
    This API provides intelligent research capabilities using LangGraph and Google Gemini.
    
    ## Features
    
    * **Research Queries**: Submit questions and get comprehensive, cited answers
    * **SMS Integration**: Query via SMS using Africa's Talking
    * **Web Search**: Multiple search provider options (Gemini, SerpAPI, Brave, Google)
    * **Safety Filters**: PII detection, toxicity filtering, hallucination checks
    * **Iterative Research**: Automatic reflection and iteration for quality
    
    ## Authentication
    
    Currently, this API does not require authentication. For production deployment,
    implement API key authentication or OAuth2.
    
    ## Rate Limiting
    
    Rate limiting is enabled by default:
    - 100 requests per hour per IP/user
    - Configurable via environment variables
    
    ## Support
    
    For issues or questions, please contact the development team or open an issue
    on the project repository.
    """,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ==================== Middleware ====================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite default
        # Add your production frontend URLs here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.
    
    Args:
        request: Incoming request
        call_next: Next middleware in chain
        
    Returns:
        Response from next middleware
    """
    # Log request
    logger.info(f"{request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code}")
    
    return response


# ==================== Exception Handlers ====================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions.
    
    Args:
        request: Request that caused the exception
        exc: HTTP exception
        
    Returns:
        JSON error response
    """
    logger.error(f"HTTP {exc.status_code}: {exc.detail} - {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "status_code": exc.status_code,
                "message": exc.detail,
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle request validation errors.
    
    Args:
        request: Request that failed validation
        exc: Validation error
        
    Returns:
        JSON error response with validation details
    """
    logger.error(f"Validation error: {exc.errors()} - {request.url.path}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "status_code": 422,
                "message": "Validation error",
                "details": exc.errors(),
                "path": str(request.url.path)
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions.
    
    Args:
        request: Request that caused the exception
        exc: Exception
        
    Returns:
        JSON error response
    """
    logger.error(f"Unhandled exception: {str(exc)} - {request.url.path}", exc_info=True)
    
    # Don't expose internal errors in production
    if settings.is_production:
        message = "An internal server error occurred"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "status_code": 500,
                "message": message,
                "path": str(request.url.path)
            }
        }
    )


# ==================== Routes ====================

# Include routers
app.include_router(research.router, tags=["Research"])
app.include_router(sms.router, tags=["SMS"])


# ==================== Health & Status Endpoints ====================

@app.get(
    "/",
    summary="Root endpoint",
    description="Returns basic API information",
    tags=["Info"]
)
async def root():
    """
    Root endpoint returning API information.
    
    Returns:
        API metadata
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get(
    "/api/health",
    summary="Health check endpoint",
    description="Check API and dependencies health status",
    tags=["Health"],
    response_model=Dict[str, Any]
)
async def health_check():
    """
    Comprehensive health check for all services.
    
    Checks:
    - API status
    - Database connectivity
    - Cache connectivity
    - Search provider configuration
    
    Returns:
        Health status for all components
    """
    health_status = {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "components": {}
    }
    
    # Check database
    try:
        db_healthy = await db_manager.health_check()
        health_status["components"]["database"] = "healthy" if db_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check cache
    try:
        cache_healthy = await cache_manager.health_check()
        health_status["components"]["cache"] = "healthy" if cache_healthy else "unhealthy"
    except Exception as e:
        logger.error(f"Cache health check failed: {str(e)}")
        health_status["components"]["cache"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check search provider
    health_status["components"]["search_provider"] = {
        "type": settings.search_provider,
        "configured": True if settings.search_provider == "mock" or settings.search_provider == "gemini" or settings.search_api_key else False
    }
    
    # Check SMS
    if settings.enable_sms:
        sms_configured = bool(settings.AT_USERNAME and settings.AT_API_KEY)
        health_status["components"]["sms"] = "configured" if sms_configured else "not_configured"
    
    # Overall status
    if health_status["components"]["database"] == "unhealthy":
        health_status["status"] = "unhealthy"
    
    return health_status


@app.get(
    "/api/status",
    summary="Detailed status information",
    description="Get detailed application status and configuration",
    tags=["Health"]
)
async def status():
    """
    Detailed application status and configuration.
    
    Returns:
        Comprehensive status information
    """
    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV
        },
        "configuration": {
            "search_provider": settings.search_provider,
            "max_search_results": settings.max_search_results,
            "max_reflection_iterations": settings.max_reflection_iterations,
            "llm_model": settings.llm_model
        },
        "features": {
            "sms": settings.enable_sms,
            "caching": settings.enable_caching,
            "metrics": settings.enable_metrics,
            "pii_filter": settings.enable_pii_filter,
            "toxicity_filter": settings.enable_toxicity_filter,
            "hallucination_check": settings.enable_hallucination_check,
            "bias_detection": settings.enable_bias_detection
        },
        "rate_limiting": {
            "enabled": settings.rate_limit_enabled,
            "requests_per_window": settings.rate_limit_requests,
            "window_seconds": settings.rate_limit_window
        }
    }


@app.get(
    "/api/metrics",
    summary="Application metrics",
    description="Get basic application metrics (if enabled)",
    tags=["Metrics"]
)
async def metrics():
    """
    Basic application metrics.
    
    Returns:
        Application metrics if enabled
    """
    if not settings.enable_metrics:
        return {"error": "Metrics not enabled"}
    
    # TODO: Implement proper metrics collection (Prometheus, etc.)
    return {
        "enabled": True,
        "note": "Detailed metrics implementation pending"
    }


# ==================== Development Endpoints ====================

if settings.is_development:
    @app.get(
        "/api/debug/config",
        summary="Configuration debug (dev only)",
        description="View current configuration (development only)",
        tags=["Debug"],
        include_in_schema=settings.is_development
    )
    async def debug_config():
        """
        Debug endpoint to view configuration.
        
        Only available in development mode.
        
        Returns:
            Sanitized configuration
        """
        return {
            "app": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "env": settings.APP_ENV,
                "host": settings.APP_HOST,
                "port": settings.APP_PORT,
                "log_level": settings.LOG_LEVEL
            },
            "database": {
                "host": settings.POSTGRES_HOST,
                "port": settings.POSTGRES_PORT,
                "db": settings.POSTGRES_DB,
                "user": settings.POSTGRES_USER
            },
            "cache": {
                "url": settings.REDIS_URL
            },
            "search": {
                "provider": settings.search_provider,
                "api_key_set": bool(settings.search_api_key)
            },
            "llm": {
                "model": settings.llm_model,
                "temperature": settings.llm_temperature,
                "max_tokens": settings.max_tokens
            },
            "features": {
                "sms": settings.enable_sms,
                "caching": settings.enable_caching,
                "metrics": settings.enable_metrics
            }
        }


# ==================== Application Entry Point ====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.APP_HOST}:{settings.APP_PORT}")
    
    uvicorn.run(
        "backend.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL
    )
