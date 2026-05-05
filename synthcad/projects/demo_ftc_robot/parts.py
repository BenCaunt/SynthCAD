from __future__ import annotations

from typing import Literal

from build123d import Color, Compound

from synthcad.library.crayon import (
    Axis,
    CRAYON_MOTOR,
    CrayonIntent,
    crayon_cylinder,
)


ShaftDirection = Literal[-1, 1]

# Project-owned Yellow Jacket envelope. This is intentionally a low-resolution
# FTC concept proxy, not a reusable vendor CAD model.
YELLOWJACKET_BODY_LENGTH_MM = 58.0
YELLOWJACKET_BODY_DIAMETER_MM = 37.0
YELLOWJACKET_GEARBOX_LENGTH_MM = 24.0
YELLOWJACKET_GEARBOX_DIAMETER_MM = 36.0
YELLOWJACKET_SHAFT_LENGTH_MM = 24.0
YELLOWJACKET_SHAFT_DIAMETER_MM = 8.0
YELLOWJACKET_TOTAL_LENGTH_MM = (
    YELLOWJACKET_BODY_LENGTH_MM
    + YELLOWJACKET_GEARBOX_LENGTH_MM
    + YELLOWJACKET_SHAFT_LENGTH_MM
)


def _axis_offset(
    center: tuple[float, float, float],
    axis: Axis,
    distance: float,
) -> tuple[float, float, float]:
    x, y, z = center
    if axis == "x":
        return (x + distance, y, z)
    if axis == "y":
        return (x, y + distance, z)
    return (x, y, z + distance)


def _segment_center(
    center: tuple[float, float, float],
    axis: Axis,
    shaft_direction: ShaftDirection,
    start: float,
    length: float,
) -> tuple[float, float, float]:
    distance = shaft_direction * (-YELLOWJACKET_TOTAL_LENGTH_MM / 2 + start + length / 2)
    return _axis_offset(center, axis, distance)


def make_yellowjacket_motor_proxy(
    label: str,
    center: tuple[float, float, float],
    *,
    axis: Axis,
    shaft_direction: ShaftDirection = 1,
    intent: CrayonIntent | None = None,
):
    """Low-detail goBILDA Yellow Jacket sized motor for this FTC concept."""

    children = [
        crayon_cylinder(
            f"{label} RS-555 can",
            _segment_center(center, axis, shaft_direction, 0.0, YELLOWJACKET_BODY_LENGTH_MM),
            radius=YELLOWJACKET_BODY_DIAMETER_MM / 2,
            length=YELLOWJACKET_BODY_LENGTH_MM,
            axis=axis,
            color=CRAYON_MOTOR,
        ),
        crayon_cylinder(
            f"{label} 36 mm gearbox proxy",
            _segment_center(
                center,
                axis,
                shaft_direction,
                YELLOWJACKET_BODY_LENGTH_MM,
                YELLOWJACKET_GEARBOX_LENGTH_MM,
            ),
            radius=YELLOWJACKET_GEARBOX_DIAMETER_MM / 2,
            length=YELLOWJACKET_GEARBOX_LENGTH_MM,
            axis=axis,
            color="#111827",
        ),
        crayon_cylinder(
            f"{label} 8 mm REX shaft proxy",
            _segment_center(
                center,
                axis,
                shaft_direction,
                YELLOWJACKET_BODY_LENGTH_MM + YELLOWJACKET_GEARBOX_LENGTH_MM,
                YELLOWJACKET_SHAFT_LENGTH_MM,
            ),
            radius=YELLOWJACKET_SHAFT_DIAMETER_MM / 2,
            length=YELLOWJACKET_SHAFT_LENGTH_MM,
            axis=axis,
            color="#d1d5db",
        ),
    ]
    motor = Compound(children=children, label=label)
    motor.color = Color(CRAYON_MOTOR)
    if intent is not None:
        motor.user_data = {"crayon_intent": intent.as_dict()}
    return motor
