"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import inspect
from collections.abc import Generator
from typing import Any

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


def pytest_configure(config: pytest.Config) -> None:
    """Register project markers used by the test suite."""
    config.addinivalue_line("markers", "asyncio: run async test functions with asyncio")


def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Run ``@pytest.mark.asyncio`` coroutine tests without requiring an external plugin."""
    if pyfuncitem.get_closest_marker("asyncio") is None:
        return None

    test_function = pyfuncitem.obj
    if not inspect.iscoroutinefunction(test_function):
        return None

    import asyncio

    fixture_names = pyfuncitem._fixtureinfo.argnames
    test_args: dict[str, Any] = {
        fixture_name: pyfuncitem.funcargs[fixture_name] for fixture_name in fixture_names
    }
    asyncio.run(test_function(**test_args))
    return True
