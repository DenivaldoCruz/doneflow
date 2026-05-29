"""Compatibility module exposing the principal DoneFlow FastAPI app."""

from __future__ import annotations

from doneflow.main import app, lifespan

__all__ = ["app", "lifespan"]
