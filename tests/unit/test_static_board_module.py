"""Unit checks for the DoneFlow Eisenhower board JavaScript module."""

from __future__ import annotations

import re
from pathlib import Path

BOARD_MODULE = Path("src/doneflow/static/js/board.js")


def _read_board_module() -> str:
    """Read the frontend board module under test."""
    assert BOARD_MODULE.exists()
    return BOARD_MODULE.read_text(encoding="utf-8")


def test_static_board_module_exports_required_public_functions() -> None:
    """The module exposes vanilla ES module functions for board interactions."""
    source = _read_board_module()

    for function_name in (
        "renderBoard",
        "addCard",
        "removeCard",
        "updateDistributionPanel",
        "showLoadingState",
        "hideLoadingState",
        "updateCounters",
    ):
        assert re.search(rf"export function {function_name}\(", source)

    assert "export const QUADRANTS" in source
    assert "DO_NOW" in source
    assert "SCHEDULE" in source
    assert "DELEGATE" in source
    assert "ELIMINATE" in source


def test_static_board_module_targets_quadrant_card_regions_and_badges() -> None:
    """Cards are routed to the correct quadrant containers and counters."""
    source = _read_board_module()

    for card_region_id in (
        "cards-do-now",
        "cards-schedule",
        "cards-delegate",
        "cards-eliminate",
    ):
        assert card_region_id in source

    assert "data-quadrant" in source
    assert "quadrant__count" in source
    assert "task-card" in source
    assert "task-card__text" in source
    assert "task-card__remove" in source
    assert "task-card__meta" in source
    assert "data-task-id" in source


def test_static_board_module_implements_card_and_loading_animations() -> None:
    """Card entry, exit, and loading states use CSS animation hooks without frameworks."""
    source = _read_board_module()

    assert "task-card--entering" in source
    assert "task-card--removing" in source
    assert "task-card--loading" in source
    assert "requestAnimationFrame" in source
    assert "transitionend" in source
    assert "setTimeout" in source
    assert "appendChild" in source
    assert "remove()" in source
    assert "document.createElement" in source


def test_static_board_module_updates_distribution_bars_with_percentages() -> None:
    """Distribution panel labels and bars are animated from distribution counts."""
    source = _read_board_module()

    assert "distribution__item" in source
    assert "distribution__fill" in source
    assert "distribution__meta" in source
    assert "--value" in source
    assert "Math.round" in source
    assert "total" in source
    assert "aria-valuenow" in source


def test_static_board_module_declares_typed_jsdoc_contracts() -> None:
    """Public board functions document their task and distribution contracts."""
    source = _read_board_module()

    for typedef in ("Quadrant", "BoardTask", "Distribution"):
        assert "@typedef" in source
        assert typedef in source

    expected_params = {
        "renderBoard": "@param {BoardTask[]} tasks",
        "addCard": "@param {BoardTask} task",
        "removeCard": "@param {string | number} taskId",
        "updateDistributionPanel": "@param {Distribution} distribution",
        "showLoadingState": "@param {Quadrant} quadrant",
        "hideLoadingState": "@param {Quadrant} quadrant",
    }

    for function_name, param_tag in expected_params.items():
        pattern = (
            rf"/\*\*[\s\S]*?{re.escape(param_tag)}[\s\S]*?\*/\nexport function {function_name}"
        )
        assert re.search(pattern, source), f"missing typed JSDoc for {function_name}"
