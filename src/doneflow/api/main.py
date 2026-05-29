"""FastAPI application factory for DoneFlow."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from doneflow.api.routes.tasks import router as tasks_router
from doneflow.database import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize application resources for the FastAPI lifespan.

    Yields:
        Control back to FastAPI after the database tables are available.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DoneFlow API",
    description="AI-powered Eisenhower Matrix task categorization API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tasks_router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Report API health for uptime probes and load balancers."""
    return {"status": "ok"}
