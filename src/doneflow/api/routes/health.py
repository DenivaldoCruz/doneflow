"""Health-check routes for DoneFlow."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from doneflow import __version__, database

HEALTH_RESPONSE_EXAMPLE: dict[str, Any] = {
    "status": "ok",
    "version": "0.4.0",
    "timestamp": "2026-05-25T12:00:00+00:00",
    "database": "connected",
}
INTERNAL_SERVER_ERROR_RESPONSE = {
    "description": "Erro interno inesperado. A resposta é sanitizada e não expõe detalhes.",
    "content": {"application/json": {"example": {"detail": "Internal server error"}}},
}

router = APIRouter(tags=["Health"])

DatabaseStatus = Literal["connected", "disconnected"]


class HealthResponse(BaseModel):
    """Health-check response for uptime probes and dependency monitoring."""

    model_config = ConfigDict(json_schema_extra={"examples": [HEALTH_RESPONSE_EXAMPLE]})

    status: Literal["ok"] = Field(description="Overall application status.")
    version: str = Field(description="DoneFlow application version.")
    timestamp: str = Field(description="Current server timestamp in ISO 8601 format.")
    database: DatabaseStatus = Field(description="Connectivity status for the configured database.")


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


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description=(
        "Retorna o status operacional da API DoneFlow, a versão implantada, o horário "
        "da verificação e a conectividade do banco de dados."
    ),
    response_description="Status operacional da aplicação e do banco de dados.",
    responses={
        200: {
            "description": "Serviço disponível.",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {"summary": "Serviço saudável", "value": HEALTH_RESPONSE_EXAMPLE}
                    }
                }
            },
        },
        500: INTERNAL_SERVER_ERROR_RESPONSE,
    },
)
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
