from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Text,
    TextAlign,
    extrude,
)

from synthcad.cad.common import BLACK, BLUE, OFF_WHITE, SILVER, tag


M3564C_OUTER_DIAMETER = 60.0
M3564C_OUTER_RADIUS = M3564C_OUTER_DIAMETER / 2
M3564C_OUTER_RING_THICKNESS = 12.0
M3564C_FACE_OFFSET = 0.5
M3564C_TOTAL_HEIGHT = M3564C_OUTER_RING_THICKNESS + M3564C_FACE_OFFSET
M3564C_INNER_RING_DIAMETER = 35.0
M3564C_INNER_RING_RADIUS = M3564C_INNER_RING_DIAMETER / 2

M3564C_CENTER_BORE_DIAMETER = 7.0
M3564C_TOOL_CLEARANCE_HOLE_DIAMETER = 5.2
M3564C_TOOL_CLEARANCE_BOLT_CIRCLE_DIAMETER = 24.0
M3564C_TOOL_DOWEL_HOLE_DIAMETER = 3.01
M3564C_TOOL_DOWEL_BOLT_CIRCLE_DIAMETER = 28.0
M3564C_ROBOT_M5_THREAD_NOMINAL_DIAMETER = 5.0
M3564C_ROBOT_M5_THREAD_MODEL_DIAMETER = 4.2
M3564C_ROBOT_M5_THREAD_DIAMETER = M3564C_ROBOT_M5_THREAD_MODEL_DIAMETER
M3564C_ROBOT_MOUNT_BOLT_CIRCLE_DIAMETER = 55.0
M3564C_ROBOT_DOWEL_HOLE_DIAMETER = 3.01
M3564C_ROBOT_DOWEL_BOLT_CIRCLE_DIAMETER = 55.0
M3564C_DOWEL_POCKET_DEPTH = 3.0

M3564C_M5_PAIR_SPACING_DEGREES = 70.0
M3564C_M5_PAIR_HALF_ANGLE_DEGREES = M3564C_M5_PAIR_SPACING_DEGREES / 2
M3564C_REPEATED_PATTERN_ANGLE_DEGREES = 120.0
M3564C_TOOL_CLEARANCE_HOLE_COUNT = 6
M3564C_DOWEL_HOLE_COUNT_PER_FACE = 3
M3564C_ROBOT_M5_THREAD_COUNT = 6

M3564C_CABLE_GLAND_WIDTH = 12.0
M3564C_CABLE_GLAND_LENGTH = 10.0
M3564C_CABLE_GLAND_HEIGHT = 5.0
M3564C_CABLE_STUB_LENGTH = 18.0
M3564C_CABLE_STUB_RADIUS = 1.8


def _bolt_circle_points(
    diameter: float,
    angles_degrees: tuple[float, ...],
) -> list[tuple[float, float]]:
    radius = diameter / 2
    points = []
    for angle_degrees in angles_degrees:
        angle = radians(angle_degrees)
        points.append((radius * cos(angle), radius * sin(angle)))
    return points


def m3564c_tool_clearance_hole_centers() -> list[tuple[float, float]]:
    """Return the six 5.20 mm through holes on the 24 mm bolt circle."""

    angles = tuple(
        index * 360.0 / M3564C_TOOL_CLEARANCE_HOLE_COUNT
        for index in range(M3564C_TOOL_CLEARANCE_HOLE_COUNT)
    )
    return _bolt_circle_points(M3564C_TOOL_CLEARANCE_BOLT_CIRCLE_DIAMETER, angles)


def m3564c_tool_dowel_hole_centers() -> list[tuple[float, float]]:
    """Return the three 3.01 mm blind tool-side dowel pockets."""

    return _bolt_circle_points(M3564C_TOOL_DOWEL_BOLT_CIRCLE_DIAMETER, (-90.0, 30.0, 150.0))


def m3564c_robot_m5_thread_centers() -> list[tuple[float, float]]:
    """Return the six M5 through holes from the repeated 70 degree pair pattern."""

    angles = []
    pair_centers = tuple(
        90.0 + index * M3564C_REPEATED_PATTERN_ANGLE_DEGREES
        for index in range(3)
    )
    for pair_center in pair_centers:
        angles.extend(
            [
                pair_center - M3564C_M5_PAIR_HALF_ANGLE_DEGREES,
                pair_center + M3564C_M5_PAIR_HALF_ANGLE_DEGREES,
            ]
        )
    return _bolt_circle_points(M3564C_ROBOT_MOUNT_BOLT_CIRCLE_DIAMETER, tuple(angles))


def m3564c_robot_dowel_hole_centers() -> list[tuple[float, float]]:
    """Return the three 3.01 mm blind robot-side dowel pockets."""

    return _bolt_circle_points(M3564C_ROBOT_DOWEL_BOLT_CIRCLE_DIAMETER, (-90.0, 30.0, 150.0))


def _add_subtractive_cylinder(
    radius: float,
    height: float,
    center_z: float,
    centers: list[tuple[float, float]],
) -> None:
    for x, y in centers:
        with Locations((x, y, center_z)):
            Cylinder(radius, height, mode=Mode.SUBTRACT)


def _make_m3564c_body():
    through_height = M3564C_TOTAL_HEIGHT + 1.0
    through_center_z = M3564C_TOTAL_HEIGHT / 2

    with BuildPart() as body:
        with Locations((0, 0, M3564C_OUTER_RING_THICKNESS / 2)):
            Cylinder(M3564C_OUTER_RADIUS, M3564C_OUTER_RING_THICKNESS)

        with Locations((0, 0, M3564C_OUTER_RING_THICKNESS + M3564C_FACE_OFFSET / 2)):
            Cylinder(M3564C_INNER_RING_RADIUS, M3564C_FACE_OFFSET)

        with Locations((0, 0, M3564C_FACE_OFFSET / 2)):
            Cylinder(
                M3564C_INNER_RING_RADIUS,
                M3564C_FACE_OFFSET + 0.02,
                mode=Mode.SUBTRACT,
            )

        _add_subtractive_cylinder(
            M3564C_CENTER_BORE_DIAMETER / 2,
            through_height,
            through_center_z,
            [(0.0, 0.0)],
        )
        _add_subtractive_cylinder(
            M3564C_TOOL_CLEARANCE_HOLE_DIAMETER / 2,
            through_height,
            through_center_z,
            m3564c_tool_clearance_hole_centers(),
        )
        _add_subtractive_cylinder(
            M3564C_ROBOT_M5_THREAD_DIAMETER / 2,
            through_height,
            through_center_z,
            m3564c_robot_m5_thread_centers(),
        )

        _add_subtractive_cylinder(
            M3564C_TOOL_DOWEL_HOLE_DIAMETER / 2,
            M3564C_DOWEL_POCKET_DEPTH + 0.05,
            M3564C_TOTAL_HEIGHT - M3564C_DOWEL_POCKET_DEPTH / 2,
            m3564c_tool_dowel_hole_centers(),
        )
        _add_subtractive_cylinder(
            M3564C_ROBOT_DOWEL_HOLE_DIAMETER / 2,
            M3564C_DOWEL_POCKET_DEPTH + 0.05,
            M3564C_DOWEL_POCKET_DEPTH / 2,
            m3564c_robot_dowel_hole_centers(),
        )

    return tag(body.part, "M3564C machined load-cell body", SILVER)


def _make_top_label(text: str, y: float, size: float):
    with BuildPart() as label:
        with BuildSketch(Plane.XY):
            Text(
                text,
                size,
                text_align=(TextAlign.CENTER, TextAlign.CENTER),
                align=(Align.CENTER, Align.CENTER),
            )
        extrude(amount=0.06)
    return tag(
        Location((0, y, M3564C_OUTER_RING_THICKNESS + 0.02)) * label.part,
        f"M3564C top marking {text}",
        BLACK,
    )


def _make_cable_gland():
    gland = Location(
        (
            0.0,
            -M3564C_OUTER_RADIUS - M3564C_CABLE_GLAND_LENGTH / 2 + 1.0,
            M3564C_CABLE_GLAND_HEIGHT / 2,
        )
    ) * Box(
        M3564C_CABLE_GLAND_WIDTH,
        M3564C_CABLE_GLAND_LENGTH,
        M3564C_CABLE_GLAND_HEIGHT,
    )
    return tag(gland, "M3564C molded cable gland", BLACK)


def _make_cable_stub():
    cable = Location(
        (
            0.0,
            -M3564C_OUTER_RADIUS - M3564C_CABLE_GLAND_LENGTH - M3564C_CABLE_STUB_LENGTH / 2,
            M3564C_CABLE_STUB_RADIUS,
        )
    ) * Cylinder(
        M3564C_CABLE_STUB_RADIUS,
        M3564C_CABLE_STUB_LENGTH,
        rotation=(90, 0, 0),
    )
    return tag(cable, "M3564C 4 m cable direction stub", BLUE)


def make_m3564c_load_cell() -> Compound:
    """Reference model of the Sunrise Instruments M3564C six-axis load cell."""

    children = [
        _make_m3564c_body(),
        _make_cable_gland(),
        _make_cable_stub(),
        _make_top_label("M3564C", 21.0, 3.0),
        _make_top_label("TOOL SIDE", -21.0, 2.2),
    ]
    return tag(
        Compound(children=children, label="M3564C six-axis circular load cell"),
        "M3564C six-axis circular load cell",
        OFF_WHITE,
    )
