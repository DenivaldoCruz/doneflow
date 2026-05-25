"""Unit tests for TaskRepository using in-memory SQLite (TDD RED phase)."""

from __future__ import annotations

from datetime import datetime, timezone
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from sqlalchemy import create_engine

from doneflow.database import Base, SessionLocal
from doneflow.models.quadrant import Quadrant
from doneflow.repositories.task_repository import TaskRepository



def test_create_persists_and_returns_task_with_generated_id() -> None:
    """create should persist a task and return it with a generated id."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Finalizar proposta para cliente estratégico",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.95,
        ai_reasoning="Prazo hoje com alto impacto no fechamento do trimestre.",
    )

    assert created.id is not None
    assert created.description == "Finalizar proposta para cliente estratégico"
    assert created.quadrant == Quadrant.DO_NOW



def test_get_by_id_returns_existing_task() -> None:
    """get_by_id should return a previously persisted task."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Agendar reunião de alinhamento semanal",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.88,
    )

    found = repository.get_by_id(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id=created.id,
    )

    assert found is not None
    assert found.id == created.id
    assert found.description == "Agendar reunião de alinhamento semanal"



def test_get_by_id_returns_none_for_nonexistent_id() -> None:
    """get_by_id should return None when task id does not exist."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    found = repository.get_by_id(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id="00000000-0000-0000-0000-000000000000",
    )

    assert found is None



def test_get_all_returns_complete_list() -> None:
    """get_all should return all persisted tasks."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Responder e-mails pendentes",
        quadrant=Quadrant.DELEGATE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.72,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Definir metas da próxima sprint",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.84,
    )

    tasks = repository.get_all(session_factory=lambda: SessionLocal(bind=engine))

    assert len(tasks) == 2



def test_get_by_quadrant_filters_tasks_correctly() -> None:
    """get_by_quadrant should return only tasks matching requested quadrant."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Preparar relatório urgente de incidentes",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.93,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Limpar caixa de entrada sem prioridade",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.66,
    )

    do_now_tasks = repository.get_by_quadrant(
        session_factory=lambda: SessionLocal(bind=engine),
        quadrant=Quadrant.DO_NOW,
    )

    assert len(do_now_tasks) == 1
    assert do_now_tasks[0].quadrant == Quadrant.DO_NOW



def test_update_quadrant_updates_and_persists_change() -> None:
    """update_quadrant should change task quadrant and persist the change."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Coletar materiais de apoio",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.81,
    )

    updated = repository.update_quadrant(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id=created.id,
        quadrant=Quadrant.DELEGATE,
    )
    persisted = repository.get_by_id(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id=created.id,
    )

    assert updated is not None
    assert updated.quadrant == Quadrant.DELEGATE
    assert persisted is not None
    assert persisted.quadrant == Quadrant.DELEGATE



def test_delete_removes_task_and_returns_true() -> None:
    """delete should remove an existing task and return True."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    created = repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Cancelar assinatura sem uso",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.77,
    )

    deleted = repository.delete(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id=created.id,
    )
    found_after_delete = repository.get_by_id(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id=created.id,
    )

    assert deleted is True
    assert found_after_delete is None



def test_delete_returns_false_for_nonexistent_id() -> None:
    """delete should return False when task id does not exist."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    deleted = repository.delete(
        session_factory=lambda: SessionLocal(bind=engine),
        task_id="00000000-0000-0000-0000-000000000000",
    )

    assert deleted is False



def test_get_distribution_returns_correct_count_per_quadrant() -> None:
    """get_distribution should return counts grouped by quadrant."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    repository = TaskRepository()

    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Resolver bug em produção com prazo hoje",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.97,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Planejar treinamentos do próximo mês",
        quadrant=Quadrant.SCHEDULE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.83,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Delegar atualização de dashboard",
        quadrant=Quadrant.DELEGATE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.79,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Arquivar notificações irrelevantes",
        quadrant=Quadrant.ELIMINATE,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.7,
    )
    repository.create(
        session_factory=lambda: SessionLocal(bind=engine),
        description="Revisar contrato com deadline imediato",
        quadrant=Quadrant.DO_NOW,
        created_at=datetime.now(timezone.utc),
        ai_confidence=0.92,
    )

    distribution = repository.get_distribution(session_factory=lambda: SessionLocal(bind=engine))

    assert distribution[Quadrant.DO_NOW] == 2
    assert distribution[Quadrant.SCHEDULE] == 1
    assert distribution[Quadrant.DELEGATE] == 1
    assert distribution[Quadrant.ELIMINATE] == 1
