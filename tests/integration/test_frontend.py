"""Integration tests for serving the DoneFlow static frontend."""

from __future__ import annotations

import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient

from doneflow.main import app

pytestmark = pytest.mark.integration

EXPECTED_QUADRANTS = ("DO_NOW", "SCHEDULE", "DELEGATE", "ELIMINATE")


@pytest.fixture
def client() -> TestClient:
    """Create a FastAPI test client for frontend asset checks."""
    return TestClient(app)


def test_get_root_returns_html_frontend(client: TestClient) -> None:
    """GET / returns the DoneFlow index document as HTML."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!doctype html>" in response.text.lower()


def test_get_board_stylesheet_returns_200(client: TestClient) -> None:
    """GET /static/css/board.css serves the board stylesheet."""
    response = client.get("/static/css/board.css")

    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "--do-now: #C0392B" in response.text


def test_get_app_javascript_returns_200(client: TestClient) -> None:
    """GET /static/js/app.js serves the browser application module."""
    response = client.get("/static/js/app.js")

    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
    assert "initDoneFlowApp" in response.text


def test_root_html_contains_board_with_four_quadrants(client: TestClient) -> None:
    """The frontend shell includes the Eisenhower board and all four quadrants."""
    response = client.get("/")

    assert response.status_code == 200
    assert 'class="board"' in response.text
    assert "Matriz de Eisenhower" in response.text
    for quadrant in EXPECTED_QUADRANTS:
        assert f'data-quadrant="{quadrant}"' in response.text
