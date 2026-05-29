"""Task orchestration service for DoneFlow."""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from doneflow.models.quadrant import Quadrant
from doneflow.models.task import Task
from doneflow.schemas.task import DistributionResponse

if TYPE_CHECKING:
    from doneflow.repositories.task_repository import TaskRepository
    from doneflow.services.ai_categorization_service import AICategorizationService
    from doneflow.services.categorization_cache import CategorizationCache

T = TypeVar("T")
SessionFactory = Callable[[], Any]
LOGGER = logging.getLogger(__name__)


class TaskNotFoundError(LookupError):
    """Raised when a requested task resource does not exist."""

    def __init__(self, task_id: UUID | str) -> None:
        """Initialize the exception with the missing task identifier.

        Args:
            task_id: Identifier that could not be found.
        """
        self.task_id = task_id
        super().__init__(f"Task not found: {task_id}")


class TaskService:
    """Coordinate task classification, persistence, and retrieval.

    The service keeps business orchestration outside HTTP handlers and database
    repositories. Dependencies are constructor-injected so tests can provide
    mocks and production code can use the default repository, AI service, cache,
    and SQLAlchemy session factory.
    """

    def __init__(
        self,
        *,
        repository: TaskRepository | None = None,
        ai_service: AICategorizationService | None = None,
        cache: CategorizationCache | None = None,
        session_factory: SessionFactory | None = None,
    ) -> None:
        """Initialize service dependencies.

        Args:
            repository: Task persistence adapter. Defaults to ``TaskRepository``.
            ai_service: AI categorization adapter. Defaults to ``AICategorizationService``.
            cache: Categorization cache adapter. Defaults to ``CategorizationCache``.
            session_factory: Callable producing SQLAlchemy sessions. Defaults to
                the application ``session_local`` factory.
        """
        self._repository = repository if repository is not None else self._default_repository()
        self._ai_service = ai_service if ai_service is not None else self._default_ai_service()
        self._cache = cache if cache is not None else self._default_cache()
        self._session_factory = (
            session_factory if session_factory is not None else self._default_session_factory()
        )

    async def create_task(self, description: str) -> Task:
        """Create a task after resolving its AI categorization.

        The categorization flow checks the cache first, calls the AI service on a
        cache miss, writes the new classification back to cache, and persists the
        task through ``TaskRepository``.

        Args:
            description: User-provided task description.

        Returns:
            Persisted domain task.
        """
        classification = self._cache.get(description)
        if classification is None:
            classification = await self._ai_service.classify_task(description)
            self._cache.set(description, classification)

        quadrant = self._coerce_quadrant(classification["quadrant"])
        confidence = float(classification.get("confidence", 1.0))
        reasoning = classification.get("reasoning")
        return self._repository.create(
            session_factory=self._session_factory,
            description=description,
            quadrant=quadrant,
            created_at=datetime.now(UTC),
            ai_confidence=confidence,
            ai_reasoning=reasoning if isinstance(reasoning, str) else None,
        )

    async def create_and_categorize(self, description: str) -> Task:
        """Create and categorize a task using the canonical MVP flow.

        Args:
            description: User-provided task description.

        Returns:
            Persisted domain task.
        """
        return await self.create_task(description)

    def get_all_tasks(self) -> list[Task] | Coroutine[Any, Any, list[Task]]:
        """Return all persisted tasks.

        Returns:
            List of domain tasks. When called from an active event loop, returns
            a coroutine to be awaited; otherwise returns the list directly for
            compatibility with synchronous repository tests.
        """
        return self._run_or_return(self._get_all_tasks_async)

    def get_task_by_id(self, task_id: UUID | str) -> Task | Coroutine[Any, Any, Task]:
        """Return a task by id or raise ``TaskNotFoundError``.

        Args:
            task_id: Task identifier to fetch.

        Returns:
            Matching domain task.

        Raises:
            TaskNotFoundError: If no task exists for ``task_id``.
        """
        return self._run_or_return(lambda: self._get_task_by_id_async(task_id))

    def get_tasks_by_quadrant(
        self, quadrant: Quadrant
    ) -> list[Task] | Coroutine[Any, Any, list[Task]]:
        """Return all tasks assigned to a quadrant.

        Args:
            quadrant: Quadrant used to filter tasks.

        Returns:
            List of matching domain tasks.
        """
        return self._run_or_return(lambda: self._get_tasks_by_quadrant_async(quadrant))

    def update_quadrant(
        self, task_id: UUID | str, quadrant: Quadrant
    ) -> Task | Coroutine[Any, Any, Task]:
        """Persist a manual quadrant update for an existing task.

        Args:
            task_id: Task identifier to update.
            quadrant: New quadrant selected by the user.

        Returns:
            Updated domain task.

        Raises:
            TaskNotFoundError: If no task exists for ``task_id``.
        """
        return self._run_or_return(lambda: self._update_quadrant_async(task_id, quadrant))

    def delete_task(self, task_id: UUID | str) -> bool | Coroutine[Any, Any, bool]:
        """Delete a task by id.

        Args:
            task_id: Task identifier to delete.

        Returns:
            ``True`` when deletion succeeds.

        Raises:
            TaskNotFoundError: If no task exists for ``task_id``.
        """
        return self._run_or_return(lambda: self._delete_task_async(task_id))

    def get_distribution(self) -> DistributionResponse | Coroutine[Any, Any, DistributionResponse]:
        """Return task counts grouped by Eisenhower quadrant.

        Returns:
            Pydantic response model with quadrant counts and total.
        """
        return self._run_or_return(self._get_distribution_async)

    async def _get_all_tasks_async(self) -> list[Task]:
        """Asynchronously delegate task listing to the repository."""
        return self._repository.get_all(session_factory=self._session_factory)

    async def _get_task_by_id_async(self, task_id: UUID | str) -> Task:
        """Asynchronously fetch a task by id and normalize not-found handling."""
        task = self._repository.get_by_id(session_factory=self._session_factory, task_id=task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def _get_tasks_by_quadrant_async(self, quadrant: Quadrant) -> list[Task]:
        """Asynchronously delegate quadrant filtering to the repository."""
        return self._repository.get_by_quadrant(
            session_factory=self._session_factory,
            quadrant=quadrant,
        )

    async def _update_quadrant_async(self, task_id: UUID | str, quadrant: Quadrant) -> Task:
        """Asynchronously persist a manual quadrant update."""
        task = self._repository.update_quadrant(
            session_factory=self._session_factory,
            task_id=task_id,
            quadrant=quadrant,
        )
        if task is None:
            raise TaskNotFoundError(task_id)
        return task

    async def _delete_task_async(self, task_id: UUID | str) -> bool:
        """Asynchronously delete a task and normalize not-found handling."""
        deleted = self._repository.delete(session_factory=self._session_factory, task_id=task_id)
        if not deleted:
            raise TaskNotFoundError(task_id)
        return True

    async def _get_distribution_async(self) -> DistributionResponse:
        """Asynchronously return normalized task distribution counts."""
        counts = self._repository.get_distribution(session_factory=self._session_factory)
        return DistributionResponse.from_quadrant_counts(cast(dict[Quadrant | str, int], counts))

    def _run_or_return(
        self, async_factory: Callable[[], Coroutine[Any, Any, T]]
    ) -> T | Coroutine[Any, Any, T]:
        """Return a coroutine inside event loops and concrete values otherwise.

        Args:
            async_factory: Zero-argument factory that builds the coroutine.

        Returns:
            Coroutine when an event loop is already running, or the coroutine
            result when called from synchronous code.
        """
        try:
            _running_loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(async_factory())
        return async_factory()

    def _coerce_quadrant(self, value: Quadrant | str) -> Quadrant:
        """Normalize raw classification quadrant values.

        Args:
            value: Quadrant enum or string value returned by the AI/cache layer.

        Returns:
            ``Quadrant`` enum instance.
        """
        if isinstance(value, Quadrant):
            return value
        return Quadrant.from_string(value)

    def _default_repository(self) -> TaskRepository:
        """Build the default repository dependency lazily."""
        from doneflow.repositories.task_repository import TaskRepository

        return TaskRepository()

    def _default_ai_service(self) -> AICategorizationService:
        """Build the default AI service dependency lazily."""
        from doneflow.services.ai_categorization_service import AICategorizationService

        return AICategorizationService()

    def _default_cache(self) -> CategorizationCache:
        """Build the default cache dependency lazily."""
        from doneflow.config import get_settings
        from doneflow.services.categorization_cache import CategorizationCache

        ttl_seconds = int(os.getenv("AI_CACHE_TTL_SECONDS", "300"))
        try:
            ttl_seconds = get_settings().AI_CACHE_TTL_SECONDS
        except Exception as exc:  # noqa: BLE001
            LOGGER.debug("Using environment/default cache TTL: %s", type(exc).__name__)
        if ttl_seconds <= 0:
            ttl_seconds = 300
        return CategorizationCache(ttl_seconds=ttl_seconds, max_entries=1024)

    def _default_session_factory(self) -> SessionFactory:
        """Return the default SQLAlchemy session factory lazily."""
        from doneflow.database import session_local

        return session_local
