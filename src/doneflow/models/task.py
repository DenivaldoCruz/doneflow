"""ORM Task model for DoneFlow (SQLAlchemy)."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String

from .base import Base


class Task(Base):
    """Database model representing a task.

    Minimal set of columns is implemented to satisfy unit tests for
    RF-01: description validation and created_at timestamp.
    """

    __tablename__ = "tasks"

    id: int = Column(Integer, primary_key=True)
    description: str = Column(String, nullable=False)
    quadrant: Optional[str] = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, *args, **kwargs) -> None:
        """Initialize Task and ensure created_at is set on instance creation.

        SQLAlchemy's Column default may be applied on INSERT; for tests and
        convenience we set created_at at construction time if not provided.
        """
        super().__init__(*args, **kwargs)
        if getattr(self, "created_at", None) is None:
            self.created_at = datetime.utcnow()

    def __repr__(self) -> str:  # pragma: no cover - trivial helper
        return f"<Task id={self.id} description={self.description!r}>"

