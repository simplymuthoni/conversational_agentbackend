"""
Configuration module for the Conversational Research Agent application.

This module manages all application settings and environment variables using Pydantic's
BaseSettings for type validation and automatic loading from .env files.

The settings are organized into logical groups:
- API credentials (Gemini, LangSmith, Africa's Talking, Search)
- Database configuration (PostgreSQL)
- Cache configuration (Redis)
- Application runtime settings
- Security and safety settings

All sensitive credentials are loaded from environment variables and must be provided
via a .env file or system environment variables.

Example:
    >>> from backend.config import settings
    >>> print(settings.GEMINI_API_KEY)
    'your-api-key-here'
    
    >>> print(settings.POSTGRES_HOST)
    'postgres'

Note:
    Required environment variables (marked with ...) must be set or the application
    will fail to start with a ValidationError.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import Optional
import logging


class Settings(BaseSettings):
    """
    Application settings and configuration.
    
    Manages all environment variables and application configuration using Pydantic
    for automatic validation, type conversion, and loading from .env files.
    
    Attributes:
        GEMINI_API_KEY (str): Google Gemini API key for LLM operations. Required.
        LANGSMITH_API_KEY (str): LangSmith API key for observability and tracing. Required.
        AT_USERNAME (str): Africa's Talking username for SMS services. Required.
        AT_API_KEY (str): Africa's Talking API key for SMS authentication. Required.
        POSTGRES_HOST (str): PostgreSQL database host. Defaults to 'postgres'.
        POSTGRES_PORT (int): PostgreSQL database port. Defaults to 5432.
        POSTGRES_DB (str): PostgreSQL database name. Defaults to 'research'.
        POSTGRES_USER (str): PostgreSQL username. Defaults to 'postgres'.
        POSTGRES_PASSWORD (str): PostgreSQL password. Required for security.
        REDIS_URL (str): Redis connection URL for caching and rate limiting.
            Defaults to 'redis://redis:6379/0'.
        APP_ENV (str): Application environment (development/staging/production).
            Defaults to 'development'.
        APP_HOST (str): Host address for the FastAPI application. Defaults to '0.0.0.0'.
        APP_PORT (int): Port number for the FastAPI application. Defaults to 8000.
        LOG_LEVEL (str): Logging level (debug/info/warning/error/critical).
            Defaults to 'info'.
    
    Configuration:
        Automatically loads variables from a .env file in the project root.
        Case-insensitive environment variable names are supported.
    
    Raises:
        ValidationError: If required fields are missing or values have incorrect types.
    
    Example:
        >>> settings = Settings()
        >>> print(f"Connecting to {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
        Connecting to postgres:5432
        
        >>> if settings.APP_ENV == "production":
        ...     print("Running in production mode")
    """
    
    # ==================== API Keys ====================
    # Required for external service integrations
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    LANGSMITH_API_KEY: str = Field(..., env="LANGSMITH_API_KEY")
    
    # Africa's Talking SMS Gateway
    AT_USERNAME: str = Field(..., env="AT_USERNAME")
    AT_API_KEY: str = Field(..., env="AT_API_KEY")
    africas_talking_webhook_secret: Optional[str] = Field(
        None,
        env="AT_WEBHOOK_SECRET",
        description="Secret for validating Africa's Talking webhooks"
    )
    
    # Search API (optional - defaults to mock if not provided)
    search_api_key: Optional[str] = Field(
        None,
        env="SEARCH_API_KEY",
        description="API key for search provider (SerpAPI, Brave, Google)"
    )
    search_engine_id: Optional[str] = Field(
        None,
        env="SEARCH_ENGINE_ID",
        description="Search Engine ID for Google Custom Search"
    )
    search_provider: str = Field(
        default="mock",
        env="SEARCH_PROVIDER",
        description="Search provider: mock, gemini, serpapi, brave, google"
    )
    
    # ==================== Database Configuration ====================
    POSTGRES_HOST: str = Field("postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field("research", env="POSTGRES_DB")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    
    @property
    def postgres_url(self) -> str:
        """
        Construct PostgreSQL connection URL.
        
        Returns:
            Full PostgreSQL connection string for async SQLAlchemy
        """
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ==================== Cache Configuration ====================
    REDIS_URL: str = Field("redis://redis:6379/0", env="REDIS_URL")
    
    # ==================== Application Runtime Settings ====================
    APP_ENV: str = Field("development", env="APP_ENV")
    APP_HOST: str = Field("0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(8000, env="APP_PORT")
    LOG_LEVEL: str = Field("info", env="LOG_LEVEL")
    
    # Application metadata
    APP_NAME: str = Field(
        "Research Agent API",
        env="APP_NAME"
    )
    APP_VERSION: str = Field(
        "1.0.0",
        env="APP_VERSION"
    )
    
    # ==================== LLM Configuration ====================
    llm_model: str = Field(
        default="gemini-2.5-flash",
        env="LLM_MODEL",
        description="Gemini model to use for generation"
    )
    llm_temperature: float = Field(
        default=0.7,
        env="LLM_TEMPERATURE",
        ge=0.0,
        le=1.0,
        description="LLM sampling temperature"
    )
    max_tokens: int = Field(
        default=2048,
        env="MAX_TOKENS",
        ge=100,
        le=8192,
        description="Maximum tokens in LLM response"
    )
    
    # ==================== Research Agent Settings ====================
    max_search_results: int = Field(
        default=10,
        env="MAX_SEARCH_RESULTS",
        ge=1,
        le=50,
        description="Maximum search results to retrieve per query"
    )
    max_reflection_iterations: int = Field(
        default=3,
        env="MAX_REFLECTION_ITERATIONS",
        ge=1,
        le=5,
        description="Maximum reflection/iteration loops"
    )
    
    # ==================== Security & Safety Settings ====================
    enable_pii_filter: bool = Field(
        default=True,
        env="ENABLE_PII_FILTER",
        description="Enable PII detection and filtering"
    )
    enable_toxicity_filter: bool = Field(
        default=True,
        env="ENABLE_TOXICITY_FILTER",
        description="Enable toxicity content filtering"
    )
    enable_hallucination_check: bool = Field(
        default=True,
        env="ENABLE_HALLUCINATION_CHECK",
        description="Enable hallucination detection"
    )
    enable_bias_detection: bool = Field(
        default=True,
        env="ENABLE_BIAS_DETECTION",
        description="Enable bias detection in outputs"
    )
    enable_prompt_injection_check: bool = Field(
        default=True,
        env="ENABLE_PROMPT_INJECTION_CHECK",
        description="Enable prompt injection detection"
    )
    
    # ==================== Rate Limiting ====================
    rate_limit_enabled: bool = Field(
        default=True,
        env="RATE_LIMIT_ENABLED",
        description="Enable rate limiting"
    )
    rate_limit_requests: int = Field(
        default=100,
        env="RATE_LIMIT_REQUESTS",
        description="Max requests per window"
    )
    rate_limit_window: int = Field(
        default=3600,
        env="RATE_LIMIT_WINDOW",
        description="Rate limit window in seconds"
    )
    
    # ==================== Feature Flags ====================
    enable_sms: bool = Field(
        default=True,
        env="ENABLE_SMS",
        description="Enable SMS integration"
    )
    enable_caching: bool = Field(
        default=True,
        env="ENABLE_CACHING",
        description="Enable response caching"
    )
    enable_metrics: bool = Field(
        default=True,
        env="ENABLE_METRICS",
        description="Enable metrics collection"
    )
    
    # ==================== Validators ====================
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
        v_lower = v.lower()
        if v_lower not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_lower
    
    @validator('APP_ENV')
    def validate_app_env(cls, v):
        """Validate app environment."""
        valid_envs = ['development', 'staging', 'production']
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"APP_ENV must be one of: {', '.join(valid_envs)}")
        return v_lower
    
    @validator('search_provider')
    def validate_search_provider(cls, v):
        """Validate search provider."""
        valid_providers = ['mock', 'serpapi', 'brave', 'google']
        v_lower = v.lower()
        if v_lower not in valid_providers:
            raise ValueError(f"search_provider must be one of: {', '.join(valid_providers)}")
        return v_lower
    
    # ==================== Helper Properties ====================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == 'development'
    
    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self.LOG_LEVEL == 'debug' or self.is_development
    
    def get_log_level_int(self) -> int:
        """
        Get logging level as integer.
        
        Returns:
            Logging level constant from logging module
        """
        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }
        return levels.get(self.LOG_LEVEL, logging.INFO)
    
    class Config:
        """Pydantic configuration for Settings class."""
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'


# Global settings instance - import this in other modules
settings = Settings()


# Configure logging based on settings
logging.basicConfig(
    level=settings.get_log_level_int(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Log configuration on startup
logger = logging.getLogger(__name__)
logger.info(f"Configuration loaded: {settings.APP_NAME} v{settings.APP_VERSION}")
logger.info(f"Environment: {settings.APP_ENV}")
logger.info(f"Log level: {settings.LOG_LEVEL}")
logger.info(f"Search provider: {settings.search_provider}")
logger.info(f"Safety filters enabled: PII={settings.enable_pii_filter}, "
           f"Toxicity={settings.enable_toxicity_filter}, "
           f"Hallucination={settings.enable_hallucination_check}")
