"""End-to-end tests for the DoneFlow primary user flow."""

from __future__ import annotations

import os
from collections.abc import Generator
from importlib import import_module
from typing import Any, cast

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from doneflow.database import Base, get_db
from doneflow.models.quadrant import Quadrant
from doneflow.services.ai_categorization_service import AICategorizationService

API_PREFIX = "/api/v1"
pytestmark = pytest.mark.e2e

TASK_CASES: tuple[tuple[str, Quadrant], ...] = (
    ("Resolver incidente urgente de produção hoje", Quadrant.DO_NOW),
    ("Planejar estratégia trimestral do produto", Quadrant.SCHEDULE),
    ("Delegar atualização do relatório para a equipe", Quadrant.DELEGATE),
    ("Ler newsletters antigas quando sobrar tempo", Quadrant.ELIMINATE),
)


@pytest.fixture
def sqlite_session_factory() -> Generator[sessionmaker[Session], None, None]:
    """Create an isolated in-memory SQLite session factory for E2E tests."""
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
    """Mock AI categorization so E2E tests are deterministic and offline."""

    async def fake_classify_task(
        self: AICategorizationService,
        task_description: str,
    ) -> dict[str, Any]:
        """Return the quadrant expected for each task in the full-flow scenario."""
        del self
        classifications = dict(TASK_CASES)
        return {
            "quadrant": classifications[task_description],
            "confidence": 0.98,
            "reasoning": "Mocked E2E classification for the DoneFlow primary user flow.",
        }

    monkeypatch.setattr(AICategorizationService, "classify_task", fake_classify_task)


@pytest.fixture
def e2e_app(
    sqlite_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    mock_ai_categorization: None,
) -> Generator[FastAPI, None, None]:
    """Create a FastAPI app wired to the test database and mocked AI service."""
    del mock_ai_categorization

    def override_get_db() -> Generator[Session, None, None]:
        """Yield a request-scoped SQLAlchemy session from the test factory."""
        session = sqlite_session_factory()
        try:
            yield session
        finally:
            session.close()

    import doneflow.database as database

    monkeypatch.setattr(database, "SessionFactory", sqlite_session_factory)
    app_module = import_module("doneflow.api.main")
    app = cast(FastAPI, app_module.app)
    app.dependency_overrides[get_db] = override_get_db
    yield app

    app.dependency_overrides.clear()


async def _create_task(
    client: httpx.AsyncClient,
    description: str,
    expected_quadrant: Quadrant,
) -> dict[str, Any]:
    """Create a task through the API and assert its automatic classification."""
    response = await client.post(f"{API_PREFIX}/tasks", json={"description": description})

    assert response.status_code == 201
    body = cast(dict[str, Any], response.json())
    assert body["description"] == description
    assert body["quadrant"] == expected_quadrant.value
    assert body["ai_confidence"] == 0.98
    return body


@pytest.mark.asyncio
async def test_primary_user_flow_classifies_distributes_deletes_and_reclassifies(
    e2e_app: FastAPI,
) -> None:
    """Exercise the PRD 7.2 flow through the DoneFlow HTTP API."""
    transport = httpx.ASGITransport(app=e2e_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        initial_board_response = await async_client.get(f"{API_PREFIX}/tasks")
        assert initial_board_response.status_code == 200
        assert initial_board_response.json() == []

        created_tasks = [
            await _create_task(async_client, description, expected_quadrant)
            for description, expected_quadrant in TASK_CASES
        ]

        distribution_response = await async_client.get(f"{API_PREFIX}/tasks/distribution")
        assert distribution_response.status_code == 200
        assert distribution_response.json() == {
            "DO_NOW": 1,
            "SCHEDULE": 1,
            "DELEGATE": 1,
            "ELIMINATE": 1,
            "total": 4,
        }

        board_response = await async_client.get(f"{API_PREFIX}/tasks")
        assert board_response.status_code == 200
        assert board_response.json() == created_tasks

        task_to_delete = created_tasks[2]
        delete_response = await async_client.delete(f"{API_PREFIX}/tasks/{task_to_delete['id']}")
        assert delete_response.status_code == 204

        board_after_delete_response = await async_client.get(f"{API_PREFIX}/tasks")
        assert board_after_delete_response.status_code == 200
        board_after_delete = board_after_delete_response.json()
        assert task_to_delete["id"] not in {task["id"] for task in board_after_delete}
        assert len(board_after_delete) == 3

        task_to_reclassify = created_tasks[1]
        reclassify_response = await async_client.patch(
            f"{API_PREFIX}/tasks/{task_to_reclassify['id']}",
            json={"quadrant": Quadrant.DO_NOW.value},
        )
        assert reclassify_response.status_code == 200
        reclassified_task = reclassify_response.json()
        assert reclassified_task["id"] == task_to_reclassify["id"]
        assert reclassified_task["description"] == task_to_reclassify["description"]
        assert reclassified_task["quadrant"] == Quadrant.DO_NOW.value

        final_board_response = await async_client.get(f"{API_PREFIX}/tasks")
        assert final_board_response.status_code == 200
        final_tasks_by_id = {task["id"]: task for task in final_board_response.json()}
        assert task_to_delete["id"] not in final_tasks_by_id
        assert final_tasks_by_id[task_to_reclassify["id"]]["quadrant"] == Quadrant.DO_NOW.value
