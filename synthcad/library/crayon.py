from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from build123d import Box, Color, Cylinder, Location, Sphere


Axis = Literal["x", "y", "z"]

CRAYON_FRAME = "#4b5563"
CRAYON_DRIVE = "#dc2626"
CRAYON_INTAKE = "#2563eb"
CRAYON_INDEXER = "#059669"
CRAYON_SHOOTER = "#f59e0b"
CRAYON_MOTOR = "#ca8a04"
CRAYON_SENSOR = "#7c3aed"
CRAYON_GAME_PIECE_PURPLE = "#7e22ce"
CRAYON_GAME_PIECE_GREEN = "#16a34a"
CRAYON_KEEP_OUT = "#e5e7eb"


@dataclass(frozen=True)
class CrayonIntent:
    """Refinement note for a low-detail planning part."""

    interfaces: tuple[str, ...] = ()
    refine_with: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "interfaces": self.interfaces,
            "refine_with": self.refine_with,
            "notes": self.notes,
        }


def _paint(shape, label: str, color: str, alpha: float = 1.0, intent: CrayonIntent | None = None):
    shape.label = label
    shape.color = Color(color, alpha)
    if intent is not None:
        shape.user_data = {"crayon_intent": intent.as_dict()}
    return shape


def _axis_rotation(axis: Axis) -> tuple[float, float, float]:
    if axis == "x":
        return (0, 90, 0)
    if axis == "y":
        return (90, 0, 0)
    return (0, 0, 0)


def crayon_box(
    label: str,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    color: str,
    *,
    alpha: float = 1.0,
    rotation: tuple[float, float, float] = (0, 0, 0),
    intent: CrayonIntent | None = None,
):
    shape = Location(center) * Box(*size, rotation=rotation)
    return _paint(shape, label, color, alpha, intent)


def crayon_cylinder(
    label: str,
    center: tuple[float, float, float],
    *,
    radius: float,
    length: float,
    axis: Axis,
    color: str,
    alpha: float = 1.0,
    intent: CrayonIntent | None = None,
):
    shape = Location(center) * Cylinder(radius, length, rotation=_axis_rotation(axis))
    return _paint(shape, label, color, alpha, intent)


def crayon_sphere(
    label: str,
    center: tuple[float, float, float],
    *,
    radius: float,
    color: str,
    alpha: float = 1.0,
    intent: CrayonIntent | None = None,
):
    shape = Location(center) * Sphere(radius)
    return _paint(shape, label, color, alpha, intent)
