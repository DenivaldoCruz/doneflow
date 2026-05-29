"""Integration tests for task API endpoints."""

from __future__ import annotations

import os
from collections.abc import Generator
from importlib import import_module
from typing import Any

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from doneflow.database import Base, get_db
from doneflow.models.quadrant import Quadrant
from doneflow.schemas.task import TaskResponse
from doneflow.services.ai_categorization_service import AICategorizationService

API_PREFIX = "/api/v1"
TASK_RESPONSE_FIELDS = set(TaskResponse.model_fields)
pytestmark = pytest.mark.integration


@pytest.fixture
def sqlite_session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Create an isolated in-memory SQLite session factory for API tests."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        class_=Session,
    )

    yield test_session_factory

    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def mock_ai_categorization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock AI categorization so integration tests never call Anthropic."""

    async def fake_classify_task(
        self: AICategorizationService,
        task_description: str,
    ) -> dict[str, Any]:
        """Return deterministic quadrants based on the submitted description."""
        del self
        classifications = {
            "Preparar reunião urgente com CEO hoje": Quadrant.DO_NOW,
            "Planejar roadmap do produto": Quadrant.SCHEDULE,
            "Responder cliente sobre entrega": Quadrant.DELEGATE,
            "Arquivar newsletters antigas": Quadrant.ELIMINATE,
        }
        return {
            "quadrant": classifications.get(task_description, Quadrant.DO_NOW),
            "confidence": 0.94,
            "reasoning": "Mocked classification for integration tests.",
        }

    monkeypatch.setattr(AICategorizationService, "classify_task", fake_classify_task)


@pytest.fixture
def client(
    sqlite_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    mock_ai_categorization: None,
) -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient wired to the in-memory SQLite database."""
    del mock_ai_categorization

    def override_get_db() -> Generator[Session, None, None]:
        """Yield a database session from the test session factory."""
        session = sqlite_session_factory()
        try:
            yield session
        finally:
            session.close()

    import doneflow.database as database

    monkeypatch.setattr(database, "SessionFactory", sqlite_session_factory)
    app_module = import_module("doneflow.api.main")
    app = app_module.app
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_post_task_returns_201_with_quadrant(client: TestClient) -> None:
    """POST /tasks creates a categorized task and returns HTTP 201."""
    response = client.post(
        f"{API_PREFIX}/tasks",
        json={"description": "Preparar reunião urgente com CEO hoje"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["description"] == "Preparar reunião urgente com CEO hoje"
    assert body["quadrant"] == Quadrant.DO_NOW.value
    assert body["ai_confidence"] == 0.94


def test_post_empty_task_returns_422(client: TestClient) -> None:
    """POST /tasks rejects empty task descriptions with HTTP 422."""
    response = client.post(f"{API_PREFIX}/tasks", json={"description": ""})

    assert response.status_code == 422


def test_get_tasks_returns_correct_distribution(client: TestClient) -> None:
    """GET /tasks/distribution returns counts for every quadrant."""
    descriptions = [
        "Preparar reunião urgente com CEO hoje",
        "Planejar roadmap do produto",
        "Responder cliente sobre entrega",
        "Arquivar newsletters antigas",
    ]
    for description in descriptions:
        response = client.post(f"{API_PREFIX}/tasks", json={"description": description})
        assert response.status_code == 201

    response = client.get(f"{API_PREFIX}/tasks/distribution")

    assert response.status_code == 200
    assert response.json() == {
        "DO_NOW": 1,
        "SCHEDULE": 1,
        "DELEGATE": 1,
        "ELIMINATE": 1,
        "total": 4,
    }


def test_post_task_with_text_shorter_than_five_chars_returns_422(client: TestClient) -> None:
    """POST /tasks rejects descriptions shorter than five characters."""
    response = client.post(f"{API_PREFIX}/tasks", json={"description": "abcd"})

    assert response.status_code == 422


def test_post_task_with_text_longer_than_500_chars_returns_422(client: TestClient) -> None:
    """POST /tasks rejects descriptions longer than 500 characters."""
    response = client.post(f"{API_PREFIX}/tasks", json={"description": "x" * 501})

    assert response.status_code == 422


def test_get_tasks_returns_empty_list_initially(client: TestClient) -> None:
    """GET /tasks returns an empty list before any task is created."""
    response = client.get(f"{API_PREFIX}/tasks")

    assert response.status_code == 200
    assert response.json() == []


def test_get_tasks_returns_created_task(client: TestClient) -> None:
    """GET /tasks includes a task created through POST /tasks."""
    created_response = client.post(
        f"{API_PREFIX}/tasks",
        json={"description": "Preparar reunião urgente com CEO hoje"},
    )
    assert created_response.status_code == 201
    created_task = created_response.json()

    response = client.get(f"{API_PREFIX}/tasks")

    assert response.status_code == 200
    assert response.json() == [created_task]


def test_task_response_body_has_all_task_response_schema_fields(client: TestClient) -> None:
    """POST /tasks returns every field defined by TaskResponse."""
    response = client.post(
        f"{API_PREFIX}/tasks",
        json={"description": "Preparar reunião urgente com CEO hoje"},
    )

    assert response.status_code == 201
    assert set(response.json()) == TASK_RESPONSE_FIELDS
