"""SQLAlchemy configuration and ORM mapping for DoneFlow."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, String, Text, Uuid, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from doneflow.config import get_settings

settings = get_settings()

connect_args: dict[str, bool] = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionFactory = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)


class Base(DeclarativeBase):
    """Declarative SQLAlchemy base for ORM models."""


class TaskORM(Base):
    """SQLAlchemy mapping for the tasks table."""

    __tablename__ = "tasks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    text: Mapped[str] = mapped_column(String(500), nullable=False)
    quadrant: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    ai_reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)


@contextmanager
def session_local(*, bind: object | None = None) -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and guarantee proper cleanup.

    Args:
        bind: Optional engine/connection override, useful for tests.

    Yields:
        SQLAlchemy ``Session`` instance.
    """
    session = SessionFactory() if bind is None else SessionFactory(bind=bind)
    try:
        yield session
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for FastAPI dependency injection."""
    with session_local() as session:
        yield session
