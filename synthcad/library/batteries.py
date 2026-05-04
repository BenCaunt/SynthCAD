from __future__ import annotations

from build123d import Box, BuildPart, BuildSketch, Compound, Location, Plane, RectangleRounded, Text, extrude

from synthcad.cad.common import BATTERY_BLACK, BATTERY_LABEL, SILVER, tag


# OCR/readback from real-parts/battery.png:
# OVONIC 4S1P 14.8V, 1550 mAh, 100C, 22.94 Wh, 2.87 x 1.42 x 1.50 in.
BATTERY_LENGTH = 73.0
BATTERY_WIDTH = 36.0
BATTERY_HEIGHT = 38.0
BATTERY_CORNER_RADIUS = 4.0
BATTERY_LEAD_RESERVE = 20.0


def _rounded_pack_body():
    with BuildPart() as body:
        with BuildSketch(Plane.XY):
            RectangleRounded(BATTERY_LENGTH, BATTERY_WIDTH, BATTERY_CORNER_RADIUS)
        extrude(amount=BATTERY_HEIGHT)
    return tag(body.part, "OVONIC 4S 1550 mAh LiPo body", BATTERY_BLACK)


def make_small_4s_battery() -> Compound:
    """Reference 73 x 36 x 38 mm 4S LiPo pack from real-parts/battery.png."""

    children = [_rounded_pack_body()]
    children.append(
        tag(
            Location((0, 0, BATTERY_HEIGHT + 0.03))
            * Box(BATTERY_LENGTH - 8, BATTERY_WIDTH - 8, 0.08),
            "battery top label",
            BATTERY_LABEL,
        )
    )
    with BuildPart() as lettering:
        with BuildSketch(Plane.XY):
            Text("4S 1550mAh", 4.0)
        extrude(amount=0.08)
    children.append(
        tag(
            Location((0, 0, BATTERY_HEIGHT + 0.12)) * lettering.part,
            "battery label text",
            BATTERY_BLACK,
        )
    )
    children.append(
        tag(
            Location((BATTERY_LENGTH / 2 + BATTERY_LEAD_RESERVE / 2, 4.0, BATTERY_HEIGHT - 8.0))
            * Box(BATTERY_LEAD_RESERVE, 3.0, 3.0),
            "main discharge lead clearance reference",
            SILVER,
        )
    )
    children.append(
        tag(
            Location((BATTERY_LENGTH / 2 + BATTERY_LEAD_RESERVE / 2 - 3.0, -5.0, BATTERY_HEIGHT - 13.0))
            * Box(BATTERY_LEAD_RESERVE - 6.0, 2.0, 2.0),
            "balance lead clearance reference",
            SILVER,
        )
    )

    return Compound(children=children, label="small-4s-battery")
