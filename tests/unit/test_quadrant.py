"""Unit tests for the Quadrant enum (TDD RED phase)."""

from __future__ import annotations

from enum import Enum
from importlib import import_module

import pytest

EXPECTED_MEMBERS = ("DO_NOW", "SCHEDULE", "DELEGATE", "ELIMINATE")
EXPECTED_PT_BR_LABELS = {
    "DO_NOW": "Fazer Agora",
    "SCHEDULE": "Agendar",
    "DELEGATE": "Delegar",
    "ELIMINATE": "Eliminar",
}
EXPECTED_COLORS = {
    "DO_NOW": "#C0392B",
    "SCHEDULE": "#2980B9",
    "DELEGATE": "#E6A817",
    "ELIMINATE": "#555555",
}


def _load_quadrant_enum() -> type[Enum] | None:
    """Load Quadrant enum if available, otherwise return None."""
    candidate_locations = (
        "doneflow.models.task:Quadrant",
        "doneflow.models.quadrant:Quadrant",
        "doneflow.models.enums:Quadrant",
    )

    for location in candidate_locations:
        module_name, symbol_name = location.split(":")
        try:
            module = import_module(module_name)
        except ImportError:
            continue

        quadrant = getattr(module, symbol_name, None)
        if quadrant is not None:
            return quadrant

    return None


@pytest.fixture
def quadrant_enum() -> type[Enum]:
    """Return Quadrant enum under test."""
    quadrant = _load_quadrant_enum()
    assert quadrant is not None, "Quadrant enum should exist in the models layer"
    return quadrant


@pytest.mark.parametrize("member_name", EXPECTED_MEMBERS)
def test_quadrant_enum_contains_all_valid_members(
    quadrant_enum: type[Enum],
    member_name: str,
) -> None:
    """Quadrant enum should expose all four Eisenhower members."""
    assert member_name in quadrant_enum.__members__


def test_quadrant_enum_rejects_invalid_value(quadrant_enum: type[Enum]) -> None:
    """Quadrant enum should reject invalid values."""
    with pytest.raises(ValueError):
        quadrant_enum("NOT_A_VALID_QUADRANT")


@pytest.mark.parametrize("member_name", EXPECTED_MEMBERS)
def test_quadrant_enum_converts_string_to_enum(
    quadrant_enum: type[Enum],
    member_name: str,
) -> None:
    """Quadrant enum should convert string values to enum members."""
    member = quadrant_enum(member_name)
    assert member.name == member_name


@pytest.mark.parametrize("member_name, expected_label", EXPECTED_PT_BR_LABELS.items())
def test_quadrant_enum_exposes_portuguese_representation(
    quadrant_enum: type[Enum],
    member_name: str,
    expected_label: str,
) -> None:
    """Quadrant enum should expose pt-BR label for each quadrant."""
    member = quadrant_enum[member_name]
    assert getattr(member, "label_pt", None) == expected_label


@pytest.mark.parametrize("member_name, expected_color", EXPECTED_COLORS.items())
def test_quadrant_enum_exposes_expected_hex_color_rf04(
    quadrant_enum: type[Enum],
    member_name: str,
    expected_color: str,
) -> None:
    """Quadrant enum should expose PRD RF-04 color mapping."""
    member = quadrant_enum[member_name]
    assert getattr(member, "hex_color", None) == expected_color


EXPECTED_DESCRIPTIONS = {
    "DO_NOW": "Urgente e importante.",
    "SCHEDULE": "Não urgente e importante.",
    "DELEGATE": "Urgente e não importante.",
    "ELIMINATE": "Não urgente e não importante.",
}


@pytest.mark.parametrize("member_name, expected_desc", EXPECTED_DESCRIPTIONS.items())
def test_quadrant_enum_exposes_description(
    quadrant_enum: type[Enum],
    member_name: str,
    expected_desc: str,
) -> None:
    """Quadrant enum should expose semantic descriptions for each quadrant."""
    member = quadrant_enum[member_name]
    assert getattr(member, "description", None) == expected_desc


def test_quadrant_from_string_case_insensitive(quadrant_enum: type[Enum]) -> None:
    """Quadrant.from_string should convert case-insensitive strings."""
    result = quadrant_enum.from_string("do_now")
    assert result == quadrant_enum.DO_NOW

    result = quadrant_enum.from_string("  SCHEDULE  ")
    assert result == quadrant_enum.SCHEDULE


def test_quadrant_from_string_rejects_non_string_type(quadrant_enum: type[Enum]) -> None:
    """Quadrant.from_string should raise TypeError for non-string input."""
    with pytest.raises(TypeError, match="value must be a string"):
        quadrant_enum.from_string(123)  # type: ignore


def test_quadrant_from_string_rejects_invalid_value(quadrant_enum: type[Enum]) -> None:
    """Quadrant.from_string should raise ValueError for invalid quadrant names."""
    with pytest.raises(ValueError, match="Invalid quadrant value"):
        quadrant_enum.from_string("INVALID_QUADRANT")


def test_quadrant_str_representation(quadrant_enum: type[Enum]) -> None:
    """Quadrant __str__ should return canonical value representation."""
    member = quadrant_enum.DO_NOW
    assert str(member) == "DO_NOW"

    member = quadrant_enum.SCHEDULE
    assert str(member) == "SCHEDULE"
