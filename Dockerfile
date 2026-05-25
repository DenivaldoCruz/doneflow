FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip \
    && pip install --prefix=/install .


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=8000 \
    UVICORN_WORKERS=2 \
    APP_MODULE=src.doneflow.api.main:app

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY --from=builder /install /usr/local
COPY src ./src

EXPOSE 8000

USER appuser

CMD ["sh", "-c", "uvicorn ${APP_MODULE} --host ${UVICORN_HOST} --port ${UVICORN_PORT} --workers ${UVICORN_WORKERS}"]
