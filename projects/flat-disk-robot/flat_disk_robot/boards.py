from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Compound,
    Cylinder,
    Line,
    Locations,
    Mode,
    Plane,
    Rectangle,
    extrude,
    make_face,
)

from synthcad.cad.common import (
    BLACK,
    BLUE,
    COPPER_GOLD,
    COPPER_THICKNESS,
    OFF_WHITE,
    PCB_GREEN,
    PCB_THICKNESS,
    SILK_THICKNESS,
    SILK_WHITE,
    SILVER,
    SOLDER_MASK,
    annulus,
    box,
    circle_point,
    qfn_package,
    rounded_board,
    tag,
    text_label,
    trace_between,
)


TOF_EDGE_RADIUS = 3.5
TOF_NECK_RADIUS = 2.0
TOF_MOUNTING_HOLES = [
    (-17.5, 10.25, 1.55),
    (-17.5, -4.75, 1.55),
    (17.5, 10.25, 1.55),
    (17.5, -4.75, 1.55),
    (-7.5, -10.25, 1.55),
    (7.5, -10.25, 1.55),
]


def make_product_diagram_board() -> Compound:
    """Approximate the 40 mm x 15 mm board drawing from a project reference image."""

    small_vias = [
        (-18.0 + col * 0.82, -4.6 + row * 1.0, 0.16)
        for col in range(3)
        for row in range(4)
    ]
    small_vias.extend([(14.9 + i * 0.8, -6.2, 0.16) for i in range(4)])
    small_vias.extend([(-4.0, -2.4, 0.15), (-2.4, -2.2, 0.15), (3.1, -1.7, 0.15)])

    children = [rounded_board("40 x 15 mm rounded PCB", 40, 15, 1.5, small_vias)]

    for x, y, _radius in small_vias:
        children.append(annulus("plated via", x, y, 0.16, 0.29))

    pad_centers = [(-12.0, 3.0), (-5.0, 3.0), (8.4, 3.7), (15.2, 3.7), (8.4, -3.0), (15.2, -3.0)]
    for index, (x, y) in enumerate(pad_centers, start=1):
        children.append(
            box(
                f"rectangular electrode {index}",
                x,
                y,
                PCB_THICKNESS + COPPER_THICKNESS / 2,
                3.7,
                2.4,
                COPPER_THICKNESS,
                COPPER_GOLD,
            )
        )
        children.append(
            box(
                f"electrode notch {index}",
                x,
                y - 1.05,
                PCB_THICKNESS + COPPER_THICKNESS + 0.02,
                0.55,
                1.0,
                SILK_THICKNESS,
                SOLDER_MASK,
            )
        )

    trace_routes = [
        ((-10.0, 1.8), (-7.0, 0.0)),
        ((-5.0, 1.8), (-2.4, 0.0)),
        ((2.8, -1.2), (6.0, 1.5)),
        ((6.0, 1.5), (11.7, 1.5)),
        ((11.7, 1.5), (13.5, 2.2)),
        ((2.6, -3.2), (5.6, -5.8)),
        ((5.6, -5.8), (9.8, -5.8)),
        ((9.8, -5.8), (12.8, -4.2)),
        ((-8.0, -5.2), (-2.6, -5.2)),
        ((-2.6, -5.2), (-0.9, -3.2)),
        ((-7.4, 0.1), (-1.6, 0.1)),
    ]
    for index, (start, end) in enumerate(trace_routes, start=1):
        children.append(trace_between(f"copper trace {index}", start, end))

    children.extend(qfn_package("rotated controller IC", 0.0, -2.3, 3.6, 45, pins_per_side=6))

    for index, (x, y, length, width, color) in enumerate(
        [
            (-3.8, -2.8, 1.8, 1.0, BLACK),
            (-3.8, -3.7, 1.2, 0.45, SILVER),
            (-0.2, 2.9, 0.9, 1.0, SILVER),
            (2.2, 3.2, 1.1, 0.75, SILVER),
            (2.2, 4.4, 1.1, 0.75, SILVER),
        ],
        start=1,
    ):
        children.append(
            box(
                f"support component {index}",
                x,
                y,
                PCB_THICKNESS + 0.18,
                length,
                width,
                0.36,
                color,
            )
        )

    children.append(text_label("dimension label", "40 x 15 mm", 0, 6.4, 1.0))
    return Compound(children=children, label="product-diagram-board")


def _tof_satellite_vias(
    mounting_holes: list[tuple[float, float, float]],
) -> list[tuple[float, float, float]]:
    vias: list[tuple[float, float, float]] = []
    for x, y, _radius in mounting_holes:
        for angle in range(0, 360, 60):
            px = x + cos(radians(angle)) * 2.25
            py = y + sin(radians(angle)) * 2.25
            vias.append((px, py, 0.12))
    return vias


def _tof_board_outline(
    mounting_holes: list[tuple[float, float, float]],
    via_holes: list[tuple[float, float, float]],
):
    top_left = (-17.5, 10.25)
    top_right = (17.5, 10.25)
    side_right = (17.5, -4.75)
    bottom_right = (7.5, -10.25)
    bottom_left = (-7.5, -10.25)
    side_left = (-17.5, -4.75)
    left_neck = (bottom_left[0] - TOF_EDGE_RADIUS - TOF_NECK_RADIUS, bottom_left[1])
    right_neck = (bottom_right[0] + TOF_EDGE_RADIUS + TOF_NECK_RADIUS, bottom_right[1])

    with BuildPart() as board:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Line(
                    circle_point(top_left, TOF_EDGE_RADIUS, 90),
                    circle_point(top_right, TOF_EDGE_RADIUS, 90),
                )
                CenterArc(top_right, TOF_EDGE_RADIUS, 90, -90)
                Line(
                    circle_point(top_right, TOF_EDGE_RADIUS, 0),
                    circle_point(side_right, TOF_EDGE_RADIUS, 0),
                )
                CenterArc(side_right, TOF_EDGE_RADIUS, 0, -90)
                Line(
                    circle_point(side_right, TOF_EDGE_RADIUS, -90),
                    circle_point(right_neck, TOF_NECK_RADIUS, 90),
                )
                CenterArc(right_neck, TOF_NECK_RADIUS, 90, 90)
                CenterArc(bottom_right, TOF_EDGE_RADIUS, 0, -90)
                Line(
                    circle_point(bottom_right, TOF_EDGE_RADIUS, -90),
                    circle_point(bottom_left, TOF_EDGE_RADIUS, -90),
                )
                CenterArc(bottom_left, TOF_EDGE_RADIUS, -90, -90)
                CenterArc(left_neck, TOF_NECK_RADIUS, 0, 90)
                Line(
                    circle_point(left_neck, TOF_NECK_RADIUS, 90),
                    circle_point(side_left, TOF_EDGE_RADIUS, -90),
                )
                CenterArc(side_left, TOF_EDGE_RADIUS, -90, -90)
                Line(
                    circle_point(side_left, TOF_EDGE_RADIUS, 180),
                    circle_point(top_left, TOF_EDGE_RADIUS, 180),
                )
                CenterArc(top_left, TOF_EDGE_RADIUS, 180, -90)
            make_face()
        extrude(amount=PCB_THICKNESS)

        for x, y, radius in [*mounting_holes, *via_holes]:
            with Locations((x, y, PCB_THICKNESS / 2)):
                Cylinder(radius, PCB_THICKNESS * 3, mode=Mode.SUBTRACT)

    return tag(board.part, "42 x 27.5 mm TOF sensor PCB", PCB_GREEN)


def make_tof_sensor_board() -> Compound:
    """Approximate the TOF sensor board drawing in the flat disk robot references."""

    mounting_holes = TOF_MOUNTING_HOLES
    via_holes = _tof_satellite_vias(mounting_holes)
    children = [_tof_board_outline(mounting_holes, via_holes)]

    for x, y, radius in mounting_holes:
        children.append(annulus("3.1 mm plated mounting hole", x, y, radius, 2.45))
    for x, y, radius in via_holes:
        children.append(annulus("small drilled via", x, y, radius, 0.22))

    children.append(
        box(
            "central JST-style connector housing",
            0,
            -2.0,
            PCB_THICKNESS + 2.45,
            12.4,
            5.4,
            4.9,
            OFF_WHITE,
        )
    )
    for index, x in enumerate([-4.2, -1.4, 1.4, 4.2], start=1):
        children.append(
            box(
                f"connector contact {index}",
                x,
                1.25,
                PCB_THICKNESS + 0.15,
                0.55,
                2.5,
                0.18,
                SILVER,
            )
        )

    children.append(box("TOF sensor module", 13.6, 4.4, PCB_THICKNESS + 0.75, 7.2, 4.8, 1.5, BLACK))
    children.append(box("sensor lens opening", 13.6, 4.4, PCB_THICKNESS + 1.56, 2.6, 1.8, 0.12, BLUE))
    children.append(box("boot switch base", -15.8, 4.4, PCB_THICKNESS + 0.55, 4.2, 4.0, 1.1, SILVER))
    children.append(box("boot switch cap", -15.8, 4.4, PCB_THICKNESS + 1.25, 2.3, 2.4, 0.9, OFF_WHITE))

    for index, x in enumerate([-5.0, -2.5, 0.0, 2.5, 5.0], start=1):
        children.append(
            box(
                f"vertical pin pad {index}",
                x,
                3.7,
                PCB_THICKNESS + COPPER_THICKNESS / 2,
                0.5,
                2.6,
                COPPER_THICKNESS,
                COPPER_GOLD,
            )
        )
    for index, y in enumerate([3.2, 2.3, 1.4, 0.5], start=1):
        children.append(
            box(
                f"right header pad {index}",
                18.4,
                y,
                PCB_THICKNESS + COPPER_THICKNESS / 2,
                2.0,
                0.35,
                COPPER_THICKNESS,
                COPPER_GOLD,
            )
        )
    for index, y in enumerate([-1.4, -2.3, -3.2, -4.1], start=1):
        children.append(
            box(
                f"power pad {index}",
                13.8,
                y,
                PCB_THICKNESS + COPPER_THICKNESS / 2,
                0.35,
                1.4,
                COPPER_THICKNESS,
                COPPER_GOLD,
            )
        )

    children.append(
        box(
            "address table silkscreen border",
            0.0,
            7.5,
            PCB_THICKNESS + COPPER_THICKNESS / 2,
            6.5,
            4.9,
            COPPER_THICKNESS,
            SILK_WHITE,
        )
    )
    children.append(
        box(
            "address table fill",
            0.0,
            7.5,
            PCB_THICKNESS + COPPER_THICKNESS + 0.02,
            6.05,
            4.45,
            SILK_THICKNESS,
            PCB_GREEN,
        )
    )
    for x in [-1.15, 1.15]:
        children.append(
            box(
                "address table column rule",
                x,
                7.5,
                PCB_THICKNESS + COPPER_THICKNESS + 0.05,
                0.08,
                4.5,
                SILK_THICKNESS,
                SILK_WHITE,
            )
        )
    for y in [6.4, 7.5, 8.6]:
        children.append(
            box(
                "address table row rule",
                0.0,
                y,
                PCB_THICKNESS + COPPER_THICKNESS + 0.05,
                6.1,
                0.08,
                SILK_THICKNESS,
                SILK_WHITE,
            )
        )

    children.extend(
        [
            text_label("boot label", "BOOT", -15.8, 1.0, 0.9),
            text_label("uart label", "UART", 16.5, 1.2, 0.8),
            text_label("i2c label", "I2C", 18.1, 0.1, 0.8),
            text_label("power label", "PWR", 14.0, -5.5, 0.8),
            text_label("address label", "A0 A1 ADDR", 0.0, 9.2, 0.42),
            text_label("hole dimension label", "six holes: 3.1 mm", 0.0, -12.0, 0.58),
        ]
    )

    return Compound(children=children, label="tof-sensor-board")
