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
