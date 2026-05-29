"""Task API routes for the DoneFlow v1 REST interface."""

from __future__ import annotations

from collections.abc import Awaitable, Generator
from contextlib import contextmanager
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from doneflow.database import get_db
from doneflow.models.task import Task
from doneflow.schemas.task import DistributionResponse, TaskCreate, TaskResponse, TaskUpdate
from doneflow.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(tags=["tasks"])


@contextmanager
def _session_dependency_factory(session: Session) -> Generator[Session, None, None]:
    """Adapt a FastAPI-managed SQLAlchemy session to the repository contract.

    Args:
        session: Session yielded by the ``get_db`` dependency.

    Yields:
        The same SQLAlchemy session without taking over its lifecycle.
    """
    yield session


def get_task_service(session: Session = Depends(get_db)) -> TaskService:
    """Build the task service with the request-scoped database dependency.

    Args:
        session: SQLAlchemy session injected by FastAPI.

    Returns:
        Task service configured for the current request.
    """
    return TaskService(session_factory=lambda: _session_dependency_factory(session))


async def _await_service_result[T](result: T | Awaitable[T]) -> T:
    """Await a service result when it is coroutine-backed by an active event loop.

    Args:
        result: Concrete service result or awaitable service result.

    Returns:
        Resolved service result.
    """
    return await cast(Awaitable[T], result)


def _not_found_error(exc: TaskNotFoundError) -> HTTPException:
    """Convert a task-domain lookup error into a FastAPI 404 exception.

    Args:
        exc: Domain exception containing the missing task identifier.

    Returns:
        HTTP 404 exception suitable for API handlers.
    """
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreate,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a task and classify it into an Eisenhower Matrix quadrant."""
    return await service.create_and_categorize(payload.description)


@router.get("/tasks", response_model=list[TaskResponse])
async def list_tasks(service: TaskService = Depends(get_task_service)) -> list[Task]:
    """List all persisted tasks in insertion order."""
    return await _await_service_result(service.get_all_tasks())


@router.get("/tasks/distribution", response_model=DistributionResponse)
async def get_tasks_distribution(
    service: TaskService = Depends(get_task_service),
) -> DistributionResponse:
    """Return task counts for every Eisenhower Matrix quadrant."""
    return await _await_service_result(service.get_distribution())


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Fetch a single task by its UUID identifier."""
    try:
        return await _await_service_result(service.get_task_by_id(task_id))
    except TaskNotFoundError as exc:
        raise _not_found_error(exc) from exc


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task_quadrant(
    task_id: UUID,
    payload: TaskUpdate,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Manually reclassify an existing task into another quadrant."""
    if payload.quadrant is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="quadrant is required for manual reclassification",
        )

    try:
        return await _await_service_result(service.update_quadrant(task_id, payload.quadrant))
    except TaskNotFoundError as exc:
        raise _not_found_error(exc) from exc


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> Response:
    """Delete a task from the board by its UUID identifier."""
    try:
        await _await_service_result(service.delete_task(task_id))
    except TaskNotFoundError as exc:
        raise _not_found_error(exc) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
