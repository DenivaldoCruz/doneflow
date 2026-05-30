"""Unit tests for AICategorizationService (TDD RED phase)."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock

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


def test_parse_response_rejects_non_object_payload(ai_service_class: type) -> None:
    """JSON arrays should be rejected and handled by classify_task fallback."""
    service = ai_service_class()

    with pytest.raises(ValueError, match="Response must be an object"):
        service._parse_response('["DO_NOW"]')


def test_parse_response_rejects_out_of_range_confidence(ai_service_class: type) -> None:
    """Confidence values outside the normalized range should be rejected."""
    service = ai_service_class()

    with pytest.raises(ValueError, match="Confidence out of range"):
        service._parse_response('{"quadrant":"DO_NOW","confidence":1.5}')


def test_parse_response_rejects_unknown_quadrant(ai_service_class: type) -> None:
    """Unknown quadrant values should be rejected before persistence."""
    service = ai_service_class()

    with pytest.raises(ValueError, match="Invalid quadrant value"):
        service._parse_response('{"quadrant":"PARK","confidence":0.5}')


def test_fallback_classifies_urgent_unimportant_tasks_as_delegate(ai_service_class: type) -> None:
    """Urgent but not strategic fallback tasks should map to DELEGATE."""
    service = ai_service_class()

    result = service._fallback_classification("Responder email urgente agora")

    assert result == {"quadrant": Quadrant.DELEGATE, "confidence": 0.5}


def test_fallback_classifies_important_nonurgent_tasks_as_schedule(ai_service_class: type) -> None:
    """Strategic fallback tasks without urgency should map to SCHEDULE."""
    service = ai_service_class()

    result = service._fallback_classification("Definir estratégia de produto")

    assert result == {"quadrant": Quadrant.SCHEDULE, "confidence": 0.5}


def test_fallback_classifies_urgent_important_tasks_as_do_now(ai_service_class: type) -> None:
    """Fallback should preserve both urgency and importance when both are present."""
    service = ai_service_class()

    result = service._fallback_classification("Reunião urgente com CEO hoje")

    assert result == {"quadrant": Quadrant.DO_NOW, "confidence": 0.5}


def test_call_anthropic_api_sends_structured_prompt_and_returns_text(
    ai_service_class: type,
) -> None:
    """Anthropic calls should include model settings, timeout, and structured prompt text."""

    class FakeContent:
        text = '{"quadrant":"SCHEDULE","confidence":0.8}'

    class FakeMessage:
        content = [FakeContent()]

    service = ai_service_class()
    service._client = MagicMock()
    service._client.messages.create = AsyncMock(return_value=FakeMessage())

    result = asyncio.run(service._call_anthropic_api("Planejar roadmap de produto"))

    assert result == '{"quadrant":"SCHEDULE","confidence":0.8}'
    service._client.messages.create.assert_awaited_once()
    call_kwargs = service._client.messages.create.await_args.kwargs
    assert call_kwargs["model"] == "claude-sonnet-4-20250514"
    assert call_kwargs["timeout"] == service._timeout_seconds
    assert call_kwargs["messages"][0]["role"] == "user"
    assert "Planejar roadmap de produto" in call_kwargs["messages"][0]["content"]


def test_call_anthropic_api_rejects_empty_text(ai_service_class: type) -> None:
    """Empty Anthropic content should be treated as an invalid provider response."""

    class FakeContent:
        text = "   "

    class FakeMessage:
        content = [FakeContent()]

    service = ai_service_class()
    service._client = MagicMock()
    service._client.messages.create = AsyncMock(return_value=FakeMessage())

    with pytest.raises(ValueError, match="Empty model response"):
        asyncio.run(service._call_anthropic_api("Comprar café"))


def test_init_uses_environment_timeout_when_settings_loading_fails(
    ai_service_class: type,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings failures should fall back to the AI_TIMEOUT_SECONDS environment value."""
    module = import_module("doneflow.services.ai_categorization_service")

    def raise_settings_error() -> None:
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr(module, "get_settings", raise_settings_error)
    monkeypatch.setenv("AI_TIMEOUT_SECONDS", "1.25")

    service = ai_service_class()

    assert service._timeout_seconds == pytest.approx(1.25)


def test_init_keeps_default_timeout_when_settings_and_env_timeout_are_unavailable(
    ai_service_class: type,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Settings failures without an env override should keep the deterministic default timeout."""
    module = import_module("doneflow.services.ai_categorization_service")

    def raise_settings_error() -> None:
        raise RuntimeError("settings unavailable")

    monkeypatch.setattr(module, "get_settings", raise_settings_error)
    monkeypatch.delenv("AI_TIMEOUT_SECONDS", raising=False)

    service = ai_service_class()

    assert service._timeout_seconds == pytest.approx(2.0)


@pytest.mark.asyncio
async def test_invalid_quadrant_response_falls_back_to_keyword_classification(
    ai_service_class: type,
) -> None:
    """Unknown provider quadrants should trigger deterministic fallback classification."""
    service = ai_service_class()
    service._call_anthropic_api = AsyncMock(return_value='{"quadrant":"PARK","confidence":0.9}')

    result = await service.classify_task("Resolver entrega urgente para cliente hoje")

    assert result == {"quadrant": Quadrant.DELEGATE, "confidence": 0.5}


def test_parse_response_defaults_missing_confidence_to_half(ai_service_class: type) -> None:
    """Provider payloads may omit confidence and should default to 0.5."""
    service = ai_service_class()

    result = service._parse_response('{"quadrant":"SCHEDULE"}')

    assert result == {"quadrant": Quadrant.SCHEDULE, "confidence": 0.5}


def test_parse_response_coerces_string_confidence(ai_service_class: type) -> None:
    """String confidence values from JSON should be coerced into floats when valid."""
    service = ai_service_class()

    result = service._parse_response('{"quadrant":"DELEGATE","confidence":"0.72"}')

    assert result == {"quadrant": Quadrant.DELEGATE, "confidence": 0.72}


def test_call_anthropic_api_rejects_non_string_text(ai_service_class: type) -> None:
    """Anthropic content with non-string text should be rejected as an empty response."""

    class FakeContent:
        text = None

    class FakeMessage:
        content = [FakeContent()]

    service = ai_service_class()
    service._client = MagicMock()
    service._client.messages.create = AsyncMock(return_value=FakeMessage())

    with pytest.raises(ValueError, match="Empty model response"):
        asyncio.run(service._call_anthropic_api("Comprar café"))
