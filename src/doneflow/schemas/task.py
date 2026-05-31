"""Pydantic schemas for task API payloads."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from doneflow.models.quadrant import Quadrant

TASK_CREATE_EXAMPLE: dict[str, Any] = {
    "description": "Preparar apresentação para reunião de amanhã às 9h",
}
TASK_UPDATE_EXAMPLE: dict[str, Any] = {
    "description": "Delegar revisão do relatório para o time",
    "quadrant": "DELEGATE",
}
TASK_RESPONSE_EXAMPLE: dict[str, Any] = {
    "id": "7cbd20f3-6f31-4c7f-ba6b-c7bb4be8a88a",
    "description": "Pagar conta de energia hoje",
    "quadrant": "DO_NOW",
    "ai_confidence": 0.94,
    "ai_reasoning": "Contém prazo imediato (hoje) e alta importância.",
    "created_at": "2026-05-25T12:00:00Z",
    "updated_at": "2026-05-25T12:00:00Z",
}
DISTRIBUTION_RESPONSE_EXAMPLE: dict[str, Any] = {
    "DO_NOW": 4,
    "SCHEDULE": 3,
    "DELEGATE": 2,
    "ELIMINATE": 1,
    "total": 10,
}


class TaskCreate(BaseModel):
    """Payload to create a task."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [TASK_CREATE_EXAMPLE]},
    )

    description: str = Field(
        min_length=5,
        max_length=500,
        description="Texto da tarefa que será classificado pela IA na Matriz de Eisenhower.",
        examples=[TASK_CREATE_EXAMPLE["description"]],
    )

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
        json_schema_extra={"examples": [TASK_UPDATE_EXAMPLE]},
    )

    description: str | None = Field(
        default=None,
        min_length=5,
        max_length=500,
        description="Novo texto opcional da tarefa. Quando enviado, é normalizado sem espaços extras.",
        examples=[TASK_UPDATE_EXAMPLE["description"]],
    )
    quadrant: Quadrant | None = Field(
        default=None,
        description="Quadrante manual para recategorizar a tarefa.",
        examples=[TASK_UPDATE_EXAMPLE["quadrant"]],
    )

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
    def validate_non_empty_update(self) -> TaskUpdate:
        """Ensure update payload has at least one field to update."""
        if self.description is None and self.quadrant is None:
            raise ValueError("at least one field must be provided")
        return self


class TaskResponse(BaseModel):
    """API response schema for a task resource."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [TASK_RESPONSE_EXAMPLE]},
    )

    id: UUID = Field(description="Identificador UUID da tarefa.")
    description: str = Field(description="Descrição normalizada da tarefa.")
    quadrant: Quadrant = Field(
        description="Quadrante Eisenhower atribuído pela IA ou pelo usuário."
    )
    ai_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confiança da classificação entre 0.0 e 1.0.",
    )
    ai_reasoning: str | None = Field(
        default=None,
        description="Justificativa resumida da classificação gerada pela IA ou fallback.",
    )
    created_at: datetime = Field(description="Data e hora de criação da tarefa em ISO 8601.")
    updated_at: datetime | None = Field(
        default=None,
        description="Data e hora da última atualização em ISO 8601, quando existir.",
    )


class DistributionResponse(BaseModel):
    """Distribution of tasks across quadrants."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"examples": [DISTRIBUTION_RESPONSE_EXAMPLE]},
    )

    DO_NOW: int = Field(ge=0, description="Quantidade de tarefas urgentes e importantes.")
    SCHEDULE: int = Field(ge=0, description="Quantidade de tarefas importantes e não urgentes.")
    DELEGATE: int = Field(ge=0, description="Quantidade de tarefas urgentes e não importantes.")
    ELIMINATE: int = Field(
        ge=0, description="Quantidade de tarefas não urgentes e não importantes."
    )
    total: int = Field(ge=0, description="Total de tarefas somando todos os quadrantes.")

    @model_validator(mode="after")
    def validate_total(self) -> DistributionResponse:
        """Ensure total equals the sum of quadrant counters."""
        computed_total = self.DO_NOW + self.SCHEDULE + self.DELEGATE + self.ELIMINATE
        if self.total != computed_total:
            raise ValueError("total must be equal to sum of quadrant counts")
        return self

    @classmethod
    def from_quadrant_counts(cls, counts: dict[Quadrant | str, int]) -> DistributionResponse:
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
