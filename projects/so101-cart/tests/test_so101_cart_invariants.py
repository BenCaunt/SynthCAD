from math import cos, hypot, radians, sin

import pytest
from build123d import Box, Cylinder, Location

from synthcad.inspection import bounding_box_summary
from synthcad.projects.flat_disk_robot.robot import (
    LID_DOCK_MAGNET_CENTER_Z,
    LID_DOCK_MAGNET_POCKET_DEPTH,
    LID_DOCK_MAGNET_POCKET_RADIUS,
    LID_DOCK_MAGNET_THICKNESS,
    LID_TOP_SURFACE_Z,
    LID_WALL_BOTTOM_Z,
    ROBOT_RADIUS,
    lid_dock_magnet_theta_deg,
    place_lid_dock_magnet,
)
from synthcad.projects.so101_cart.cart import (
    CART_AXLE_Z,
    CART_CRADLE_BOTTOM_Z,
    CART_CRADLE_HEIGHT,
    CART_CRADLE_INNER_RADIUS,
    CART_CRADLE_OUTER_RADIUS,
    CART_CRADLE_TOP_Z,
    CART_DECK_BOTTOM_Z,
    CART_DECK_LENGTH,
    CART_DECK_REAR_Y,
    CART_DECK_THICKNESS,
    CART_DECK_TOP_Z,
    CART_DECK_WIDTH,
    CART_DOCK_GAP,
    CART_WHEEL_CENTER_X,
    CART_WHEEL_CENTER_Y,
    CART_WHEEL_RADIUS,
    make_flat_disk_robot_with_cart,
    make_so101_cart,
    make_so101_cart_deck,
    make_so101_cart_wheel,
    place_cart_dock_magnet,
)


def test_cart_cradle_wraps_disk_robot_with_a_small_clearance_gap() -> None:
    assert CART_CRADLE_INNER_RADIUS == pytest.approx(
        ROBOT_RADIUS + CART_DOCK_GAP,
        abs=1e-6,
    )
    assert CART_CRADLE_OUTER_RADIUS > CART_CRADLE_INNER_RADIUS
    assert CART_CRADLE_BOTTOM_Z == pytest.approx(LID_WALL_BOTTOM_Z, abs=1e-6)
    assert CART_CRADLE_TOP_Z == pytest.approx(LID_TOP_SURFACE_Z, abs=1e-6)
    assert CART_CRADLE_HEIGHT == pytest.approx(
        CART_CRADLE_TOP_Z - CART_CRADLE_BOTTOM_Z,
        abs=1e-6,
    )


def test_cart_deck_sits_above_wheels_and_is_long_enough_for_so101_base() -> None:
    assert CART_DECK_TOP_Z == pytest.approx(LID_TOP_SURFACE_Z, abs=1e-6)
    assert CART_DECK_BOTTOM_Z == pytest.approx(
        CART_DECK_TOP_Z - CART_DECK_THICKNESS,
        abs=1e-6,
    )
    # Wheels are passive; their contact point is at Z = 0.
    assert CART_WHEEL_RADIUS == pytest.approx(CART_AXLE_Z, abs=1e-6)
    assert CART_WHEEL_CENTER_Y > CART_DECK_REAR_Y
    assert CART_WHEEL_CENTER_X > CART_DECK_WIDTH / 2

    # A typical SO-101 base footprint is ~110 mm; the deck must be at least
    # that wide and considerably longer.
    assert CART_DECK_WIDTH >= 110.0
    assert CART_DECK_LENGTH >= 200.0


def test_cart_deck_builds_with_pockets_aligned_to_lid_magnets() -> None:
    deck = make_so101_cart_deck()
    bbox = bounding_box_summary(deck)

    # Deck sits between Z = 0 (wheel ground) and the disk-robot lid roof.
    assert bbox["min"][2] == pytest.approx(0.0, abs=1e-6)
    assert bbox["max"][2] == pytest.approx(LID_TOP_SURFACE_Z, abs=1e-6)

    # Probe each pocket along the radial axis: the pocket interior is empty.
    for side in (-1, 1):
        theta_deg = lid_dock_magnet_theta_deg(side)
        theta_rad = radians(theta_deg)
        pocket_center_radial = (
            CART_CRADLE_INNER_RADIUS + LID_DOCK_MAGNET_POCKET_DEPTH / 2
        )
        cx = pocket_center_radial * cos(theta_rad)
        cy = pocket_center_radial * sin(theta_rad)
        probe = Location(
            (cx, cy, LID_DOCK_MAGNET_CENTER_Z),
            (0, 0, theta_deg),
        ) * Cylinder(
            LID_DOCK_MAGNET_POCKET_RADIUS - 0.2,
            LID_DOCK_MAGNET_POCKET_DEPTH - 0.4,
            rotation=(0, 90, 0),
        )
        common = deck.intersect(probe)
        volume = float(common.volume) if common.solids() else 0.0
        assert volume == pytest.approx(0.0, abs=1e-6)


def test_cart_dock_magnet_faces_align_with_lid_dock_magnet_faces() -> None:
    """The cart magnet's inward face must sit a small dock gap from the lid magnet face."""

    for side in (-1, 1):
        lid_magnet = place_lid_dock_magnet(side)
        cart_magnet = place_cart_dock_magnet(side)

        lid_bbox = bounding_box_summary(lid_magnet)
        cart_bbox = bounding_box_summary(cart_magnet)

        lid_center = lid_bbox["center"][:2]
        cart_center = cart_bbox["center"][:2]

        # Both magnet centers lie on the same radial line (their angles match).
        lid_theta = lid_dock_magnet_theta_deg(side)
        expected = (cos(radians(lid_theta)), sin(radians(lid_theta)))

        lid_norm = hypot(*lid_center)
        cart_norm = hypot(*cart_center)
        assert (
            lid_center[0] / lid_norm,
            lid_center[1] / lid_norm,
        ) == pytest.approx(expected, abs=1e-3)
        assert (
            cart_center[0] / cart_norm,
            cart_center[1] / cart_norm,
        ) == pytest.approx(expected, abs=1e-3)

        # Distance between the two magnet pole faces equals the dock gap.
        lid_face_radial = lid_norm + LID_DOCK_MAGNET_THICKNESS / 2
        cart_face_radial = cart_norm - LID_DOCK_MAGNET_THICKNESS / 2
        assert lid_face_radial == pytest.approx(ROBOT_RADIUS, abs=1e-3)
        assert cart_face_radial - lid_face_radial == pytest.approx(
            CART_DOCK_GAP,
            abs=1e-3,
        )


def test_cart_wheel_envelope_matches_radius_parameter() -> None:
    wheel = make_so101_cart_wheel()
    bbox = bounding_box_summary(wheel)
    assert bbox["size"][0] == pytest.approx(2 * CART_WHEEL_RADIUS, abs=1e-6)
    assert bbox["size"][2] == pytest.approx(2 * CART_WHEEL_RADIUS, abs=1e-6)


def test_cart_assembly_includes_all_expected_children() -> None:
    cart = make_so101_cart()
    labels = {child.label for child in cart.children}
    assert "SO-101 cart magnetic dock body" in labels
    assert "SO-101 follower arm reference" in labels
    assert "right SO-101 cart wheel" in labels
    assert "left SO-101 cart wheel" in labels
    assert "right cart dock magnet" in labels
    assert "left cart dock magnet" in labels
    assert "M5 cart axle reference" in labels


def test_docked_assembly_keeps_cart_behind_disk_robot() -> None:
    docked = make_flat_disk_robot_with_cart()
    bbox = bounding_box_summary(docked)

    # +Y bound stays at the disk-robot front; the cart only extends rearward.
    assert bbox["max"][1] == pytest.approx(ROBOT_RADIUS, abs=0.5)
    assert bbox["min"][1] < CART_DECK_REAR_Y + 1.0
