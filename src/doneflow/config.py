"""Application configuration for DoneFlow."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables.

    Attributes:
        ANTHROPIC_API_KEY: API key used to call Anthropic Claude.
        DATABASE_URL: SQLAlchemy-compatible database connection string.
        APP_ENV: Application runtime environment.
        LOG_LEVEL: Logging level used by the application.
        AI_TIMEOUT_SECONDS: Maximum wait for AI classification requests.
        AI_CACHE_TTL_SECONDS: Time-to-live for cached AI responses.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ANTHROPIC_API_KEY: str = Field(min_length=1)
    DATABASE_URL: str = Field(min_length=1)
    APP_ENV: Literal["development", "staging", "production", "test"] = "development"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    AI_TIMEOUT_SECONDS: float = Field(default=2.0, gt=0)
    AI_CACHE_TTL_SECONDS: int = Field(default=300, ge=0)


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance for dependency injection."""
    return Settings()
