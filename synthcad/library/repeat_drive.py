from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Circle,
    Compound,
    Cylinder,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    add,
    extrude,
)

from synthcad.cad.common import PRINTED_FRAME, SILVER, TPU_BLACK, tag
from synthcad.external_parts import REPEAT_COMPACT_1806


CHASSIS_LENGTH = 110.0
CHASSIS_WIDTH = 78.0
CHASSIS_BASE_THICKNESS = 4.0
CHASSIS_CORNER_RADIUS = 8.0

AXLE_X = -18.0
AXLE_Z = 22.0
MOTOR_PLATE_Y = 37.0
MOTOR_FACE_Y = 35.0
MOTOR_PLATE_THICKNESS = 4.0
MOTOR_PLATE_LENGTH = 34.0
MOTOR_PLATE_HEIGHT = 32.0
MOTOR_STEP_FACE_Z = 5.0
MOTOR_BOLT_CIRCLE_RADIUS = 9.0
MOTOR_BOLT_ANGLES = (45, 135, 225, 315)
M2_CLEARANCE_RADIUS = 1.15
M2_COUNTERBORE_RADIUS = 2.15
M2_COUNTERBORE_DEPTH = 1.4
FACE_REGISTER_RADIUS = 7.2
FACE_REGISTER_DEPTH = 0.8
SHAFT_CLEARANCE_RADIUS = 4.2

WHEEL_RADIUS = 22.0
WHEEL_WIDTH = 16.0
WHEEL_HUB_RADIUS = 9.0
WHEEL_HUB_WIDTH = 18.0
WHEEL_SIDE_LIP_WIDTH = 1.0
WHEEL_CENTER_Y = 50.7
WHEEL_D_BORE_RADIUS = 1.9
WHEEL_D_BORE_FLAT_OFFSET = 1.32
WHEEL_BORE_LEAD_RADIUS = 2.15
WHEEL_SCREW_ACCESS_RADIUS = 3.5
WHEEL_SCREW_ACCESS_ANGLE_DEG = 45.0

MOTOR_RIB_DEPTH = 8.0
MOTOR_RIB_THICKNESS = 4.0
MOTOR_RIB_HEIGHT = 24.0
CASTER_BOSS_X = 42.0
CASTER_BOSS_RADIUS = 11.0
CASTER_BOSS_HEIGHT = 2.0
M3_CLEARANCE_RADIUS = 1.7


def d_bore_cut(length: float):
    """Create a D-shaped cutting prism for the 4 mm Repeat Compact shaft."""

    with BuildPart() as bore:
        with BuildSketch(Plane.XZ):
            Circle(WHEEL_D_BORE_RADIUS)
            with Locations((0, WHEEL_D_BORE_FLAT_OFFSET + WHEEL_D_BORE_RADIUS)):
                Rectangle(
                    WHEEL_D_BORE_RADIUS * 4,
                    WHEEL_D_BORE_RADIUS * 2,
                    mode=Mode.SUBTRACT,
                )
        extrude(amount=length)

    return Location((0, length / 2, 0)) * bore.part


def make_tpu_d_bore_wheel(
    radius: float = WHEEL_RADIUS,
    screw_access_radius: float | None = WHEEL_SCREW_ACCESS_RADIUS,
):
    """Press-fit TPU wheel for the Repeat Compact 4 mm D shaft."""

    with BuildPart() as wheel:
        Cylinder(radius, WHEEL_WIDTH, rotation=(90, 0, 0))
        Cylinder(WHEEL_HUB_RADIUS, WHEEL_HUB_WIDTH, rotation=(90, 0, 0))

        for y in [
            -WHEEL_WIDTH / 2 + WHEEL_SIDE_LIP_WIDTH / 2,
            WHEEL_WIDTH / 2 - WHEEL_SIDE_LIP_WIDTH / 2,
        ]:
            with Locations((0, y, 0)):
                Cylinder(
                    radius,
                    WHEEL_SIDE_LIP_WIDTH,
                    rotation=(90, 0, 0),
                )

        if screw_access_radius is not None:
            access_x = cos(radians(WHEEL_SCREW_ACCESS_ANGLE_DEG)) * MOTOR_BOLT_CIRCLE_RADIUS
            access_z = sin(radians(WHEEL_SCREW_ACCESS_ANGLE_DEG)) * MOTOR_BOLT_CIRCLE_RADIUS
            with Locations((access_x, 0, access_z)):
                Cylinder(
                    screw_access_radius,
                    WHEEL_HUB_WIDTH + 4.0,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )

        add(d_bore_cut(WHEEL_HUB_WIDTH + 6), mode=Mode.SUBTRACT)
        for y in [
            -WHEEL_HUB_WIDTH / 2 + 0.45,
            WHEEL_HUB_WIDTH / 2 - 0.45,
        ]:
            with Locations((0, y, 0)):
                Cylinder(
                    WHEEL_BORE_LEAD_RADIUS,
                    0.9,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )

    return tag(wheel.part, "TPU press-fit D-bore wheel", TPU_BLACK)


def motor_plate_hole_centers() -> list[tuple[float, float]]:
    return [
        (
            AXLE_X + cos(radians(angle)) * MOTOR_BOLT_CIRCLE_RADIUS,
            AXLE_Z + sin(radians(angle)) * MOTOR_BOLT_CIRCLE_RADIUS,
        )
        for angle in MOTOR_BOLT_ANGLES
    ]


def motor_bolt_circle_offsets() -> list[tuple[float, float]]:
    return [
        (
            cos(radians(angle)) * MOTOR_BOLT_CIRCLE_RADIUS,
            sin(radians(angle)) * MOTOR_BOLT_CIRCLE_RADIUS,
        )
        for angle in MOTOR_BOLT_ANGLES
    ]


def make_repeat_drive_frame():
    """Simple printed differential-drive frame for two face-mounted motors."""

    with BuildPart() as frame:
        with BuildSketch(Plane.XY):
            RectangleRounded(CHASSIS_LENGTH, CHASSIS_WIDTH, CHASSIS_CORNER_RADIUS)
        extrude(amount=CHASSIS_BASE_THICKNESS)

        for side in [-1, 1]:
            with Locations(
                (
                    AXLE_X,
                    side * MOTOR_PLATE_Y,
                    CHASSIS_BASE_THICKNESS + MOTOR_PLATE_HEIGHT / 2,
                )
            ):
                Box(MOTOR_PLATE_LENGTH, MOTOR_PLATE_THICKNESS, MOTOR_PLATE_HEIGHT)

            rib_y = side * (MOTOR_FACE_Y - MOTOR_RIB_DEPTH / 2)
            for rib_x in [
                AXLE_X - MOTOR_PLATE_LENGTH / 2 + 4.0,
                AXLE_X + MOTOR_PLATE_LENGTH / 2 - 4.0,
            ]:
                with Locations(
                    (
                        rib_x,
                        rib_y,
                        CHASSIS_BASE_THICKNESS + MOTOR_RIB_HEIGHT / 2,
                    )
                ):
                    Box(MOTOR_RIB_THICKNESS, MOTOR_RIB_DEPTH, MOTOR_RIB_HEIGHT)

            with Locations((AXLE_X, side * MOTOR_PLATE_Y, AXLE_Z)):
                Cylinder(
                    SHAFT_CLEARANCE_RADIUS,
                    MOTOR_PLATE_THICKNESS * 4,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )

            register_y = side * (MOTOR_FACE_Y + FACE_REGISTER_DEPTH / 2)
            with Locations((AXLE_X, register_y, AXLE_Z)):
                Cylinder(
                    FACE_REGISTER_RADIUS,
                    FACE_REGISTER_DEPTH,
                    rotation=(90, 0, 0),
                    mode=Mode.SUBTRACT,
                )

            counterbore_y = side * (
                MOTOR_PLATE_Y
                + MOTOR_PLATE_THICKNESS / 2
                - M2_COUNTERBORE_DEPTH / 2
            )
            for x, z in motor_plate_hole_centers():
                with Locations((x, side * MOTOR_PLATE_Y, z)):
                    Cylinder(
                        M2_CLEARANCE_RADIUS,
                        MOTOR_PLATE_THICKNESS * 4,
                        rotation=(90, 0, 0),
                        mode=Mode.SUBTRACT,
                    )
                with Locations((x, counterbore_y, z)):
                    Cylinder(
                        M2_COUNTERBORE_RADIUS,
                        M2_COUNTERBORE_DEPTH + 0.1,
                        rotation=(90, 0, 0),
                        mode=Mode.SUBTRACT,
                    )

        with Locations((CASTER_BOSS_X, 0, CHASSIS_BASE_THICKNESS)):
            Cylinder(CASTER_BOSS_RADIUS, CASTER_BOSS_HEIGHT)

        for x in [CASTER_BOSS_X - 8.0, CASTER_BOSS_X + 8.0]:
            with Locations((x, 0, CHASSIS_BASE_THICKNESS / 2)):
                Cylinder(
                    M3_CLEARANCE_RADIUS,
                    CHASSIS_BASE_THICKNESS * 3,
                    mode=Mode.SUBTRACT,
                )

        for x, y in [(6, -20), (6, 20), (36, -20), (36, 20)]:
            with Locations((x, y, CHASSIS_BASE_THICKNESS / 2)):
                Cylinder(
                    M3_CLEARANCE_RADIUS,
                    CHASSIS_BASE_THICKNESS * 3,
                    mode=Mode.SUBTRACT,
                )

        for x in [-2, 24]:
            for y in [-24, 24]:
                with Locations((x, y, CHASSIS_BASE_THICKNESS / 2)):
                    Box(4.0, 16.0, CHASSIS_BASE_THICKNESS * 3, mode=Mode.SUBTRACT)

    return tag(
        frame.part,
        "3D printed differential-drive chassis frame",
        PRINTED_FRAME,
    )


def place_repeat_drive_motor_on_y_axis(side: int):
    motor = REPEAT_COMPACT_1806.load()
    placed = Location(
        (AXLE_X, side * (MOTOR_FACE_Y - MOTOR_STEP_FACE_Z), AXLE_Z),
        (-90 * side, 0, 0),
    ) * motor
    label = (
        "right Repeat Compact 1806 gearmotor"
        if side > 0
        else "left Repeat Compact 1806 gearmotor"
    )
    return tag(placed, label, SILVER)


def place_wheel_on_y_axis(side: int):
    wheel = make_tpu_d_bore_wheel()
    rotation = (0, 180, 0) if side > 0 else (0, 0, 0)
    placed = Location((AXLE_X, side * WHEEL_CENTER_Y, AXLE_Z), rotation) * wheel
    label = "right TPU press-fit wheel" if side > 0 else "left TPU press-fit wheel"
    return tag(placed, label, TPU_BLACK)


def motor_screw_head_on_y_axis(side: int, x: float, z: float, index: int):
    y = side * (
        MOTOR_PLATE_Y + MOTOR_PLATE_THICKNESS / 2 + M2_COUNTERBORE_DEPTH / 2
    )
    screw = Location((x, y, z)) * Cylinder(
        M2_COUNTERBORE_RADIUS * 0.82,
        M2_COUNTERBORE_DEPTH,
        rotation=(90, 0, 0),
    )
    return tag(screw, f"M2 face-mount screw head {index}", SILVER)


def make_repeat_drive_differential_chassis() -> Compound:
    """Assembly showing motors face-mounted to the printed frame with TPU wheels."""

    children = [make_repeat_drive_frame()]

    for side in [-1, 1]:
        children.append(place_repeat_drive_motor_on_y_axis(side))
        children.append(place_wheel_on_y_axis(side))
        for index, (x, z) in enumerate(motor_plate_hole_centers(), start=1):
            children.append(motor_screw_head_on_y_axis(side, x, z, index))

    return Compound(children=children, label="repeat-drive-differential-chassis")
