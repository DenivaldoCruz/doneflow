"""Health-check routes for DoneFlow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from doneflow import __version__, database

router = APIRouter(tags=["health"])

DatabaseStatus = Literal["connected", "disconnected"]


def _database_status() -> DatabaseStatus:
    """Check whether the configured database accepts a trivial query.

    Returns:
        ``connected`` when the database responds, otherwise ``disconnected``.
    """
    try:
        with database.SessionFactory() as session:
            session.execute(text("SELECT 1"))
        return "connected"
    except SQLAlchemyError:
        return "disconnected"


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Report service, version, timestamp, and database health.

    Returns:
        JSON-compatible health contract for uptime probes and load balancers.
    """
    return {
        "status": "ok",
        "version": __version__,
        "timestamp": datetime.now(UTC).isoformat(),
        "database": _database_status(),
    }
