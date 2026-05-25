"""Unit tests for application settings."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from doneflow.config import Settings, get_settings


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


def test_get_settings_reads_environment_and_caches_result(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_settings should load required values from env and reuse cached object."""
    get_settings.cache_clear()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///env.db")

    first = get_settings()
    second = get_settings()

    assert first is second
    assert first.ANTHROPIC_API_KEY == "env-key"
    assert first.DATABASE_URL == "sqlite:///env.db"
