"""Unit checks for the DoneFlow static HTML shell and board stylesheet."""

from __future__ import annotations

from pathlib import Path

INDEX_TEMPLATE = Path("src/doneflow/static/index.html")
BOARD_STYLESHEET = Path("src/doneflow/static/css/board.css")


def test_static_index_template_matches_prd_section_7_layout() -> None:
    """The base template provides the section 7 dark 2x2 Eisenhower board."""
    assert INDEX_TEMPLATE.exists()
    assert BOARD_STYLESHEET.exists()

    html = INDEX_TEMPLATE.read_text(encoding="utf-8")
    css = BOARD_STYLESHEET.read_text(encoding="utf-8")

    assert 'href="/static/css/board.css"' in html
    assert "#0F1419" in css
    assert "#1A2332" in css
    assert "display: grid" in css
    assert "grid-template-columns" in css
    assert "grid-template-areas" in css
    assert "JetBrains Mono" in css
    assert "Descreva sua tarefa" in html
    assert "Painel de distribuição" in html
    assert "Matriz de Eisenhower" in html

    for quadrant in ("DO_NOW", "SCHEDULE", "DELEGATE", "ELIMINATE"):
        assert f'data-quadrant="{quadrant}"' in html
        assert f'id="cards-{quadrant.lower().replace("_", "-")}"' in html


def test_static_index_template_has_required_quadrant_components() -> None:
    """Each quadrant includes title, icon, counter, and card drop area hooks."""
    html = INDEX_TEMPLATE.read_text(encoding="utf-8")

    assert html.count('class="quadrant__icon"') == 4
    assert html.count('class="quadrant__title"') == 4
    assert html.count('class="quadrant__count"') == 4
    assert html.count('class="quadrant__cards"') == 4
    assert html.count('class="task-card"') >= 4


def test_board_stylesheet_defines_requested_eisenhower_interactions() -> None:
    """The board stylesheet owns layout, quadrant colors, animation, and loading states."""
    html = INDEX_TEMPLATE.read_text(encoding="utf-8")
    css = BOARD_STYLESHEET.read_text(encoding="utf-8")

    assert "--do-now: #C0392B" in css
    assert "--schedule: #2980B9" in css
    assert "--delegate: #E6A817" in css
    assert "--eliminate: #555555" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert "@media (max-width: 960px)" in css
    assert ".task-card:hover" in css
    assert ".task-card__remove" in css
    assert "@keyframes card-enter" in css
    assert "@keyframes skeleton-shimmer" in css
    assert ".task-card--loading" in css
    assert ".distribution__fill" in css
    assert "@keyframes distribution-fill" in css
    assert ".board__axis" in css
    assert "Importância" in html
    assert "Urgência" in html


def test_board_stylesheet_defines_app_entry_feedback_states() -> None:
    """The stylesheet supports app.js loading and toast feedback states."""
    css = BOARD_STYLESHEET.read_text(encoding="utf-8")

    assert ".new-task--loading" in css
    assert ".button:disabled" in css
    assert ".toast-region" in css
    assert ".toast" in css
    assert ".toast--error" in css
    assert ".toast--success" in css
    assert ".toast--leaving" in css
