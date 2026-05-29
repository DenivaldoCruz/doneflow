"""Principal FastAPI application for DoneFlow."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from doneflow import __version__
from doneflow.api.routes.health import router as health_router
from doneflow.api.routes.tasks import router as tasks_router
from doneflow.database import Base, engine

LOGGER = logging.getLogger(__name__)
API_PREFIX = "/api/v1"
OPENAPI_DESCRIPTION = (
    "DoneFlow is an AI-powered task categorization API that organizes work with "
    "the Eisenhower Matrix quadrants: DO_NOW, SCHEDULE, DELEGATE, and ELIMINATE."
)
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    """Create database tables during application startup.

    Yields:
        Control back to FastAPI after SQLAlchemy metadata has been created.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="DoneFlow API",
    description=OPENAPI_DESCRIPTION,
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Log request metadata without reading or logging task payload bodies.

    Args:
        request: Incoming FastAPI request.
        call_next: Next ASGI handler in the middleware chain.

    Returns:
        Response produced by downstream middleware or route handlers.
    """
    started_at = perf_counter()
    method = request.method
    path = request.url.path
    LOGGER.info("request_started method=%s path=%s", method, path)

    response = await call_next(request)
    duration_ms = (perf_counter() - started_at) * 1000
    LOGGER.info(
        "request_finished method=%s path=%s status_code=%s duration_ms=%.2f",
        method,
        path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert unhandled errors into sanitized JSON responses.

    Args:
        request: Request that triggered the unhandled exception.
        exc: Original exception, logged internally only.

    Returns:
        Generic HTTP 500 response that does not expose implementation details.
    """
    LOGGER.exception(
        "unhandled_exception method=%s path=%s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(health_router)
