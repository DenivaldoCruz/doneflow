"""Unit tests for LGPD privacy and security requirements (RNF-04)."""

from __future__ import annotations

import hashlib
import logging
import os
from typing import Any

import pytest

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from doneflow.api.routes.health import router as health_router
from doneflow.main import app
from doneflow.models.quadrant import Quadrant
from doneflow.services.ai_categorization_service import AICategorizationService
from doneflow.services.categorization_cache import CategorizationCache


def test_cache_uses_sha256_hash_and_never_stores_original_task_text() -> None:
    """RNF-04 requires cache keys to avoid storing raw task descriptions."""
    task_text = "Enviar documentos médicos confidenciais hoje"
    expected_key = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    cache = CategorizationCache(ttl_seconds=300, max_entries=1000)

    cache.set(task_text, {"quadrant": Quadrant.DO_NOW, "confidence": 0.94})

    assert cache.make_key(task_text) == expected_key
    assert cache.keys() == [expected_key]
    assert all(task_text not in key for key in cache.keys())


def test_error_logs_do_not_include_task_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Unhandled error logs must not leak task descriptions or request bodies."""
    sensitive_task_text = "Tarefa sigilosa LGPD com CPF 123.456.789-00"
    isolated_app = FastAPI()
    isolated_app.add_exception_handler(Exception, app.exception_handlers[Exception])

    router = APIRouter()

    @router.post("/tasks")
    async def boom(payload: dict[str, str]) -> None:
        del payload
        raise RuntimeError(sensitive_task_text)

    isolated_app.include_router(router)
    caplog.set_level(logging.ERROR, logger="doneflow.main")

    with TestClient(isolated_app, raise_server_exceptions=False) as client:
        response = client.post("/tasks", json={"description": sensitive_task_text})

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert sensitive_task_text not in caplog.text
    assert "description" not in caplog.text


def test_health_endpoint_does_not_expose_sensitive_internal_data() -> None:
    """Health payload should be safe for probes and omit secrets, URLs, and debug internals."""
    isolated_app = FastAPI()
    isolated_app.include_router(health_router)

    with TestClient(isolated_app) as client:
        response = client.get("/health")

    body = response.json()
    serialized_body = response.text.lower()

    assert response.status_code == 200
    assert set(body) == {"status", "version", "timestamp", "database"}
    assert "anthropic" not in serialized_body
    assert "api_key" not in serialized_body
    assert "database_url" not in serialized_body
    assert "sqlite" not in serialized_body
    assert "postgres" not in serialized_body
    assert "debug" not in serialized_body


def test_logging_middleware_does_not_log_post_tasks_body(
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request middleware must log metadata for POST /tasks without logging the JSON body."""
    sensitive_task_text = "Segredo RNF-04 urgente para cliente VIP"

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
        response = client.post("/api/v1/tasks", json={"description": sensitive_task_text})

    assert response.status_code == 201
    assert "POST" in caplog.text
    assert "/api/v1/tasks" in caplog.text
    assert sensitive_task_text not in caplog.text
    assert "description" not in caplog.text


def test_response_headers_include_content_type_and_frame_protection() -> None:
    """RNF-04 security headers should be present on API responses."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
