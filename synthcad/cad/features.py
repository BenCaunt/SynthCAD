from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import pi
from typing import Iterable


@dataclass(frozen=True)
class CircularFeature:
    center: tuple[float, ...]
    radius: float
    count: int


def _axis_value(vector, axis: str) -> float:
    return float(getattr(vector, axis.upper()))


def _round_tuple(values: Iterable[float], digits: int) -> tuple[float, ...]:
    return tuple(round(value, digits) for value in values)


def candidate_circular_holes(
    shape,
    *,
    radius_min: float = 0.5,
    radius_max: float = 5.0,
    center_axes: tuple[str, ...] = ("X", "Y"),
    digits: int = 3,
    full_circle_tolerance: float = 0.02,
    min_edge_count: int = 2,
) -> list[CircularFeature]:
    """Return grouped full-circle edges that look like drilled holes.

    STEP imports usually expose a through-hole as matching circular edges on the
    top and bottom faces. This utility intentionally works from topology rather
    than filenames or labels, so it is useful for vendor parts with unknown
    mounting patterns.
    """

    grouped: dict[tuple[tuple[float, ...], float], int] = defaultdict(int)
    for edge in shape.edges():
        if str(edge.geom_type) != "GeomType.CIRCLE":
            continue

        radius = float(edge.radius)
        if not radius_min <= radius <= radius_max:
            continue

        if abs(float(edge.length) - 2 * pi * radius) > full_circle_tolerance:
            continue

        center = edge.arc_center
        key_center = _round_tuple(
            [_axis_value(center, axis) for axis in center_axes],
            digits,
        )
        key_radius = round(radius, digits)
        grouped[(key_center, key_radius)] += 1

    features = [
        CircularFeature(center=center, radius=radius, count=count)
        for (center, radius), count in grouped.items()
        if count >= min_edge_count
    ]
    return sorted(features, key=lambda item: (item.radius, item.center))
