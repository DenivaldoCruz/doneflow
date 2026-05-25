"""Task domain model definitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from doneflow.models.quadrant import Quadrant


class Task(BaseModel):
    """Represent a task classified with the Eisenhower Matrix.

    Attributes:
        id: Unique task identifier generated automatically.
        description: Human-readable task description.
        quadrant: Eisenhower quadrant for prioritization.
        ai_confidence: Confidence score for AI-based categorization.
        created_at: UTC creation timestamp generated automatically.
        updated_at: UTC timestamp for the latest model update.
    """

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    id: UUID = Field(default_factory=uuid4)
    description: str
    quadrant: Quadrant = Field(default=Quadrant.DO_NOW)
    ai_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ai_reasoning: str | None = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """Validate and normalize a task description.

        Args:
            value: Raw task description.

        Returns:
            Normalized description text without leading/trailing spaces.

        Raises:
            TypeError: If ``value`` is not a string.
            ValueError: If normalized description is empty.
        """
        if not isinstance(value, str):
            raise TypeError("description must be a string")

        normalized = value.strip()
        if not normalized:
            raise ValueError("description must not be empty")

        if len(value.strip()) < 5:
            raise ValueError("description too short")

        if len(value.strip()) > 500:
            raise ValueError("description too long")

        return normalized

    @field_validator("created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware_datetime(cls, value: datetime) -> datetime:
        """Ensure datetime values are timezone-aware in UTC.

        Args:
            value: Datetime value to validate.

        Returns:
            Timezone-aware datetime converted to UTC when needed.

        Raises:
            ValueError: If datetime is naive (timezone-unaware).
        """
        if value.tzinfo is None:
            raise ValueError("datetime values must include timezone information")
        return value.astimezone(UTC)
