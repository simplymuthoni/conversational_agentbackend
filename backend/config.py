"""
Configuration module for the Conversational Research Agent application.

This module manages all application settings and environment variables using Pydantic's
BaseSettings for type validation and automatic loading from .env files.

The settings are organized into logical groups:
- API credentials (Gemini, LangSmith, Africa's Talking)
- Database configuration (PostgreSQL)
- Cache configuration (Redis)
- Application runtime settings

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

from pydantic import BaseSettings, Field


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
    # API Keys - Required for external service integrations
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    LANGSMITH_API_KEY: str = Field(..., env="LANGSMITH_API_KEY")
    AT_USERNAME: str = Field(..., env="AT_USERNAME")
    AT_API_KEY: str = Field(..., env="AT_API_KEY")
    # Database Configuration
    POSTGRES_HOST: str = Field("postgres", env="POSTGRES_HOST")
    POSTGRES_PORT: int = Field(5432, env="POSTGRES_PORT")
    POSTGRES_DB: str = Field("research", env="POSTGRES_DB")
    POSTGRES_USER: str = Field("postgres", env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    # Cache Configuration
    REDIS_URL: str = Field("redis://redis:6379/0", env="REDIS_URL")  
    # Application Runtime Settings
    APP_ENV: str = Field("development", env="APP_ENV")
    APP_HOST: str = Field("0.0.0.0", env="APP_HOST")
    APP_PORT: int = Field(8000, env="APP_PORT")
    LOG_LEVEL: str = Field("info", env="LOG_LEVEL")

    class Config:
        """Pydantic configuration for Settings class."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance - import this in other modules
settings = Settings()
