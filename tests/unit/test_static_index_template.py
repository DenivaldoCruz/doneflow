"""Unit checks for the DoneFlow static HTML shell."""

from __future__ import annotations

from pathlib import Path

INDEX_TEMPLATE = Path("src/doneflow/static/index.html")


def test_static_index_template_matches_prd_section_7_layout() -> None:
    """The base template provides the section 7 dark 2x2 Eisenhower board."""
    assert INDEX_TEMPLATE.exists()

    html = INDEX_TEMPLATE.read_text(encoding="utf-8")

    assert "#0F1419" in html
    assert "#1A2332" in html
    assert "display: grid" in html
    assert "grid-template-columns" in html
    assert "grid-template-areas" in html
    assert "JetBrains Mono" in html
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
