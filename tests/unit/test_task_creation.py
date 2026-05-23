"""Unit tests for task creation (RF-01) - TDD: Red first.

These tests assert the Pydantic schema validation rules and minimal
behaviour of the ORM model required for task creation.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError


from src.doneflow.api.schemas import CreateTaskSchema
from src.doneflow.models.task import Task


def test_task_schema_without_description_raises_validation_error() -> None:
    """test_task_schema_without_description_raises_validation_error

    A CreateTaskSchema instantiation without the required `description`
    field must raise a ValidationError.
    """

    with pytest.raises(ValidationError):
        # missing required field
        CreateTaskSchema()


def test_task_schema_with_short_description_raises_validation_error() -> None:
    """test_task_schema_with_short_description_raises_validation_error

    Description shorter than 5 characters must be rejected by the schema.
    """

    with pytest.raises(ValidationError):
        CreateTaskSchema(description="abc")  # length 3


def test_task_model_with_valid_description_sets_fields_correctly() -> None:
    """test_task_model_with_valid_description_sets_fields_correctly

    Creating a Task ORM instance with a valid description should set
    the description attribute and initialize `created_at` to a
    datetime value.
    """

    description = "Buy groceries for dinner"
    task = Task(description=description)

    assert task.description == description
    assert hasattr(task, "created_at")
    assert isinstance(task.created_at, datetime)

