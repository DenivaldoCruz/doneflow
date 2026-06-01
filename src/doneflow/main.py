"""Principal FastAPI application for DoneFlow."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from doneflow import __version__
from doneflow.api.routes.health import router as health_router
from doneflow.api.routes.tasks import router as tasks_router
from doneflow.database import Base, engine

LOGGER = logging.getLogger(__name__)
API_PREFIX = "/api/v1"
OPENAPI_DESCRIPTION = (
    "DoneFlow é uma API FastAPI para organizar tarefas com IA usando a Matriz de "
    "Eisenhower. O fluxo principal recebe uma descrição em linguagem natural, classifica "
    "a tarefa com Claude ou fallback determinístico, persiste o resultado e expõe o "
    "quadro por endpoints REST.\n\n"
    "Quadrantes suportados:\n"
    "* `DO_NOW`: urgente e importante.\n"
    "* `SCHEDULE`: importante e não urgente.\n"
    "* `DELEGATE`: urgente e não importante.\n"
    "* `ELIMINATE`: não urgente e não importante.\n\n"
    "Todos os endpoints retornam JSON e documentam respostas de validação, ausência de "
    "recurso e erro interno quando aplicável."
)
OPENAPI_TAGS = [
    {"name": "Tasks", "description": "Task board and AI categorization operations."},
    {"name": "Health", "description": "Service uptime and dependency health checks."},
]
STATIC_DIR = Path(__file__).parent / "static"
INDEX_FILE = STATIC_DIR / "index.html"

CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
}


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
    openapi_tags=OPENAPI_TAGS,
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
async def add_security_headers(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    """Attach privacy-oriented browser security headers to every response.

    Args:
        request: Incoming FastAPI request.
        call_next: Next ASGI handler in the middleware chain.

    Returns:
        Response with standard content-sniffing and framing protections.
    """
    response = await call_next(request)
    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers.setdefault(header_name, header_value)
    return response


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


@app.get("/", response_class=FileResponse)
async def read_frontend_index() -> FileResponse:
    """Serve the DoneFlow static frontend entry document.

    Returns:
        File response containing the DoneFlow HTML shell.
    """
    return FileResponse(INDEX_FILE, media_type="text/html")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Convert unhandled errors into sanitized JSON responses.

    Args:
        request: Request that triggered the unhandled exception.
        exc: Original exception, logged internally only.

    Returns:
        Generic HTTP 500 response that does not expose implementation details.
    """
    LOGGER.error(
        "unhandled_exception method=%s path=%s exception_type=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers=SECURITY_HEADERS,
    )


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(tasks_router, prefix=API_PREFIX)
app.include_router(health_router)
