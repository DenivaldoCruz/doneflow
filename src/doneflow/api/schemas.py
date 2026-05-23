"""Pydantic v2 schemas for the DoneFlow API.

Only the CreateTaskSchema required by RF-01 is implemented here.
"""

from pydantic import BaseModel, Field, field_validator


class CreateTaskSchema(BaseModel):
    """Schema used when creating a new Task.

    Attributes:
        description: Free-text description of the task. Must be at least
            5 characters long and non-empty.
    """

    description: str = Field(..., description="Task description (min 5 chars)")

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not empty and has at least 5 characters.

        Trims whitespace and enforces minimum length as specified in RF-01.
        """
        if v is None:
            raise ValueError("description is required")
        text = v.strip()
        if not text:
            raise ValueError("description must not be empty")
        if len(text) < 5:
            raise ValueError("description must be at least 5 characters long")
        return text

