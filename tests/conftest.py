"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine


@pytest.fixture
def sample_fixture() -> dict[str, str]:
    """Example fixture for tests."""
    return {"example": "fixture"}


@pytest.fixture
def sqlite_engine() -> Generator[Engine, None, None]:
    """Yield an in-memory SQLite engine and dispose pooled connections afterwards."""
    engine = create_engine("sqlite:///:memory:")
    try:
        yield engine
    finally:
        engine.dispose()
