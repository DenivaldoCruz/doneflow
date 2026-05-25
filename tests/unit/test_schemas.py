"""Unit tests for API schemas (TDD RED phase)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from doneflow.api.schemas import (
    DistributionResponse,
    QuadrantDistribution,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from doneflow.models.quadrant import Quadrant


def test_task_create_accepts_valid_description() -> None:
    """TaskCreate should accept valid description between 5 and 500 characters."""
    schema = TaskCreate(description="Preparar relatório mensal para diretoria")

    assert schema.description == "Preparar relatório mensal para diretoria"


@pytest.mark.parametrize("invalid_description", ["", " ", "abcd"])
def test_task_create_rejects_empty_or_too_short_description(invalid_description: str) -> None:
    """TaskCreate should reject empty description and description shorter than 5 chars."""
    with pytest.raises(ValidationError):
        TaskCreate(description=invalid_description)


def test_task_create_rejects_description_longer_than_500_characters() -> None:
    """TaskCreate should reject description larger than 500 chars."""
    with pytest.raises(ValidationError):
        TaskCreate(description="x" * 501)


def test_task_response_contains_expected_fields() -> None:
    """TaskResponse should include task identity and AI metadata fields."""
    created_at = datetime(2026, 5, 25, 12, 0, 0, tzinfo=UTC)

    response = TaskResponse(
        id="e0185fe7-4f3d-4f14-932d-336dd410665f",
        description="Alinhar planejamento trimestral",
        quadrant=Quadrant.SCHEDULE,
        created_at=created_at,
        ai_confidence=0.92,
        ai_reasoning="Importante para metas trimestrais, sem urgência imediata.",
    )

    assert str(response.id) == "e0185fe7-4f3d-4f14-932d-336dd410665f"
    assert response.description == "Alinhar planejamento trimestral"
    assert response.quadrant == Quadrant.SCHEDULE
    assert response.created_at == created_at
    assert response.ai_confidence == pytest.approx(0.92)
    assert response.ai_reasoning == "Importante para metas trimestrais, sem urgência imediata."


def test_task_update_allows_manual_quadrant_change() -> None:
    """TaskUpdate should allow manual quadrant updates."""
    update = TaskUpdate(quadrant=Quadrant.DELEGATE)

    assert update.quadrant == Quadrant.DELEGATE


def test_distribution_response_contains_count_and_percentage_by_quadrant() -> None:
    """DistributionResponse should expose count and percentage per quadrant."""
    distribution = DistributionResponse(
        quadrants={
            Quadrant.DO_NOW: QuadrantDistribution(count=4, percentage=40.0),
            Quadrant.SCHEDULE: QuadrantDistribution(count=3, percentage=30.0),
            Quadrant.DELEGATE: QuadrantDistribution(count=2, percentage=20.0),
            Quadrant.ELIMINATE: QuadrantDistribution(count=1, percentage=10.0),
        },
        total_tasks=10,
    )

    assert distribution.total_tasks == 10
    assert distribution.quadrants[Quadrant.DO_NOW].count == 4
    assert distribution.quadrants[Quadrant.SCHEDULE].percentage == pytest.approx(30.0)
    assert distribution.quadrants[Quadrant.DELEGATE].count == 2
    assert distribution.quadrants[Quadrant.ELIMINATE].percentage == pytest.approx(10.0)
