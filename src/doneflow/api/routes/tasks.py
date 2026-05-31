"""Task API routes for the DoneFlow v1 REST interface."""

from __future__ import annotations

from collections.abc import Awaitable, Generator
from contextlib import contextmanager
from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from doneflow.database import get_db
from doneflow.models.task import Task
from doneflow.schemas.task import (
    DISTRIBUTION_RESPONSE_EXAMPLE,
    TASK_CREATE_EXAMPLE,
    TASK_RESPONSE_EXAMPLE,
    TASK_UPDATE_EXAMPLE,
    DistributionResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from doneflow.services.task_service import TaskNotFoundError, TaskService

ERROR_EXAMPLE = {"detail": "Internal server error"}
NOT_FOUND_EXAMPLE = {"detail": "Task 7cbd20f3-6f31-4c7f-ba6b-c7bb4be8a88a not found"}
VALIDATION_EXAMPLE = {
    "detail": [
        {
            "type": "string_too_short",
            "loc": ["body", "description"],
            "msg": "String should have at least 5 characters",
            "input": "abc",
        }
    ]
}
INTERNAL_SERVER_ERROR_RESPONSE = {
    "description": "Erro interno inesperado. A resposta é sanitizada e não expõe detalhes.",
    "content": {"application/json": {"example": ERROR_EXAMPLE}},
}
VALIDATION_ERROR_RESPONSE = {
    "description": "Payload, parâmetros de rota ou query string inválidos.",
    "content": {"application/json": {"example": VALIDATION_EXAMPLE}},
}
NOT_FOUND_RESPONSE = {
    "description": "Tarefa não encontrada para o identificador informado.",
    "content": {"application/json": {"example": NOT_FOUND_EXAMPLE}},
}

router = APIRouter(tags=["Tasks"])


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
    summary="Create and categorize a task",
    description=(
        "Cria uma nova tarefa a partir de uma descrição em linguagem natural, chama o "
        "serviço de categorização por IA e persiste o resultado em um dos quatro "
        "quadrantes da Matriz de Eisenhower."
    ),
    response_description="Tarefa criada com quadrante, confiança e justificativa da IA.",
    responses={
        status.HTTP_201_CREATED: {
            "description": "Tarefa criada e classificada com sucesso.",
            "content": {
                "application/json": {
                    "examples": {
                        "created": {"summary": "Tarefa criada", "value": TASK_RESPONSE_EXAMPLE}
                    }
                }
            },
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: VALIDATION_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
async def create_task(
    payload: Annotated[
        TaskCreate,
        Body(
            openapi_examples={
                "urgent-important": {
                    "summary": "Tarefa urgente e importante",
                    "value": TASK_CREATE_EXAMPLE,
                }
            }
        ),
    ],
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Create a task and classify it into an Eisenhower Matrix quadrant."""
    return await service.create_and_categorize(payload.description)


@router.get(
    "/tasks",
    response_model=list[TaskResponse],
    summary="List tasks",
    description="Retorna todas as tarefas persistidas no quadro, em ordem de inserção.",
    response_description="Lista de tarefas categorizadas.",
    responses={
        status.HTTP_200_OK: {
            "description": "Lista retornada com sucesso.",
            "content": {
                "application/json": {
                    "examples": {
                        "with-task": {
                            "summary": "Lista com uma tarefa",
                            "value": [TASK_RESPONSE_EXAMPLE],
                        }
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
async def list_tasks(service: TaskService = Depends(get_task_service)) -> list[Task]:
    """List all persisted tasks in insertion order."""
    return await _await_service_result(service.get_all_tasks())


@router.get(
    "/tasks/distribution",
    response_model=DistributionResponse,
    summary="Get task distribution",
    description=(
        "Calcula quantas tarefas existem em cada quadrante da Matriz de Eisenhower "
        "e inclui o total geral do quadro."
    ),
    response_description="Contadores por quadrante e total geral.",
    responses={
        status.HTTP_200_OK: {
            "description": "Distribuição calculada com sucesso.",
            "content": {
                "application/json": {
                    "examples": {
                        "distribution": {
                            "summary": "Distribuição por quadrante",
                            "value": DISTRIBUTION_RESPONSE_EXAMPLE,
                        }
                    }
                }
            },
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
async def get_tasks_distribution(
    service: TaskService = Depends(get_task_service),
) -> DistributionResponse:
    """Return task counts for every Eisenhower Matrix quadrant."""
    return await _await_service_result(service.get_distribution())


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
    description="Busca uma tarefa específica pelo UUID informado na rota.",
    response_description="Tarefa encontrada.",
    responses={
        status.HTTP_200_OK: {
            "description": "Tarefa encontrada com sucesso.",
            "content": {
                "application/json": {
                    "examples": {
                        "found": {"summary": "Tarefa encontrada", "value": TASK_RESPONSE_EXAMPLE}
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: VALIDATION_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
async def get_task(
    task_id: UUID,
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Fetch a single task by its UUID identifier."""
    try:
        return await _await_service_result(service.get_task_by_id(task_id))
    except TaskNotFoundError as exc:
        raise _not_found_error(exc) from exc


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Manually update a task quadrant",
    description=(
        "Atualiza manualmente uma tarefa existente. O uso principal é corrigir ou "
        "sobrescrever o quadrante atribuído pela IA."
    ),
    response_description="Tarefa atualizada.",
    responses={
        status.HTTP_200_OK: {
            "description": "Tarefa atualizada com sucesso.",
            "content": {
                "application/json": {
                    "examples": {
                        "updated": {"summary": "Tarefa atualizada", "value": TASK_RESPONSE_EXAMPLE}
                    }
                }
            },
        },
        status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: VALIDATION_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
async def update_task_quadrant(
    task_id: UUID,
    payload: Annotated[
        TaskUpdate,
        Body(
            openapi_examples={
                "manual-reclassification": {
                    "summary": "Recategorização manual",
                    "value": TASK_UPDATE_EXAMPLE,
                }
            }
        ),
    ],
    service: TaskService = Depends(get_task_service),
) -> Task:
    """Manually reclassify an existing task into another quadrant."""
    if payload.quadrant is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="quadrant is required for manual reclassification",
        )

    try:
        return await _await_service_result(service.update_quadrant(task_id, payload.quadrant))
    except TaskNotFoundError as exc:
        raise _not_found_error(exc) from exc


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Remove definitivamente uma tarefa do quadro DoneFlow pelo UUID informado.",
    response_description="Tarefa removida sem corpo de resposta.",
    responses={
        status.HTTP_204_NO_CONTENT: {"description": "Tarefa removida com sucesso."},
        status.HTTP_404_NOT_FOUND: NOT_FOUND_RESPONSE,
        status.HTTP_422_UNPROCESSABLE_CONTENT: VALIDATION_ERROR_RESPONSE,
        status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
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
