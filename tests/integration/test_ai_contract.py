"""Integration contract tests for DoneFlow's Anthropic API usage."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from doneflow.models.quadrant import Quadrant
from doneflow.services.ai_categorization_service import AICategorizationService


class FakeAnthropicContent:
    """Minimal Anthropic content block with text output."""

    def __init__(self, text: str) -> None:
        """Store the provider text output."""
        self.text = text


class FakeAnthropicMessage:
    """Minimal Anthropic message response used by contract tests."""

    def __init__(self, text: str) -> None:
        """Build a message response with a single text content block."""
        self.content = [FakeAnthropicContent(text)]


@pytest.fixture
def ai_contract_service() -> AICategorizationService:
    """Return an AI service with a mocked Anthropic messages endpoint."""
    service = AICategorizationService()
    service._timeout_seconds = 2.0
    service._client = MagicMock()
    service._client.messages.create = AsyncMock(
        return_value=FakeAnthropicMessage(
            '{"quadrant":"SCHEDULE","confidence":0.86,"reasoning":"planejamento estratégico"}'
        )
    )
    return service


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_prompt_contains_required_contract_fields(
    ai_contract_service: AICategorizationService,
) -> None:
    """Prompt sent to Anthropic should include task text, JSON instruction, and quadrants."""
    task_text = "Planejar roadmap de produto para o próximo trimestre"

    await ai_contract_service._call_anthropic_api(task_text)

    call_kwargs: dict[str, Any] = ai_contract_service._client.messages.create.await_args.kwargs
    prompt = call_kwargs["messages"][0]["content"]

    assert task_text in prompt
    assert "JSON" in prompt
    assert "DO_NOW" in prompt
    assert "SCHEDULE" in prompt
    assert "DELEGATE" in prompt
    assert "ELIMINATE" in prompt


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_call_uses_expected_model_token_limit_and_timeout(
    ai_contract_service: AICategorizationService,
) -> None:
    """Anthropic call should pin model and send bounded generation settings."""
    await ai_contract_service._call_anthropic_api("Preparar reunião com CEO")

    call_kwargs: dict[str, Any] = ai_contract_service._client.messages.create.await_args.kwargs

    assert call_kwargs["model"] == "claude-sonnet-4-20250514"
    assert call_kwargs["max_tokens"] > 0
    assert call_kwargs["timeout"] == 2.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_invalid_quadrant_response_uses_fallback(
    ai_contract_service: AICategorizationService,
) -> None:
    """Invalid provider quadrants should not leak past the service contract."""
    ai_contract_service._client.messages.create = AsyncMock(
        return_value=FakeAnthropicMessage(
            '{"quadrant":"LATER","confidence":0.91,"reasoning":"valor fora do contrato"}'
        )
    )

    result = await ai_contract_service.classify_task("Arquivar memes antigos sem data definida")

    assert result == {"quadrant": Quadrant.ELIMINATE, "confidence": 0.5}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_anthropic_response_without_confidence_defaults_to_half(
    ai_contract_service: AICategorizationService,
) -> None:
    """Provider responses without confidence should preserve quadrant and default to 0.5."""
    ai_contract_service._client.messages.create = AsyncMock(
        return_value=FakeAnthropicMessage(
            '{"quadrant":"SCHEDULE","reasoning":"importante mas não urgente"}'
        )
    )

    result = await ai_contract_service.classify_task("Responder email urgente agora")

    assert result == {"quadrant": Quadrant.SCHEDULE, "confidence": 0.5}
