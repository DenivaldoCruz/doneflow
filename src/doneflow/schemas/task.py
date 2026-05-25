"""Pydantic schemas for task API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from doneflow.models.quadrant import Quadrant


class TaskCreate(BaseModel):
    """Payload to create a task."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "description": "Preparar apresentação para reunião de amanhã às 9h",
                }
            ]
        },
    )

    description: str = Field(min_length=5, max_length=500)

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """Validate and normalize task description."""
        normalized = value.strip()
        if not normalized:
            raise ValueError("description must not be empty")
        return normalized


class TaskUpdate(BaseModel):
    """Payload to manually update task attributes."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "description": "Delegar revisão do relatório para o time",
                    "quadrant": "DELEGATE",
                }
            ]
        },
    )

    description: str | None = Field(default=None, min_length=5, max_length=500)
    quadrant: Quadrant | None = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None) -> str | None:
        """Validate and normalize optional task description."""
        if value is None:
            return value

        normalized = value.strip()
        if not normalized:
            raise ValueError("description must not be empty")
        return normalized

    @model_validator(mode="after")
    def validate_non_empty_update(self) -> "TaskUpdate":
        """Ensure update payload has at least one field to update."""
        if self.description is None and self.quadrant is None:
            raise ValueError("at least one field must be provided")
        return self


class TaskResponse(BaseModel):
    """API response schema for a task resource."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": "7cbd20f3-6f31-4c7f-ba6b-c7bb4be8a88a",
                    "description": "Pagar conta de energia hoje",
                    "quadrant": "DO_NOW",
                    "ai_confidence": 0.94,
                    "ai_reasoning": "Contém prazo imediato (hoje) e alta importância.",
                    "created_at": "2026-05-25T12:00:00Z",
                    "updated_at": "2026-05-25T12:00:00Z",
                }
            ]
        },
    )

    id: UUID
    description: str
    quadrant: Quadrant
    ai_confidence: float = Field(ge=0.0, le=1.0)
    ai_reasoning: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DistributionResponse(BaseModel):
    """Distribution of tasks across quadrants."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "DO_NOW": 4,
                    "SCHEDULE": 3,
                    "DELEGATE": 2,
                    "ELIMINATE": 1,
                    "total": 10,
                }
            ]
        },
    )

    DO_NOW: int = Field(ge=0)
    SCHEDULE: int = Field(ge=0)
    DELEGATE: int = Field(ge=0)
    ELIMINATE: int = Field(ge=0)
    total: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_total(self) -> "DistributionResponse":
        """Ensure total equals the sum of quadrant counters."""
        computed_total = self.DO_NOW + self.SCHEDULE + self.DELEGATE + self.ELIMINATE
        if self.total != computed_total:
            raise ValueError("total must be equal to sum of quadrant counts")
        return self

    @classmethod
    def from_quadrant_counts(cls, counts: dict[Quadrant | str, int]) -> "DistributionResponse":
        """Build distribution schema from a generic count mapping."""
        normalized: dict[str, int] = {quadrant.value: 0 for quadrant in Quadrant}

        for raw_key, raw_value in counts.items():
            key = raw_key.value if isinstance(raw_key, Quadrant) else str(raw_key).strip().upper()
            if key in normalized:
                normalized[key] = raw_value

        payload: dict[str, Any] = {
            **normalized,
            "total": sum(normalized.values()),
        }
        return cls(**payload)
