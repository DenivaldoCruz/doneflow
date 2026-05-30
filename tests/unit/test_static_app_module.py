"""Unit checks for the DoneFlow browser entry point."""

from __future__ import annotations

import re
from pathlib import Path

APP_MODULE = Path("src/doneflow/static/js/app.js")
INDEX_TEMPLATE = Path("src/doneflow/static/index.html")


def _read_app_module() -> str:
    """Read the frontend application entry point under test."""
    assert APP_MODULE.exists()
    return APP_MODULE.read_text(encoding="utf-8")


def test_static_app_module_is_wired_as_es6_entry_point() -> None:
    """The static shell loads app.js as the DoneFlow ES module entry point."""
    html = INDEX_TEMPLATE.read_text(encoding="utf-8")
    source = _read_app_module()

    assert '<script type="module" src="/static/js/app.js"></script>' in html
    assert "import {" in source
    assert "./api.js" in source
    assert "./board.js" in source
    assert "DOMContentLoaded" in source
    assert re.search(r"export function initDoneFlowApp\(", source)


def test_static_app_module_loads_existing_tasks_on_startup() -> None:
    """Opening the page fetches all tasks and refreshes board/distribution state."""
    source = _read_app_module()

    assert "getAllTasks" in source
    assert "renderBoard" in source
    assert "getDistribution" in source
    assert "updateDistributionPanel" in source
    assert re.search(r"async function loadInitialTasks\(", source)
    assert "await getAllTasks()" in source
    assert "await refreshDistribution()" in source


def test_static_app_module_handles_enter_and_button_task_creation_flow() -> None:
    """Task creation works through the form button and Enter key listener."""
    source = _read_app_module()

    assert "task-description" in source
    assert "submit" in source
    assert "keydown" in source
    assert 'event.key === "Enter"' in source
    assert "!event.shiftKey" in source
    assert "requestSubmit" in source
    assert "createTask" in source
    assert "await createTask(description)" in source
    assert "addCard" in source


def test_static_app_module_validates_minimum_description_length_before_api_call() -> None:
    """Client-side validation rejects descriptions shorter than five characters."""
    source = _read_app_module()

    assert re.search(r"const MIN_TASK_DESCRIPTION_LENGTH = 5", source)
    assert re.search(r"export function validateTaskDescription\(", source)
    assert ".trim()" in source
    assert "length < MIN_TASK_DESCRIPTION_LENGTH" in source
    assert "A descrição precisa ter pelo menos 5 caracteres." in source


def test_static_app_module_uses_loading_indicator_and_pt_br_toasts() -> None:
    """The entry point provides loading feedback and Portuguese toast errors."""
    source = _read_app_module()

    assert "showLoadingState" in source
    assert "hideLoadingState" in source
    assert "setFormLoading" in source
    assert "aria-busy" in source
    assert "showToast" in source
    assert "toast" in source
    assert "Não foi possível carregar suas tarefas." in source
    assert "Não foi possível adicionar a tarefa." in source
    assert "Tarefa adicionada ao quadrante" in source
    assert "setTimeout" in source
