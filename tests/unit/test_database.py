"""Unit tests for SQLAlchemy database configuration."""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime

from sqlalchemy import Engine, inspect

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from doneflow.database import Base, TaskORM, get_db, session_local  # noqa: E402


def test_session_local_uses_context_manager_and_closes_session() -> None:
    """session_local context manager should yield a session and close it afterwards."""
    with session_local() as session:
        assert session.is_active

    assert session.get_bind() is not None


def test_get_db_yields_a_session_instance() -> None:
    """get_db should provide a SQLAlchemy session for FastAPI dependencies."""
    generator = get_db()
    session = next(generator)

    assert session.get_bind() is not None

    try:
        next(generator)
    except StopIteration:
        pass


def test_tasks_table_contains_expected_columns(sqlite_engine: Engine) -> None:
    """Tasks table should map all required Task model columns."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine, tables=[TaskORM.__table__])

    inspector = inspect(engine)
    columns = {column["name"] for column in inspector.get_columns("tasks")}

    assert columns == {
        "id",
        "text",
        "quadrant",
        "created_at",
        "ai_confidence",
        "ai_reasoning",
    }


def test_taskorm_persists_and_reads_all_fields(sqlite_engine: Engine) -> None:
    """TaskORM should persist values for all mapped columns."""
    engine = sqlite_engine
    Base.metadata.create_all(bind=engine, tables=[TaskORM.__table__])

    task_id = uuid.uuid4()
    created_at = datetime.now(UTC)

    with session_local(bind=engine) as session:
        task = TaskORM(
            id=task_id,
            text="Finalizar planejamento trimestral",
            quadrant="DO_NOW",
            created_at=created_at,
            ai_confidence=0.91,
            ai_reasoning="Prazo nesta semana com impacto alto.",
        )
        session.add(task)
        session.commit()
        stored = session.get(TaskORM, task_id)

    assert stored is not None
    assert stored.id == task_id
    assert stored.text == "Finalizar planejamento trimestral"
    assert stored.quadrant == "DO_NOW"
    assert stored.ai_confidence == 0.91
    assert stored.ai_reasoning == "Prazo nesta semana com impacto alto."
