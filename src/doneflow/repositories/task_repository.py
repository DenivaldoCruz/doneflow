"""Task repository implementation backed by SQLAlchemy."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from doneflow.database import TaskORM
from doneflow.models.quadrant import Quadrant
from doneflow.models.task import Task


class TaskRepository:
    """Repository responsible for CRUD and read models for tasks."""

    def create(
        self,
        *,
        session_factory: Callable[[], Session],
        description: str,
        quadrant: Quadrant,
        created_at: datetime,
        ai_confidence: float,
        ai_reasoning: str | None = None,
    ) -> Task:
        """Create and persist a new task."""
        with session_factory() as session:
            try:
                orm_task = TaskORM(
                    text=description,
                    quadrant=quadrant.value,
                    created_at=created_at,
                    ai_confidence=ai_confidence,
                    ai_reasoning=ai_reasoning,
                )
                session.add(orm_task)
                session.commit()
                session.refresh(orm_task)
                return self._to_domain(orm_task)
            except SQLAlchemyError:
                session.rollback()
                raise

    def get_by_id(
        self, *, session_factory: Callable[[], Session], task_id: UUID | str
    ) -> Task | None:
        """Fetch a task by its identifier."""
        with session_factory() as session:
            return self._fetch_task_by_id(session=session, task_id=task_id)

    def get_all(self, *, session_factory: Callable[[], Session]) -> list[Task]:
        """Return all persisted tasks."""
        with session_factory() as session:
            statement = select(TaskORM)
            result = session.execute(statement).scalars().all()
            return [self._to_domain(task) for task in result]

    def get_by_quadrant(
        self,
        *,
        session_factory: Callable[[], Session],
        quadrant: Quadrant,
    ) -> list[Task]:
        """Return tasks filtered by a specific quadrant."""
        with session_factory() as session:
            statement = select(TaskORM).where(TaskORM.quadrant == quadrant.value)
            result = session.execute(statement).scalars().all()
            return [self._to_domain(task) for task in result]

    def update_quadrant(
        self,
        *,
        session_factory: Callable[[], Session],
        task_id: UUID | str,
        quadrant: Quadrant,
    ) -> Task | None:
        """Update quadrant for an existing task."""
        with session_factory() as session:
            try:
                task = self._fetch_orm_task_by_id(session=session, task_id=task_id)
                if task is None:
                    return None

                task.quadrant = quadrant.value
                session.commit()
                session.refresh(task)
                return self._to_domain(task)
            except SQLAlchemyError:
                session.rollback()
                raise

    def delete(self, *, session_factory: Callable[[], Session], task_id: UUID | str) -> bool:
        """Delete a task by identifier."""
        with session_factory() as session:
            try:
                task = self._fetch_orm_task_by_id(session=session, task_id=task_id)
                if task is None:
                    return False

                session.delete(task)
                session.commit()
                return True
            except SQLAlchemyError:
                session.rollback()
                raise

    def get_distribution(self, *, session_factory: Callable[[], Session]) -> dict[Quadrant, int]:
        """Return task distribution grouped by quadrant."""
        with session_factory() as session:
            statement = select(TaskORM.quadrant, func.count(TaskORM.id)).group_by(TaskORM.quadrant)
            rows = session.execute(statement).all()
            distribution = {quadrant: 0 for quadrant in Quadrant}
            for quadrant_value, count in rows:
                distribution[Quadrant.from_string(quadrant_value)] = int(count)
            return distribution

    def _fetch_task_by_id(self, *, session: Session, task_id: UUID | str) -> Task | None:
        """Fetch a domain task by id within an existing session."""
        orm_task = self._fetch_orm_task_by_id(session=session, task_id=task_id)
        if orm_task is None:
            return None
        return self._to_domain(orm_task)

    def _fetch_orm_task_by_id(self, *, session: Session, task_id: UUID | str) -> TaskORM | None:
        """Fetch raw ORM task by identifier."""
        normalized_id = UUID(str(task_id)) if isinstance(task_id, str) else task_id
        statement = select(TaskORM).where(TaskORM.id == normalized_id)
        return session.execute(statement).scalar_one_or_none()

    def _to_domain(self, orm_task: TaskORM) -> Task:
        """Convert SQLAlchemy ORM model to domain model."""
        return Task(
            id=orm_task.id,
            description=orm_task.text,
            quadrant=Quadrant.from_string(orm_task.quadrant),
            created_at=self._ensure_utc(orm_task.created_at),
            updated_at=self._ensure_utc(orm_task.created_at),
            ai_confidence=orm_task.ai_confidence,
            ai_reasoning=orm_task.ai_reasoning,
        )

    def _ensure_utc(self, value: datetime) -> datetime:
        """Ensure datetime has UTC timezone information for domain validation."""
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
