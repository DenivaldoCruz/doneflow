"""Unit checks for the DoneFlow REST API JavaScript module."""

from __future__ import annotations

import re
from pathlib import Path

API_MODULE = Path("src/doneflow/static/js/api.js")


def _read_api_module() -> str:
    """Read the frontend API module under test."""
    assert API_MODULE.exists()
    return API_MODULE.read_text(encoding="utf-8")


def test_static_api_module_exports_async_functions_for_prd_section_5_3_endpoints() -> None:
    """The module exposes async integrations for every PRD section 5.3 endpoint."""
    source = _read_api_module()

    expected_exports = {
        "createTask": "POST",
        "getAllTasks": "GET",
        "getTaskById": "GET",
        "updateTaskQuadrant": "PATCH",
        "deleteTask": "DELETE",
        "getDistribution": "GET",
        "getHealth": "GET",
    }

    for function_name, method in expected_exports.items():
        assert re.search(rf"export async function {function_name}\(", source)
        assert f'method: "{method}"' in source or f'method = "{method}"' in source

    assert 'API_BASE_URL = "/api/v1"' in source
    for endpoint_fragment in (
        "/tasks",
        "/tasks/${id}",
        "/tasks/distribution",
        "/health",
    ):
        assert endpoint_fragment in source


def test_static_api_module_declares_typed_jsdoc_contracts() -> None:
    """API responses and public functions are documented with JSDoc typedefs."""
    source = _read_api_module()

    for typedef in ("Quadrant", "Task", "Distribution", "HealthResponse", "ApiErrorPayload"):
        assert "@typedef" in source
        assert typedef in source

    expected_returns = {
        "createTask": "@returns {Promise<Task>}",
        "getAllTasks": "@returns {Promise<Task[]>}",
        "getTaskById": "@returns {Promise<Task>}",
        "updateTaskQuadrant": "@returns {Promise<Task>}",
        "deleteTask": "@returns {Promise<void>}",
        "getDistribution": "@returns {Promise<Distribution>}",
        "getHealth": "@returns {Promise<HealthResponse>}",
    }

    for function_name, return_tag in expected_returns.items():
        pattern = rf"/\*\*[\s\S]*?{re.escape(return_tag)}[\s\S]*?\*/\nexport async function {function_name}"
        assert re.search(pattern, source), f"missing typed JSDoc for {function_name}"


def test_static_api_module_handles_http_errors_with_pt_br_messages() -> None:
    """HTTP and network failures are converted into friendly Portuguese errors."""
    source = _read_api_module()

    for status_code in (400, 404, 422, 500):
        assert str(status_code) in source

    for message in (
        "Não foi possível processar a solicitação.",
        "Tarefa não encontrada.",
        "Revise os dados enviados e tente novamente.",
        "Ocorreu um erro interno no DoneFlow.",
        "Não foi possível conectar ao DoneFlow.",
    ):
        assert message in source

    assert "response.ok" in source
    assert "throw new Error" in source
