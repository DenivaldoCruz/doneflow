"""Unit tests for TaskService orchestration (TDD RED phase)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from importlib import import_module
from types import ModuleType
from typing import Any
from unittest.mock import ANY, AsyncMock, MagicMock
from uuid import UUID

import pytest

from doneflow.models.quadrant import Quadrant
from doneflow.models.task import Task
from doneflow.schemas.task import DistributionResponse


@pytest.fixture
def task_service_module() -> ModuleType:
    """Import the TaskService module expected to be implemented next."""
    return import_module("doneflow.services.task_service")


@pytest.fixture
def session_factory() -> MagicMock:
    """Return a mocked SQLAlchemy session factory dependency."""
    return MagicMock(name="session_factory")


@pytest.fixture
def repository() -> MagicMock:
    """Return a mocked TaskRepository dependency."""
    return MagicMock(name="TaskRepository")


@pytest.fixture
def ai_service() -> MagicMock:
    """Return a mocked AICategorizationService dependency."""
    service = MagicMock(name="AICategorizationService")
    service.classify_task = AsyncMock(name="classify_task")
    return service


@pytest.fixture
def cache() -> MagicMock:
    """Return a mocked categorization cache dependency."""
    return MagicMock(name="CategorizationCache")


def make_task(
    *,
    description: str = "Finalizar relatório financeiro urgente",
    quadrant: Quadrant = Quadrant.DO_NOW,
    ai_confidence: float = 0.94,
) -> Task:
    """Build a valid domain task for service tests."""
    return Task(
        id=UUID("11111111-1111-1111-1111-111111111111"),
        description=description,
        quadrant=quadrant,
        ai_confidence=ai_confidence,
        ai_reasoning="Prazo imediato com impacto estratégico.",
        created_at=datetime(2026, 5, 28, 12, 0, tzinfo=UTC),
        updated_at=datetime(2026, 5, 28, 12, 0, tzinfo=UTC),
    )


def build_service(
    task_service_module: ModuleType,
    *,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> Any:
    """Instantiate TaskService with explicit mocked dependencies."""
    return task_service_module.TaskService(
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )


def test_create_task_with_cache_miss_calls_ai_and_persists_task(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """create_task should classify through AI on cache miss and persist the result."""
    description = "Finalizar relatório financeiro urgente"
    classification = {
        "quadrant": Quadrant.DO_NOW,
        "confidence": 0.94,
        "reasoning": "Prazo imediato com impacto estratégico.",
    }
    expected_task = make_task(description=description)
    cache.get.return_value = None
    ai_service.classify_task.return_value = classification
    repository.create.return_value = expected_task
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    created = asyncio.run(service.create_task(description))

    assert created == expected_task
    cache.get.assert_called_once_with(description)
    ai_service.classify_task.assert_awaited_once_with(description)
    cache.set.assert_called_once_with(description, classification)
    repository.create.assert_called_once_with(
        session_factory=session_factory,
        description=description,
        quadrant=Quadrant.DO_NOW,
        created_at=ANY,
        ai_confidence=0.94,
        ai_reasoning="Prazo imediato com impacto estratégico.",
    )


def test_create_task_with_cached_classification_uses_cache_and_does_not_call_ai(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """create_task should reuse cached categorization instead of calling AI again."""
    description = "Planejar roadmap do próximo trimestre"
    cached_classification = {"quadrant": Quadrant.SCHEDULE, "confidence": 0.88}
    expected_task = make_task(
        description=description,
        quadrant=Quadrant.SCHEDULE,
        ai_confidence=0.88,
    )
    cache.get.return_value = cached_classification
    repository.create.return_value = expected_task
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    created = asyncio.run(service.create_task(description))

    assert created == expected_task
    cache.get.assert_called_once_with(description)
    ai_service.classify_task.assert_not_called()
    cache.set.assert_not_called()
    repository.create.assert_called_once_with(
        session_factory=session_factory,
        description=description,
        quadrant=Quadrant.SCHEDULE,
        created_at=ANY,
        ai_confidence=0.88,
        ai_reasoning=None,
    )


def test_get_all_tasks_delegates_to_repository(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """get_all_tasks should return exactly what TaskRepository.get_all returns."""
    expected_tasks = [make_task(), make_task(description="Delegar revisão operacional")]
    repository.get_all.return_value = expected_tasks
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    tasks = service.get_all_tasks()

    assert tasks == expected_tasks
    repository.get_all.assert_called_once_with(session_factory=session_factory)


def test_get_task_by_id_with_missing_task_raises_task_not_found_error(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """get_task_by_id should raise TaskNotFoundError when repository returns None."""
    task_id = UUID("22222222-2222-2222-2222-222222222222")
    repository.get_by_id.return_value = None
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    with pytest.raises(task_service_module.TaskNotFoundError):
        service.get_task_by_id(task_id)

    repository.get_by_id.assert_called_once_with(
        session_factory=session_factory,
        task_id=task_id,
    )


def test_update_quadrant_persists_new_category(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """update_quadrant should persist and return the newly selected quadrant."""
    task_id = UUID("33333333-3333-3333-3333-333333333333")
    expected_task = make_task(quadrant=Quadrant.DELEGATE)
    repository.update_quadrant.return_value = expected_task
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    updated = service.update_quadrant(task_id, Quadrant.DELEGATE)

    assert updated == expected_task
    repository.update_quadrant.assert_called_once_with(
        session_factory=session_factory,
        task_id=task_id,
        quadrant=Quadrant.DELEGATE,
    )


def test_delete_task_with_missing_task_raises_task_not_found_error(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """delete_task should raise TaskNotFoundError when repository cannot delete the id."""
    task_id = UUID("44444444-4444-4444-4444-444444444444")
    repository.delete.return_value = False
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    with pytest.raises(task_service_module.TaskNotFoundError):
        service.delete_task(task_id)

    repository.delete.assert_called_once_with(session_factory=session_factory, task_id=task_id)


def test_get_distribution_returns_distribution_response(
    task_service_module: ModuleType,
    repository: MagicMock,
    ai_service: MagicMock,
    cache: MagicMock,
    session_factory: MagicMock,
) -> None:
    """get_distribution should convert repository counts into a DistributionResponse."""
    repository.get_distribution.return_value = {
        Quadrant.DO_NOW: 2,
        Quadrant.SCHEDULE: 3,
        Quadrant.DELEGATE: 1,
        Quadrant.ELIMINATE: 4,
    }
    service = build_service(
        task_service_module,
        repository=repository,
        ai_service=ai_service,
        cache=cache,
        session_factory=session_factory,
    )

    distribution = service.get_distribution()

    assert distribution == DistributionResponse(
        DO_NOW=2,
        SCHEDULE=3,
        DELEGATE=1,
        ELIMINATE=4,
        total=10,
    )
    repository.get_distribution.assert_called_once_with(session_factory=session_factory)
