from __future__ import annotations

from build123d import Color, Cylinder, Location

from synthcad.cad.common import OFF_WHITE, tag


def make_vertical_access_keepout(
    *,
    label: str,
    x: float,
    y: float,
    z_min: float,
    z_max: float,
    radius: float,
    color: str = OFF_WHITE,
    alpha: float = 1.0,
):
    """Reference volume for straight-line top access to a fastener or tool.

    Add these keep-out solids to reference assemblies and run interference
    checks. Any overlap means nearby geometry blocks the assumed vertical tool
    approach path.
    """

    if z_max <= z_min:
        raise ValueError("z_max must be greater than z_min")
    if not 0.0 <= alpha <= 1.0:
        raise ValueError("alpha must be between 0.0 and 1.0")

    height = z_max - z_min
    keepout = Location((x, y, z_min + height / 2)) * Cylinder(radius, height)
    tagged = tag(keepout, label, color)
    tagged.color = Color(color, alpha)
    return tagged
