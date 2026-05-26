"""Unit tests for PromptBuilder (TDD RED phase)."""

from __future__ import annotations

from importlib import import_module

import pytest


KEYWORDS_URGENCIA = ("hoje", "urgente", "deadline", "prazo", "cliente", "entrega")
QUADRANTES_COM_DESCRICAO = {
    "DO_NOW": "urgente e importante",
    "SCHEDULE": "não urgente e importante",
    "DELEGATE": "urgente e não importante",
    "ELIMINATE": "não urgente e não importante",
}
CRITERIOS_RF03 = (
    "urgência",
    "importância",
    "impacto",
    "consequ",
)


def _load_prompt_builder_class() -> type | None:
    """Load PromptBuilder class from known module locations."""
    candidate_locations = (
        "doneflow.services.prompt_builder:PromptBuilder",
        "doneflow.services.ai.prompt_builder:PromptBuilder",
        "doneflow.services.ai_categorization_service:PromptBuilder",
    )

    for location in candidate_locations:
        module_name, symbol_name = location.split(":")
        try:
            module = import_module(module_name)
        except ImportError:
            continue

        prompt_builder = getattr(module, symbol_name, None)
        if prompt_builder is not None:
            return prompt_builder

    return None


@pytest.fixture
def prompt_builder_class() -> type:
    """Return PromptBuilder class under test."""
    prompt_builder = _load_prompt_builder_class()
    assert prompt_builder is not None, "PromptBuilder deve existir na camada de serviços"
    return prompt_builder


@pytest.fixture
def generated_prompt(prompt_builder_class: type) -> str:
    """Generate prompt using a representative task description."""
    builder = prompt_builder_class()
    prompt = builder.build_prompt("Preparar entrega urgente para cliente com prazo hoje")
    assert isinstance(prompt, str)
    return prompt


def test_prompt_builder_returns_non_empty_string(generated_prompt: str) -> None:
    """PromptBuilder should return a non-empty string output."""
    assert generated_prompt.strip() != ""


def test_prompt_contains_task_description(generated_prompt: str) -> None:
    """Generated prompt should include the original task description."""
    assert "Preparar entrega urgente para cliente com prazo hoje" in generated_prompt


def test_prompt_contains_json_output_instruction(generated_prompt: str) -> None:
    """Generated prompt should explicitly instruct JSON output."""
    lowered = generated_prompt.casefold()
    assert "json" in lowered
    assert "retorne" in lowered or "responda" in lowered


@pytest.mark.parametrize("quadrant, description", QUADRANTES_COM_DESCRICAO.items())
def test_prompt_contains_all_quadrants_with_descriptions(
    generated_prompt: str,
    quadrant: str,
    description: str,
) -> None:
    """Generated prompt should mention all quadrants and their semantic descriptions."""
    lowered = generated_prompt.casefold()
    assert quadrant in generated_prompt
    assert description in lowered


@pytest.mark.parametrize("criterion", CRITERIOS_RF03)
def test_prompt_contains_rf03_urgency_and_importance_criteria(
    generated_prompt: str,
    criterion: str,
) -> None:
    """Generated prompt should include RF-03 urgency/importance evaluation criteria."""
    assert criterion in generated_prompt.casefold()


@pytest.mark.parametrize("keyword", KEYWORDS_URGENCIA)
def test_prompt_references_urgency_keywords_in_instructions(
    generated_prompt: str,
    keyword: str,
) -> None:
    """Generated prompt should reference urgency keywords used by classifier rules."""
    assert keyword in generated_prompt.casefold()
