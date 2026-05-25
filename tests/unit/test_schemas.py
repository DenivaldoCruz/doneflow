"""Unit tests for Pydantic task schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from doneflow.models.quadrant import Quadrant
from doneflow.schemas.task import DistributionResponse, TaskCreate, TaskResponse, TaskUpdate


@pytest.mark.unit
def test_task_create_trims_description_when_valid() -> None:
    schema = TaskCreate(description="  Preparar demo para o cliente  ")
    assert schema.description == "Preparar demo para o cliente"


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


@pytest.mark.unit
def test_task_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate()


@pytest.mark.unit
def test_task_update_accepts_quadrant_only() -> None:
    schema = TaskUpdate(quadrant=Quadrant.SCHEDULE)
    assert schema.quadrant == Quadrant.SCHEDULE


@pytest.mark.unit
def test_task_response_supports_from_attributes() -> None:
    class Obj:
        id = uuid4()
        description = "Executar tarefa urgente"
        quadrant = Quadrant.DO_NOW
        ai_confidence = 0.9
        ai_reasoning = "Urgente e importante"
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)

    schema = TaskResponse.model_validate(Obj())
    assert schema.description == "Executar tarefa urgente"


@pytest.mark.unit
def test_distribution_response_requires_total_consistency() -> None:
    with pytest.raises(ValidationError):
        DistributionResponse(DO_NOW=1, SCHEDULE=2, DELEGATE=3, ELIMINATE=4, total=9)


@pytest.mark.unit
def test_distribution_response_from_quadrant_counts_builds_total() -> None:
    schema = DistributionResponse.from_quadrant_counts(
        {
            Quadrant.DO_NOW: 1,
            "schedule": 2,
            "DELEGATE": 3,
            "eliminate": 4,
        }
    )
    assert schema.total == 10


def test_task_update_trims_description_when_provided() -> None:
    """TaskUpdate should trim whitespace from description."""
    update = TaskUpdate(description="  Updated task  ")
    assert update.description == "Updated task"


def test_task_update_rejects_empty_trimmed_description() -> None:
    """TaskUpdate should reject description that becomes empty after trim."""
    with pytest.raises(ValidationError):
        TaskUpdate(description="    ")


def test_task_update_rejects_too_short_description() -> None:
    """TaskUpdate should reject description shorter than 5 chars."""
    with pytest.raises(ValidationError):
        TaskUpdate(description="1234")  # 4 chars, below minimum of 5


def test_task_update_rejects_too_long_description() -> None:
    """TaskUpdate should reject description longer than 500 chars."""
    with pytest.raises(ValidationError):
        TaskUpdate(description="x" * 501)


def test_task_update_allows_description_with_quadrant() -> None:
    """TaskUpdate should allow providing both description and quadrant."""
    update = TaskUpdate(
        description="New description for task",
        quadrant=Quadrant.DO_NOW,
    )
    assert update.description == "New description for task"
    assert update.quadrant == Quadrant.DO_NOW


def test_distribution_response_handles_all_valid_quadrant_keys() -> None:
    """DistributionResponse.from_quadrant_counts should handle various key formats."""
    schema = DistributionResponse.from_quadrant_counts(
        {
            "DO_NOW": 1,
            "SCHEDULE": 2,
            Quadrant.DELEGATE: 3,
            "eliminate": 4,
        }
    )
    assert schema.DO_NOW == 1
    assert schema.SCHEDULE == 2
    assert schema.DELEGATE == 3
    assert schema.ELIMINATE == 4
    assert schema.total == 10


def test_distribution_response_ignores_unknown_keys() -> None:
    """DistributionResponse.from_quadrant_counts should ignore unknown quadrant keys."""
    schema = DistributionResponse.from_quadrant_counts(
        {
            "DO_NOW": 1,
            "UNKNOWN_KEY": 999,  # Should be ignored
        }
    )
    assert schema.DO_NOW == 1
    assert schema.SCHEDULE == 0
    assert schema.DELEGATE == 0
    assert schema.ELIMINATE == 0
    assert schema.total == 1


