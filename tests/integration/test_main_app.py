"""Integration tests for the DoneFlow FastAPI application shell."""

from __future__ import annotations

import logging
import os
from typing import Any

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi import APIRouter, FastAPI, Request
from fastapi.testclient import TestClient

from doneflow.main import app
from doneflow.models.quadrant import Quadrant
from doneflow.services.ai_categorization_service import AICategorizationService

pytestmark = pytest.mark.integration


def test_main_app_exposes_doneflow_openapi_metadata() -> None:
    """The principal app exposes DoneFlow product metadata in OpenAPI."""
    schema = app.openapi()

    assert schema["info"]["title"] == "DoneFlow API"
    assert schema["info"]["version"] == "0.4.0"
    assert "Eisenhower" in schema["info"]["description"]


def test_tasks_router_is_included_under_api_v1_prefix() -> None:
    """Task routes are mounted under /api/v1 and not at the application root."""
    with TestClient(app) as client:
        prefixed_response = client.get("/api/v1/tasks")
        unprefixed_response = client.get("/tasks")

    assert prefixed_response.status_code == 200
    assert unprefixed_response.status_code == 404


def test_cors_middleware_allows_configured_origins() -> None:
    """CORS middleware responds to browser preflight requests."""
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/tasks",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_request_logging_middleware_does_not_log_task_body(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request logging records request metadata without task descriptions for LGPD safety."""

    async def fake_classify_task(
        self: AICategorizationService,
        task_description: str,
    ) -> dict[str, Any]:
        del self
        del task_description
        return {
            "quadrant": Quadrant.DO_NOW,
            "confidence": 0.95,
            "reasoning": "Mocked classification.",
        }

    monkeypatch.setattr(AICategorizationService, "classify_task", fake_classify_task)
    caplog.set_level(logging.INFO, logger="doneflow.main")

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/tasks",
            json={"description": "Segredo LGPD urgente hoje"},
        )

    assert response.status_code == 201
    log_messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "POST" in log_messages
    assert "/api/v1/tasks" in log_messages
    assert "Segredo LGPD urgente hoje" not in log_messages
    assert "description" not in log_messages


def test_global_exception_handler_returns_sanitized_500_response() -> None:
    """Unhandled exceptions are converted into sanitized JSON responses."""
    isolated_app = FastAPI()
    isolated_app.add_exception_handler(Exception, app.exception_handlers[Exception])

    router = APIRouter()

    @router.get("/boom")
    async def boom(_: Request) -> None:
        raise RuntimeError("sensitive database internals")

    isolated_app.include_router(router)

    with TestClient(isolated_app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_lifespan_creates_database_tables(monkeypatch: pytest.MonkeyPatch) -> None:
    """Application startup creates database tables through the lifespan hook."""
    calls: list[str] = []

    def fake_create_all(*, bind: object) -> None:
        del bind
        calls.append("create_all")

    monkeypatch.setattr("doneflow.main.Base.metadata.create_all", fake_create_all)

    with TestClient(app):
        pass

    assert calls == ["create_all"]
