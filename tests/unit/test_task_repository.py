"""Unit tests for TaskRepository using in-memory SQLite (TDD RED phase)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from unittest.mock import MagicMock

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from doneflow.database import Base, session_local
from doneflow.models.quadrant import Quadrant
from doneflow.repositories.task_repository import TaskRepository


def test_create_persists_and_returns_task_with_generated_id(sqlite_engine: Engine) -> None:
    """create should persist a task and return it with a generated id."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Finalizar proposta para cliente estratégico",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(UTC),
        ai_confidence=0.95,
        ai_reasoning="Prazo hoje com alto impacto no fechamento do trimestre.",
    )

    assert created.id is not None
    assert created.description == "Finalizar proposta para cliente estratégico"
    assert created.quadrant == Quadrant.DO_NOW


def test_get_by_id_returns_existing_task(sqlite_engine: Engine) -> None:
    """get_by_id should return a previously persisted task."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Agendar reunião de alinhamento semanal",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(UTC),
        ai_confidence=0.88,
    )

    found = repository.get_by_id(
        session_factory=lambda: session_local(bind=engine),
        task_id=created.id,
    )

    assert found is not None
    assert found.id == created.id
    assert found.description == "Agendar reunião de alinhamento semanal"


def test_get_by_id_returns_none_for_nonexistent_id(sqlite_engine: Engine) -> None:
    """get_by_id should return None when task id does not exist."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    found = repository.get_by_id(
        session_factory=lambda: session_local(bind=engine),
        task_id="00000000-0000-0000-0000-000000000000",
    )

    assert found is None


def test_get_all_returns_complete_list(sqlite_engine: Engine) -> None:
    """get_all should return all persisted tasks."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Responder e-mails pendentes",
        quadrant=Quadrant.DELEGATE,
        created_at=datetime.now(UTC),
        ai_confidence=0.72,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Definir metas da próxima sprint",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(UTC),
        ai_confidence=0.84,
    )

    tasks = repository.get_all(session_factory=lambda: session_local(bind=engine))

    assert len(tasks) == 2


def test_get_by_quadrant_filters_tasks_correctly(sqlite_engine: Engine) -> None:
    """get_by_quadrant should return only tasks matching requested quadrant."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Preparar relatório urgente de incidentes",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(UTC),
        ai_confidence=0.93,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Limpar caixa de entrada sem prioridade",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(UTC),
        ai_confidence=0.66,
    )

    do_now_tasks = repository.get_by_quadrant(
        session_factory=lambda: session_local(bind=engine),
        quadrant=Quadrant.DO_NOW,
    )

    assert len(do_now_tasks) == 1
    assert do_now_tasks[0].quadrant == Quadrant.DO_NOW


def test_update_quadrant_updates_and_persists_change(sqlite_engine: Engine) -> None:
    """update_quadrant should change task quadrant and persist the change."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Coletar materiais de apoio",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(UTC),
        ai_confidence=0.81,
    )

    updated = repository.update_quadrant(
        session_factory=lambda: session_local(bind=engine),
        task_id=created.id,
        quadrant=Quadrant.DELEGATE,
    )
    persisted = repository.get_by_id(
        session_factory=lambda: session_local(bind=engine),
        task_id=created.id,
    )

    assert updated is not None
    assert updated.quadrant == Quadrant.DELEGATE
    assert persisted is not None
    assert persisted.quadrant == Quadrant.DELEGATE


def test_delete_removes_task_and_returns_true(sqlite_engine: Engine) -> None:
    """delete should remove an existing task and return True."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Cancelar assinatura sem uso",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(UTC),
        ai_confidence=0.77,
    )

    deleted = repository.delete(
        session_factory=lambda: session_local(bind=engine),
        task_id=created.id,
    )
    found_after_delete = repository.get_by_id(
        session_factory=lambda: session_local(bind=engine),
        task_id=created.id,
    )

    assert deleted is True
    assert found_after_delete is None


def test_delete_returns_false_for_nonexistent_id(sqlite_engine: Engine) -> None:
    """delete should return False when task id does not exist."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    deleted = repository.delete(
        session_factory=lambda: session_local(bind=engine),
        task_id="00000000-0000-0000-0000-000000000000",
    )

    assert deleted is False


def test_get_distribution_returns_correct_count_per_quadrant(sqlite_engine: Engine) -> None:
    """get_distribution should return counts grouped by quadrant."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Resolver bug em produção com prazo hoje",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(UTC),
        ai_confidence=0.97,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Planejar treinamentos do próximo mês",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(UTC),
        ai_confidence=0.83,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Delegar atualização de dashboard",
        quadrant=Quadrant.DELEGATE,
        created_at=datetime.now(UTC),
        ai_confidence=0.79,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Arquivar notificações irrelevantes",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(UTC),
        ai_confidence=0.7,
    )
    repository.create(
        session_factory=lambda: session_local(bind=engine),
        description="Revisar contrato com deadline imediato",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(UTC),
        ai_confidence=0.92,
    )

    distribution = repository.get_distribution(session_factory=lambda: session_local(bind=engine))

    assert distribution[Quadrant.DO_NOW] == 2
    assert distribution[Quadrant.SCHEDULE] == 1
    assert distribution[Quadrant.DELEGATE] == 1
    assert distribution[Quadrant.ELIMINATE] == 1


def test_create_rolls_back_and_reraises_on_sqlalchemy_error() -> None:
    """create should rollback and re-raise when commit fails."""
    repository = TaskRepository()
    session = MagicMock()
    session.commit.side_effect = SQLAlchemyError("commit failed")

    class _SessionContext:
        def __enter__(self) -> MagicMock:
            return session

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    with pytest.raises(SQLAlchemyError):
        repository.create(
            session_factory=lambda: _SessionContext(),
            description="Tarefa com falha no commit",
            quadrant=Quadrant.DO_NOW,
            created_at=datetime.now(UTC),
            ai_confidence=0.99,
        )

    session.rollback.assert_called_once()


def test_update_quadrant_rolls_back_and_reraises_on_sqlalchemy_error() -> None:
    """update_quadrant should rollback and re-raise when commit fails."""
    repository = TaskRepository()
    session = MagicMock()
    fake_task = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = fake_task
    session.commit.side_effect = SQLAlchemyError("commit failed")

    class _SessionContext:
        def __enter__(self) -> MagicMock:
            return session

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    with pytest.raises(SQLAlchemyError):
        repository.update_quadrant(
            session_factory=lambda: _SessionContext(),
            task_id="00000000-0000-0000-0000-000000000001",
            quadrant=Quadrant.SCHEDULE,
        )

    session.rollback.assert_called_once()


def test_delete_rolls_back_and_reraises_on_sqlalchemy_error() -> None:
    """delete should rollback and re-raise when delete operation fails."""
    repository = TaskRepository()
    session = MagicMock()
    fake_task = MagicMock()
    session.execute.return_value.scalar_one_or_none.return_value = fake_task
    session.commit.side_effect = SQLAlchemyError("commit failed")

    class _SessionContext:
        def __enter__(self) -> MagicMock:
            return session

        def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
            return None

    with pytest.raises(SQLAlchemyError):
        repository.delete(
            session_factory=lambda: _SessionContext(),
            task_id="00000000-0000-0000-0000-000000000002",
        )

    session.rollback.assert_called_once()
