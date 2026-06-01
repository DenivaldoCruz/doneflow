"""Unit tests for PromptBuilder (TDD RED phase)."""

from __future__ import annotations

from importlib import import_module

import pytest

KEYWORDS_BY_QUADRANT = {
    "DO_NOW": (
        "hoje",
        "urgente",
        "deadline",
        "agora",
        "prazo",
        "cliente",
        "entrega",
        "crítico",
        "incidente",
        "bloqueio",
    ),
    "SCHEDULE": (
        "roadmap",
        "produto",
        "estratégia",
        "proposta",
        "reunião",
        "ceo",
        "planejar",
        "trimestre",
        "objetivo",
        "melhoria",
    ),
    "DELEGATE": (
        "responder",
        "administrativo",
        "rotina",
        "solicitação",
        "operacional",
        "acompanhar",
        "cobrar",
        "confirmar",
    ),
    "ELIMINATE": (
        "sem prazo",
        "baixo impacto",
        "opcional",
        "talvez",
        "arquivo",
        "organizar",
        "figurinhas",
        "distração",
    ),
}
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
FEW_SHOT_TASKS_BY_QUADRANT = {
    "DO_NOW": (
        "Resolver incidente crítico de produção para cliente hoje",
        "Enviar proposta urgente ao CEO antes do deadline",
    ),
    "SCHEDULE": (
        "Definir roadmap de produto do próximo trimestre",
        "Planejar reunião estratégica de melhoria com a liderança",
    ),
    "DELEGATE": (
        "Responder solicitação administrativa urgente agora",
        "Confirmar entrega operacional com fornecedor ainda hoje",
    ),
    "ELIMINATE": (
        "Organizar figurinhas antigas sem prazo",
        "Pesquisar curiosidades opcionais de baixo impacto",
    ),
}


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
    """Generated prompt should explicitly instruct JSON-only output without markdown."""
    lowered = generated_prompt.casefold()
    assert "somente em json" in lowered
    assert "sem markdown" in lowered
    assert "sem texto extra" in lowered


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


@pytest.mark.parametrize(
    ("quadrant", "keyword"),
    [
        (quadrant, keyword)
        for quadrant, keywords in KEYWORDS_BY_QUADRANT.items()
        for keyword in keywords
    ],
)
def test_prompt_references_expanded_pt_br_keywords_by_quadrant(
    generated_prompt: str,
    quadrant: str,
    keyword: str,
) -> None:
    """Generated prompt should reference expanded PT-BR keyword lists by quadrant."""
    lowered = generated_prompt.casefold()
    assert quadrant in generated_prompt
    assert keyword in lowered


@pytest.mark.parametrize("quadrant, example_tasks", FEW_SHOT_TASKS_BY_QUADRANT.items())
def test_prompt_contains_two_few_shot_examples_for_each_quadrant(
    generated_prompt: str,
    quadrant: str,
    example_tasks: tuple[str, str],
) -> None:
    """Prompt should provide two few-shot JSON examples for every quadrant."""
    assert generated_prompt.count(f'"quadrant": "{quadrant}"') >= 2
    for example_task in example_tasks:
        assert example_task in generated_prompt


def test_prompt_instructs_low_confidence_for_ambiguous_tasks(generated_prompt: str) -> None:
    """Prompt should lower confidence below 0.6 when task context is ambiguous."""
    lowered = generated_prompt.casefold()
    assert "ambígu" in lowered
    assert "confidence" in lowered
    assert "< 0.6" in lowered or "menor que 0.6" in lowered
