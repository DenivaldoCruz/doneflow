"""Unit tests for Task model (TDD RED phase)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from doneflow.models.quadrant import Quadrant
from doneflow.models.task import Task


def test_task_creation_with_required_fields() -> None:
    """Task should be created with explicit required fields."""
    now = datetime.now(timezone.utc)
    task = Task(
        id="8f26ed6e-4ac2-4c49-bf4f-d233fce9f5fb",
        text="Preparar apresentação para o cliente",
        quadrant=Quadrant.DO_NOW,
        created_at=now,
    )

    assert str(task.id) == "8f26ed6e-4ac2-4c49-bf4f-d233fce9f5fb"
    assert task.text == "Preparar apresentação para o cliente"
    assert task.quadrant == Quadrant.DO_NOW
    assert task.created_at == now


@pytest.mark.parametrize("invalid_text", ["", "a", "abcd", "   "])
def test_task_rejects_empty_or_too_short_text(invalid_text: str) -> None:
    """Task should reject empty text or text with less than 5 characters."""
    with pytest.raises(ValidationError):
        Task(
            text=invalid_text,
            quadrant=Quadrant.SCHEDULE,
        )


def test_task_rejects_text_longer_than_500_characters() -> None:
    """Task should reject text with more than 500 characters."""
    with pytest.raises(ValidationError):
        Task(
            text="x" * 501,
            quadrant=Quadrant.DELEGATE,
        )


def test_task_generates_uuid_automatically_when_id_is_not_provided() -> None:
    """Task should generate UUID automatically when id is omitted."""
    task = Task(
        text="Agendar revisão semanal",
        quadrant=Quadrant.SCHEDULE,
    )

    assert isinstance(task.id, UUID)


def test_task_generates_created_at_automatically_when_not_provided() -> None:
    """Task should generate created_at automatically when omitted."""
    before = datetime.now(timezone.utc)
    task = Task(
        text="Delegar compilação de relatório",
        quadrant=Quadrant.DELEGATE,
    )
    after = datetime.now(timezone.utc)

    assert isinstance(task.created_at, datetime)
    assert before <= task.created_at <= after


def test_task_accepts_optional_ai_confidence_between_zero_and_one() -> None:
    """Task should accept optional ai_confidence within inclusive range [0.0, 1.0]."""
    low = Task(
        text="Responder e-mails não críticos",
        quadrant=Quadrant.ELIMINATE,
        ai_confidence=0.0,
    )
    high = Task(
        text="Responder e-mails não críticos",
        quadrant=Quadrant.ELIMINATE,
        ai_confidence=1.0,
    )

    assert low.ai_confidence == 0.0
    assert high.ai_confidence == 1.0


@pytest.mark.parametrize("invalid_confidence", [-0.01, 1.01])
def test_task_rejects_ai_confidence_out_of_range(invalid_confidence: float) -> None:
    """Task should reject ai_confidence values outside range [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        Task(
            text="Planejar sprint da próxima semana",
            quadrant=Quadrant.DO_NOW,
            ai_confidence=invalid_confidence,
        )


def test_task_accepts_optional_ai_reasoning() -> None:
    """Task should accept optional ai_reasoning field."""
    reasoning = "Possui prazo hoje e alto impacto no resultado do trimestre."
    task = Task(
        text="Finalizar proposta comercial",
        quadrant=Quadrant.DO_NOW,
        ai_reasoning=reasoning,
    )

    assert task.ai_reasoning == reasoning
