"""AI categorization service using Anthropic async client."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic

from doneflow.config import get_settings
from doneflow.models.quadrant import Quadrant
from doneflow.services.prompt_builder import PromptBuilder

LOGGER = logging.getLogger(__name__)


class AICategorizationService:
    """Categorize tasks into Eisenhower quadrants using Anthropic Claude.

    This service attempts a remote AI classification first and falls back to a
    deterministic local heuristic when the remote call fails.
    """

    def __init__(self) -> None:
        """Initialize service dependencies and configuration."""
        self._model: str = "claude-sonnet-4-20250514"
        self._timeout_seconds: float = 2.0
        self._prompt_builder = PromptBuilder()

        api_key = os.getenv("ANTHROPIC_API_KEY", "test-key")
        try:
            settings = get_settings()
            self._timeout_seconds = settings.AI_TIMEOUT_SECONDS
            api_key = settings.ANTHROPIC_API_KEY
        except Exception:  # noqa: BLE001
            timeout_env = os.getenv("AI_TIMEOUT_SECONDS")
            if timeout_env:
                self._timeout_seconds = float(timeout_env)

        self._client = AsyncAnthropic(api_key=api_key)

    async def classify_task(self, task_description: str) -> dict[str, Any]:
        """Classify a task and return quadrant + confidence payload.

        Args:
            task_description: Task description to classify.

        Returns:
            A dict containing ``quadrant`` and ``confidence`` keys.
        """
        try:
            response_text = await self._call_anthropic_api(task_description)
            parsed = self._parse_response(response_text)
            return {
                "quadrant": parsed["quadrant"],
                "confidence": parsed["confidence"],
            }
        except TimeoutError:
            raise
        except Exception as exc:  # noqa: BLE001
            LOGGER.error(
                "AI categorization failed, applying fallback classification: %s", type(exc).__name__
            )
            return self._fallback_classification(task_description)

    async def _call_anthropic_api(self, task_description: str) -> str:
        """Call Anthropic API and return the raw model text output.

        Args:
            task_description: Task description used to build the model prompt.

        Returns:
            JSON payload as plain text returned by the model.
        """
        prompt = self._prompt_builder.build(task_description)
        message = await self._client.messages.create(
            model=self._model,
            max_tokens=200,
            temperature=0,
            timeout=self._timeout_seconds,
            messages=[{"role": "user", "content": prompt}],
        )

        content = message.content[0]
        text = getattr(content, "text", "")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Empty model response")

        return text

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """Parse and validate JSON response from model.

        Args:
            response_text: Raw text that should represent JSON.

        Returns:
            Normalized payload containing quadrant enum and confidence float.

        Raises:
            ValueError: If payload is invalid or missing required fields.
        """
        payload = json.loads(response_text)
        if not isinstance(payload, dict):
            raise ValueError("Response must be an object")

        if "quadrant" not in payload or "confidence" not in payload:
            raise ValueError("Missing required response fields")

        quadrant = Quadrant.from_string(str(payload["quadrant"]))
        confidence = float(payload["confidence"])
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence out of range")

        return {"quadrant": quadrant, "confidence": confidence}

    def _fallback_classification(self, task_description: str) -> dict[str, Any]:
        """Return deterministic fallback categorization based on keywords.

        Args:
            task_description: Task description to categorize.

        Returns:
            Fallback payload with deterministic quadrant and confidence.
        """
        text = task_description.lower()
        urgency_keywords = ("hoje", "urgente", "agora", "deadline", "prazo", "cliente", "entrega")
        importance_keywords = ("roadmap", "produto", "estratég", "proposta", "reuni", "ceo")

        is_urgent = any(keyword in text for keyword in urgency_keywords)
        is_important = any(keyword in text for keyword in importance_keywords)

        if is_urgent and is_important:
            quadrant = Quadrant.DO_NOW
        elif is_important:
            quadrant = Quadrant.SCHEDULE
        elif is_urgent:
            quadrant = Quadrant.DELEGATE
        else:
            quadrant = Quadrant.ELIMINATE

        return {"quadrant": quadrant, "confidence": 0.5}
