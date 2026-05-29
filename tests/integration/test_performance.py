"""Performance integration tests for DoneFlow non-functional requirements."""

# ruff: noqa: I001

from __future__ import annotations

import asyncio
import os
from collections.abc import Generator
from datetime import UTC
from datetime import datetime
from importlib import import_module
from math import ceil
from pathlib import Path
from time import perf_counter
from typing import Any

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import httpx
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from doneflow.database import Base
from doneflow.database import TaskORM
from doneflow.database import get_db
from doneflow.models.quadrant import Quadrant
from doneflow.services.ai_categorization_service import AICategorizationService

API_PREFIX = "/api/v1"
pytestmark = pytest.mark.integration


@pytest.fixture
def sqlite_session_factory(
    tmp_path: Path,
) -> Generator[sessionmaker[Session], None, None]:
    """Create an isolated SQLite session factory for performance tests."""
    database_path = tmp_path / "performance.db"
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}",
        connect_args={"check_same_thread": False},
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
def mock_fast_ai_categorization(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock AI categorization with deterministic, low-latency responses."""

    async def fake_classify_task(
        self: AICategorizationService,
        task_description: str,
    ) -> dict[str, Any]:
        """Return a deterministic classification without external API calls."""
        del self
        await asyncio.sleep(0.01)
        return {
            "quadrant": (
                Quadrant.DO_NOW if "urgente" in task_description.lower() else Quadrant.SCHEDULE
            ),
            "confidence": 0.97,
            "reasoning": "Mocked performance-test classification.",
        }

    monkeypatch.setattr(AICategorizationService, "classify_task", fake_classify_task)


@pytest.fixture
def seeded_tasks(sqlite_session_factory: sessionmaker[Session]) -> None:
    """Seed exactly 100 tasks directly in the test database."""
    quadrants = list(Quadrant)
    with sqlite_session_factory() as session:
        session.add_all(
            TaskORM(
                text=f"Performance seed task {index}",
                quadrant=quadrants[index % len(quadrants)].value,
                created_at=datetime.now(UTC),
                ai_confidence=0.95,
                ai_reasoning="Seeded task for distribution performance validation.",
            )
            for index in range(100)
        )
        session.commit()


@pytest.fixture
def async_client(
    sqlite_session_factory: sessionmaker[Session],
    monkeypatch: pytest.MonkeyPatch,
    mock_fast_ai_categorization: None,
) -> Generator[httpx.AsyncClient, None, None]:
    """Create an AsyncClient wired to the isolated SQLite database."""
    del mock_fast_ai_categorization

    def override_get_db() -> Generator[Session, None, None]:
        """Yield a database session from the performance test session factory."""
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
    transport = httpx.ASGITransport(app=app)

    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    try:
        yield client
    finally:
        asyncio.run(client.aclose())
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_post_tasks_with_10_simultaneous_requests_completes_under_5_seconds(
    async_client: httpx.AsyncClient,
) -> None:
    """Validate RNF-06 throughput using 10 simultaneous task creation requests."""

    async def create_task(index: int) -> tuple[httpx.Response, float]:
        """POST one task using the shared async test client and capture latency."""
        request_started_at = perf_counter()
        response = await async_client.post(
            f"{API_PREFIX}/tasks",
            json={"description": f"Resolver demanda urgente {index} hoje"},
        )
        return response, perf_counter() - request_started_at

    started_at = perf_counter()
    results = await asyncio.gather(*(create_task(index) for index in range(10)))
    total_duration = perf_counter() - started_at
    responses = [response for response, _duration in results]
    durations = sorted(duration for _response, duration in results)
    p95_duration = durations[ceil(len(durations) * 0.95) - 1]

    assert total_duration < 5.0
    assert p95_duration < 2.0
    assert [response.status_code for response in responses] == [201] * 10


@pytest.mark.asyncio
async def test_get_tasks_average_latency_stays_under_200ms(
    async_client: httpx.AsyncClient,
    seeded_tasks: None,
) -> None:
    """Validate list-task read latency remains below the RNF-01 read budget."""
    del seeded_tasks

    durations_ms: list[float] = []
    for _ in range(10):
        started_at = perf_counter()
        response = await async_client.get(f"{API_PREFIX}/tasks")
        durations_ms.append((perf_counter() - started_at) * 1000)

        assert response.status_code == 200
        assert len(response.json()) == 100

    average_latency_ms = sum(durations_ms) / len(durations_ms)
    assert average_latency_ms < 200


@pytest.mark.asyncio
async def test_health_responds_under_100ms_while_posts_are_in_flight(
    async_client: httpx.AsyncClient,
) -> None:
    """Validate health checks remain fast while write load is in flight."""
    post_tasks = [
        asyncio.create_task(
            async_client.post(
                f"{API_PREFIX}/tasks",
                json={"description": f"Tarefa urgente concorrente {index}"},
            )
        )
        for index in range(10)
    ]

    await asyncio.sleep(0)
    started_at = perf_counter()
    response = await async_client.get("/health")
    health_latency_ms = (perf_counter() - started_at) * 1000
    post_responses = await asyncio.gather(*post_tasks)

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert health_latency_ms < 100
    assert [post_response.status_code for post_response in post_responses] == [201] * 10


@pytest.mark.asyncio
async def test_distribution_with_100_tasks_responds_under_500ms(
    async_client: httpx.AsyncClient,
    seeded_tasks: None,
) -> None:
    """Validate quadrant distribution latency with 100 persisted tasks."""
    del seeded_tasks

    started_at = perf_counter()
    response = await async_client.get(f"{API_PREFIX}/tasks/distribution")
    duration_ms = (perf_counter() - started_at) * 1000

    assert response.status_code == 200
    assert response.json() == {
        "DO_NOW": 25,
        "SCHEDULE": 25,
        "DELEGATE": 25,
        "ELIMINATE": 25,
        "total": 100,
    }
    assert duration_ms < 500
