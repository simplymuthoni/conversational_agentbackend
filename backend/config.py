import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
GEMINI_API_KEY: str = Field(None)
LANGSMITH_API_KEY: str = Field(None)
LANGGRAPH_CLOUD_LICENSE_KEY: str = Field(None)


AT_USERNAME: str = Field(None)
AT_API_KEY: str = Field(None)


POSTGRES_HOST: str = Field("postgres")
POSTGRES_PORT: int = Field(5432)
POSTGRES_DB: str = Field("research")
POSTGRES_USER: str = Field("postgres")
POSTGRES_PASSWORD: str = Field("postgres")


REDIS_URL: str = Field("redis://redis:6379/0")


APP_ENV: str = Field("development")
APP_HOST: str = Field("0.0.0.0")
APP_PORT: int = Field(8000)


LOG_LEVEL: str = Field("info")


class Config:
env_file = ".env"


settings = Settings()