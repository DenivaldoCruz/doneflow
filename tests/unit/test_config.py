"""Unit tests for application settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from doneflow.config import Settings


def test_settings_loads_defaults_when_environment_is_empty() -> None:
    """Settings should use safe defaults for optional environment values."""
    settings = Settings(
        ANTHROPIC_API_KEY="test-key",
        DATABASE_URL="sqlite:///doneflow.db",
    )

    assert settings.APP_ENV == "development"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.AI_TIMEOUT_SECONDS == 2
    assert settings.AI_CACHE_TTL_SECONDS == 300


def test_settings_rejects_invalid_log_level() -> None:
    """Settings should validate log level against supported values."""
    with pytest.raises(ValidationError):
        Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="sqlite:///doneflow.db",
            LOG_LEVEL="TRACE",
        )


def test_settings_rejects_non_positive_timeout() -> None:
    """Settings should reject timeout values that are not positive."""
    with pytest.raises(ValidationError):
        Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="sqlite:///doneflow.db",
            AI_TIMEOUT_SECONDS=0,
        )


def test_settings_rejects_negative_cache_ttl() -> None:
    """Settings should reject negative cache TTL values."""
    with pytest.raises(ValidationError):
        Settings(
            ANTHROPIC_API_KEY="test-key",
            DATABASE_URL="sqlite:///doneflow.db",
            AI_CACHE_TTL_SECONDS=-1,
        )
