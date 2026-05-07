from __future__ import annotations

from math import cos, radians, sin

from build123d import (
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Compound,
    Cylinder,
    Line,
    Location,
    Locations,
    Mode,
    Plane,
    add,
    extrude,
    make_face,
)

from synthcad.cad.common import (
    BLACK,
    PRINTED_FRAME,
    SILVER,
    TPU_BLACK,
    tag,
)
from synthcad.external_parts import SO_ARM_101_ASSEMBLY
from synthcad.projects.flat_disk_robot.robot import (
    LID_DOCK_MAGNET_CENTER_Z,
    LID_DOCK_MAGNET_DIAMETER,
    LID_DOCK_MAGNET_POCKET_DEPTH,
    LID_DOCK_MAGNET_POCKET_RADIUS,
    LID_DOCK_MAGNET_RADIUS,
    LID_DOCK_MAGNET_THICKNESS,
    LID_TOP_SURFACE_Z,
    LID_WALL_BOTTOM_Z,
    ROBOT_RADIUS,
    lid_dock_magnet_theta_deg,
    make_flat_disk_robot,
)


# Cradle wraps the rear arc of the disk robot with a small clearance gap.
CART_DOCK_GAP = 0.5
CART_CRADLE_INNER_RADIUS = ROBOT_RADIUS + CART_DOCK_GAP
CART_CRADLE_THICKNESS = 8.0
CART_CRADLE_OUTER_RADIUS = CART_CRADLE_INNER_RADIUS + CART_CRADLE_THICKNESS
CART_CRADLE_HALF_SWEEP_DEG = 40.0
CART_CRADLE_CENTER_ANGLE_DEG = -90.0
CART_CRADLE_BOTTOM_Z = LID_WALL_BOTTOM_Z
CART_CRADLE_TOP_Z = LID_TOP_SURFACE_Z
CART_CRADLE_HEIGHT = CART_CRADLE_TOP_Z - CART_CRADLE_BOTTOM_Z

# Top deck is co-planar with the disk-robot lid roof so a payload can slide
# back and forth across the dock without a step.
CART_DECK_WIDTH = 180.0
CART_DECK_LENGTH = 260.0
CART_DECK_THICKNESS = 8.0
CART_DECK_TOP_Z = CART_CRADLE_TOP_Z
CART_DECK_BOTTOM_Z = CART_DECK_TOP_Z - CART_DECK_THICKNESS
# Slight overlap into the cradle keeps the deck/cradle weld solid.
CART_DECK_FRONT_Y = -CART_CRADLE_OUTER_RADIUS + 4.0
CART_DECK_REAR_Y = CART_DECK_FRONT_Y - CART_DECK_LENGTH
CART_DECK_CENTER_Y = (CART_DECK_FRONT_Y + CART_DECK_REAR_Y) / 2

# Two passive idler wheels on a single M5 axle let the disk robot push or pull
# the cart like a wheelbarrow (with the magnetic dock standing in for the
# front legs).
CART_WHEEL_RADIUS = 35.0
CART_WHEEL_TIRE_WIDTH = 12.0
CART_WHEEL_HUB_RADIUS = 9.0
CART_WHEEL_HUB_WIDTH = 16.0
CART_WHEEL_BORE_RADIUS = 2.7
CART_AXLE_RADIUS = 2.5
CART_AXLE_Z = CART_WHEEL_RADIUS

CART_CHEEK_THICKNESS = 6.0
CART_CHEEK_LENGTH = 80.0
CART_CHEEK_X = CART_DECK_WIDTH / 2 - CART_CHEEK_THICKNESS / 2
CART_CHEEK_BOTTOM_Z = 0.0
CART_CHEEK_TOP_Z = CART_DECK_BOTTOM_Z
CART_CHEEK_HEIGHT = CART_CHEEK_TOP_Z - CART_CHEEK_BOTTOM_Z
CART_CHEEK_CENTER_Z = (CART_CHEEK_BOTTOM_Z + CART_CHEEK_TOP_Z) / 2

CART_WHEEL_CENTER_X = (
    CART_CHEEK_X
    + CART_CHEEK_THICKNESS / 2
    + CART_WHEEL_HUB_WIDTH / 2
    + 1.0
)
CART_WHEEL_CENTER_Y = CART_DECK_REAR_Y + 60.0
CART_AXLE_LENGTH = 2 * (CART_WHEEL_CENTER_X + CART_WHEEL_HUB_WIDTH / 2 + 2.0)

# SO-101 arm sits on the deck top.  We center it on the cart and put the base
# slightly forward of the wheel axle for a sensible mass distribution.
CART_ARM_BASE_X = 0.0
CART_ARM_BASE_Y = CART_WHEEL_CENTER_Y + 60.0
CART_ARM_BASE_Z = CART_DECK_TOP_Z


def _cradle_segment_part():
    ts_deg = CART_CRADLE_CENTER_ANGLE_DEG - CART_CRADLE_HALF_SWEEP_DEG
    te_deg = CART_CRADLE_CENTER_ANGLE_DEG + CART_CRADLE_HALF_SWEEP_DEG
    ri = CART_CRADLE_INNER_RADIUS
    ro = CART_CRADLE_OUTER_RADIUS

    p_outer_start = (
        ro * cos(radians(ts_deg)),
        ro * sin(radians(ts_deg)),
    )
    p_outer_end = (
        ro * cos(radians(te_deg)),
        ro * sin(radians(te_deg)),
    )
    p_inner_start = (
        ri * cos(radians(ts_deg)),
        ri * sin(radians(ts_deg)),
    )
    p_inner_end = (
        ri * cos(radians(te_deg)),
        ri * sin(radians(te_deg)),
    )

    with BuildPart() as cradle:
        with BuildSketch(Plane.XY):
            with BuildLine():
                CenterArc((0, 0), ro, ts_deg, te_deg - ts_deg)
                Line(p_outer_end, p_inner_end)
                CenterArc((0, 0), ri, te_deg, ts_deg - te_deg)
                Line(p_inner_start, p_outer_start)
            make_face()
        extrude(amount=CART_CRADLE_HEIGHT)
    return cradle.part


def _cart_dock_magnet_radial_location(side: int) -> Location:
    """Magnet outer-face center on the cradle inner surface, +X radial outward."""

    theta_deg = lid_dock_magnet_theta_deg(side)
    cx = CART_CRADLE_INNER_RADIUS * cos(radians(theta_deg))
    cy = CART_CRADLE_INNER_RADIUS * sin(radians(theta_deg))
    return Location(
        (cx, cy, LID_DOCK_MAGNET_CENTER_Z),
        (0, 0, theta_deg),
    )


def _add_cart_magnet_pocket(side: int):
    base = _cart_dock_magnet_radial_location(side)
    pocket_local_x = LID_DOCK_MAGNET_POCKET_DEPTH / 2
    with Locations(base * Location((pocket_local_x, 0, 0))):
        Cylinder(
            LID_DOCK_MAGNET_POCKET_RADIUS,
            LID_DOCK_MAGNET_POCKET_DEPTH + 0.4,
            rotation=(0, 90, 0),
            mode=Mode.SUBTRACT,
        )


def make_so101_cart_deck():
    """Printable cart body that wraps the disk robot rear and carries the SO-101."""

    with BuildPart() as cart:
        add(Location((0, 0, CART_CRADLE_BOTTOM_Z)) * _cradle_segment_part())

        with Locations(
            (
                0.0,
                CART_DECK_CENTER_Y,
                (CART_DECK_TOP_Z + CART_DECK_BOTTOM_Z) / 2,
            )
        ):
            Box(CART_DECK_WIDTH, CART_DECK_LENGTH, CART_DECK_THICKNESS)

        for side in [-1, 1]:
            with Locations(
                (
                    side * CART_CHEEK_X,
                    CART_WHEEL_CENTER_Y,
                    CART_CHEEK_CENTER_Z,
                )
            ):
                Box(
                    CART_CHEEK_THICKNESS,
                    CART_CHEEK_LENGTH,
                    CART_CHEEK_HEIGHT,
                )

            with Locations(
                (
                    side * CART_CHEEK_X,
                    CART_WHEEL_CENTER_Y,
                    CART_AXLE_Z,
                )
            ):
                Cylinder(
                    CART_AXLE_RADIUS + 0.2,
                    CART_CHEEK_THICKNESS * 4,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )

            _add_cart_magnet_pocket(side)

    return tag(
        cart.part,
        "SO-101 cart magnetic dock body",
        PRINTED_FRAME,
    )


def make_so101_cart_wheel():
    """Simple printable cart wheel with central M5 axle clearance bore."""

    with BuildPart() as wheel:
        Cylinder(CART_WHEEL_RADIUS, CART_WHEEL_TIRE_WIDTH, rotation=(90, 0, 0))
        Cylinder(CART_WHEEL_HUB_RADIUS, CART_WHEEL_HUB_WIDTH, rotation=(90, 0, 0))
        Cylinder(
            CART_WHEEL_BORE_RADIUS,
            CART_WHEEL_HUB_WIDTH + 4.0,
            rotation=(90, 0, 0),
            mode=Mode.SUBTRACT,
        )

    return tag(wheel.part, "SO-101 cart printed wheel", TPU_BLACK)


def place_cart_wheel(side: int):
    wheel = make_so101_cart_wheel()
    placed = Location(
        (
            side * CART_WHEEL_CENTER_X,
            CART_WHEEL_CENTER_Y,
            CART_AXLE_Z,
        )
    ) * wheel
    label = "right SO-101 cart wheel" if side > 0 else "left SO-101 cart wheel"
    return tag(placed, label, TPU_BLACK)


def place_cart_axle():
    axle = Location(
        (0, CART_WHEEL_CENTER_Y, CART_AXLE_Z),
        (0, 90, 0),
    ) * Cylinder(CART_AXLE_RADIUS, CART_AXLE_LENGTH)
    return tag(axle, "M5 cart axle reference", SILVER)


def place_cart_dock_magnet(side: int):
    base = _cart_dock_magnet_radial_location(side)
    magnet_local_offset = Location(
        (LID_DOCK_MAGNET_THICKNESS / 2, 0, 0)
    )
    placed = (
        base
        * magnet_local_offset
        * Cylinder(
            LID_DOCK_MAGNET_RADIUS,
            LID_DOCK_MAGNET_THICKNESS,
            rotation=(0, 90, 0),
        )
    )
    label = (
        "right cart dock magnet" if side > 0 else "left cart dock magnet"
    )
    return tag(placed, label, BLACK)


def place_so101_arm():
    arm = SO_ARM_101_ASSEMBLY.load()
    placed = Location(
        (CART_ARM_BASE_X, CART_ARM_BASE_Y, CART_ARM_BASE_Z),
        (0, 0, 0),
    ) * arm
    return tag(placed, "SO-101 follower arm reference", SILVER)


def make_so101_cart():
    """Cart-only reference assembly (deck, wheels, axle, magnets, arm)."""

    children: list = [
        make_so101_cart_deck(),
        place_cart_axle(),
        place_so101_arm(),
    ]
    for side in [-1, 1]:
        children.append(place_cart_wheel(side))
        children.append(place_cart_dock_magnet(side))

    return Compound(children=children, label="so101-cart")


def make_flat_disk_robot_with_cart():
    """Flat disk robot docked to the cart that carries the SO-101."""

    cart_children: list = [
        make_so101_cart_deck(),
        place_cart_axle(),
        place_so101_arm(),
    ]
    for side in [-1, 1]:
        cart_children.append(place_cart_wheel(side))
        cart_children.append(place_cart_dock_magnet(side))

    children: list = [make_flat_disk_robot(), *cart_children]
    return Compound(children=children, label="flat-disk-robot-with-cart")
