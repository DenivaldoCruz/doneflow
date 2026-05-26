"""Unit tests for AICategorizationService (TDD RED phase)."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock

import pytest

from doneflow.models.quadrant import Quadrant


@pytest.fixture
def ai_service_class() -> type:
    """Return AICategorizationService class from known module locations."""
    candidate_locations = (
        "doneflow.services.ai_categorization_service:AICategorizationService",
        "doneflow.services.ai_categorization:AICategorizationService",
        "doneflow.services.ai.service:AICategorizationService",
    )

    for location in candidate_locations:
        module_name, symbol_name = location.split(":")
        try:
            module = import_module(module_name)
        except ImportError:
            continue

        ai_service = getattr(module, symbol_name, None)
        if ai_service is not None:
            return ai_service

    pytest.fail("AICategorizationService deve existir na camada de serviços")


@pytest.mark.asyncio
async def test_task_with_urgent_keyword_classified_as_do_now(ai_service_class: type) -> None:
    """Tasks with urgency keywords should map to DO_NOW when important context is present."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(
        return_value='{"quadrant":"DO_NOW","confidence":0.94,"reasoning":"urgente e crítico"}'
    )

    result = await service.classify_task("Entregar proposta urgente para cliente hoje")

    assert result["quadrant"] == Quadrant.DO_NOW


@pytest.mark.asyncio
async def test_task_with_strategic_keyword_classified_as_schedule(ai_service_class: type) -> None:
    """Strategic-but-not-urgent tasks should map to SCHEDULE."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(
        return_value='{"quadrant":"SCHEDULE","confidence":0.87,"reasoning":"tema estratégico"}'
    )

    result = await service.classify_task("Definir roadmap de produto para próximo trimestre")

    assert result["quadrant"] == Quadrant.SCHEDULE


@pytest.mark.asyncio
async def test_low_priority_task_classified_as_eliminate(ai_service_class: type) -> None:
    """Low urgency and low importance tasks should map to ELIMINATE."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(
        return_value='{"quadrant":"ELIMINATE","confidence":0.81,"reasoning":"baixo impacto"}'
    )

    result = await service.classify_task("Organizar figurinhas antigas sem prazo")

    assert result["quadrant"] == Quadrant.ELIMINATE


@pytest.mark.asyncio
async def test_ai_service_fallback_on_timeout(ai_service_class: type) -> None:
    """Timeouts from AI provider should raise TimeoutError."""

    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(side_effect=TimeoutError("anthropic timeout"))

    with pytest.raises(TimeoutError, match="anthropic timeout"):
        await service.classify_task("Fazer backup de fotos pessoais sem prazo")


@pytest.mark.asyncio
async def test_categorization_respects_both_dimensions(ai_service_class: type) -> None:
    """Classification must respect urgency and importance dimensions together."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(
        return_value='{"quadrant":"DELEGATE","confidence":0.76,"reasoning":"urgente mas pouco estratégico"}'
    )

    result = await service.classify_task("Responder solicitação urgente de rotina administrativa")

    assert result["quadrant"] == Quadrant.DELEGATE


@pytest.mark.asyncio
async def test_invalid_api_response_returns_fallback(ai_service_class: type) -> None:
    """Unexpected API payload shape should trigger fallback result."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(return_value='{"category":"DO_NOW"}')

    result = await service.classify_task("Planejar viagem futura")

    assert result["quadrant"] == Quadrant.ELIMINATE


@pytest.mark.asyncio
async def test_malformed_json_returns_fallback(ai_service_class: type) -> None:
    """Malformed JSON from provider should trigger fallback without crashing."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(return_value='{"quadrant": "DO_NOW"')

    result = await service.classify_task("Comprar café")

    assert result["quadrant"] == Quadrant.ELIMINATE


@pytest.mark.asyncio
async def test_confidence_is_float_between_zero_and_one(ai_service_class: type) -> None:
    """Classifier output confidence should be float normalized to [0, 1]."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(
        return_value='{"quadrant":"DO_NOW","confidence":0.61,"reasoning":"urgência e impacto"}'
    )

    result: dict[str, Any] = await service.classify_task("Entregar relatório para CEO hoje")

    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0
