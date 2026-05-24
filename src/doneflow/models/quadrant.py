"""Eisenhower Matrix quadrant enum definitions."""

from __future__ import annotations

from enum import Enum


class Quadrant(str, Enum):
    """Representa os quadrantes da Matriz de Eisenhower.

    Cada membro identifica a combinação entre urgência e importância
    usada para classificar tarefas no DoneFlow.

    Attributes:
        DO_NOW: Urgente e importante.
        SCHEDULE: Não urgente e importante.
        DELEGATE: Urgente e não importante.
        ELIMINATE: Não urgente e não importante.
    """

    DO_NOW = "DO_NOW"
    SCHEDULE = "SCHEDULE"
    DELEGATE = "DELEGATE"
    ELIMINATE = "ELIMINATE"

    @property
    def label(self) -> str:
        """Retorna o rótulo amigável em português (pt-BR)."""
        labels: dict[Quadrant, str] = {
            Quadrant.DO_NOW: "Fazer Agora",
            Quadrant.SCHEDULE: "Agendar",
            Quadrant.DELEGATE: "Delegar",
            Quadrant.ELIMINATE: "Eliminar",
        }
        return labels[self]

    @property
    def label_pt(self) -> str:
        """Retorna alias compatível para rótulo pt-BR."""
        return self.label

    @property
    def color(self) -> str:
        """Retorna a cor hexadecimal associada ao quadrante."""
        colors: dict[Quadrant, str] = {
            Quadrant.DO_NOW: "#C0392B",
            Quadrant.SCHEDULE: "#2980B9",
            Quadrant.DELEGATE: "#E6A817",
            Quadrant.ELIMINATE: "#555555",
        }
        return colors[self]

    @property
    def hex_color(self) -> str:
        """Retorna alias compatível para cor hexadecimal."""
        return self.color

    @property
    def description(self) -> str:
        """Retorna a descrição textual da semântica do quadrante."""
        descriptions: dict[Quadrant, str] = {
            Quadrant.DO_NOW: "Urgente e importante.",
            Quadrant.SCHEDULE: "Não urgente e importante.",
            Quadrant.DELEGATE: "Urgente e não importante.",
            Quadrant.ELIMINATE: "Não urgente e não importante.",
        }
        return descriptions[self]

    @classmethod
    def from_string(cls, value: str) -> Quadrant:
        """Converte string para ``Quadrant`` de forma tolerante a maiúsculas.

        Args:
            value: Texto com o nome/valor do quadrante.

        Returns:
            Membro correspondente de ``Quadrant``.

        Raises:
            ValueError: Quando o texto não corresponde a nenhum quadrante.
            TypeError: Quando ``value`` não for string.
        """
        if not isinstance(value, str):
            raise TypeError("value must be a string")

        normalized = value.strip().upper()

        try:
            return cls[normalized]
        except KeyError:
            try:
                return cls(normalized)
            except ValueError as exc:
                raise ValueError(f"Invalid quadrant value: {value}") from exc

    def __str__(self) -> str:
        """Retorna a representação textual canônica do quadrante."""
        return self.value
