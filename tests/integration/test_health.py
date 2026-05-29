"""Integration tests for the DoneFlow health endpoint."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from time import perf_counter
from typing import Any

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient

from doneflow import __version__
from doneflow.api.main import app

pytestmark = pytest.mark.integration

EXPECTED_HEALTH_FIELDS = {"status", "version", "timestamp", "database"}
DATABASE_STATUSES = {"connected", "disconnected"}
MAX_HEALTH_RESPONSE_SECONDS = 0.1
MAX_TIMESTAMP_AGE_SECONDS = 5.0


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client for health endpoint checks."""
    return TestClient(app)


def _request_health(client: TestClient) -> tuple[float, Any]:
    """Call GET /health and return elapsed seconds with the response object.

    Args:
        client: FastAPI test client used to call the application.

    Returns:
        Tuple containing elapsed request time in seconds and the HTTP response.
    """
    started_at = perf_counter()
    response = client.get("/health")
    elapsed_seconds = perf_counter() - started_at

    return elapsed_seconds, response


def _assert_complete_health_contract(body: dict[str, Any]) -> None:
    """Assert that the health body exposes the full expected response contract.

    Args:
        body: JSON response body returned by GET /health.
    """
    assert set(body) == EXPECTED_HEALTH_FIELDS


def test_get_health_returns_200_with_complete_contract(client: TestClient) -> None:
    """GET /health returns HTTP 200 and the full health response contract."""
    _, response = _request_health(client)

    assert response.status_code == 200
    _assert_complete_health_contract(response.json())


def test_get_health_body_has_status_ok(client: TestClient) -> None:
    """GET /health body reports the application status as ok."""
    _, response = _request_health(client)
    body = response.json()

    assert body["status"] == "ok"
    _assert_complete_health_contract(body)


def test_get_health_body_has_application_version(client: TestClient) -> None:
    """GET /health body includes the current application version."""
    _, response = _request_health(client)
    body = response.json()

    assert body["version"] == __version__
    _assert_complete_health_contract(body)


def test_get_health_body_has_current_utc_timestamp(client: TestClient) -> None:
    """GET /health body includes a current UTC timestamp."""
    before_request = datetime.now(UTC)
    _, response = _request_health(client)
    after_request = datetime.now(UTC)
    body = response.json()

    timestamp = datetime.fromisoformat(body["timestamp"])

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset() == UTC.utcoffset(timestamp)
    assert before_request <= timestamp <= after_request
    assert (after_request - timestamp).total_seconds() <= MAX_TIMESTAMP_AGE_SECONDS
    _assert_complete_health_contract(body)


def test_get_health_body_has_database_status(client: TestClient) -> None:
    """GET /health body includes a database connection status."""
    _, response = _request_health(client)
    body = response.json()

    assert body["database"] in DATABASE_STATUSES
    _assert_complete_health_contract(body)


def test_get_health_response_time_is_under_100ms(client: TestClient) -> None:
    """GET /health responds in under 100 milliseconds."""
    elapsed_seconds, response = _request_health(client)

    assert elapsed_seconds < MAX_HEALTH_RESPONSE_SECONDS
    _assert_complete_health_contract(response.json())
