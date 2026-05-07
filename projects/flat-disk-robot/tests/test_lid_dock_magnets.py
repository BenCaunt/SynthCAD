from math import cos, hypot, radians, sin

import pytest
from build123d import Box, Cylinder, Location

from synthcad.inspection import bounding_box_summary
from synthcad.projects.flat_disk_robot.robot import (
    LID_DOCK_MAGNET_BOSS_DEPTH,
    LID_DOCK_MAGNET_BOSS_OUTER_INSET,
    LID_DOCK_MAGNET_BOSS_RADIUS,
    LID_DOCK_MAGNET_CENTER_Z,
    LID_DOCK_MAGNET_DIAMETER,
    LID_DOCK_MAGNET_POCKET_DEPTH,
    LID_DOCK_MAGNET_POCKET_RADIAL_CLEARANCE,
    LID_DOCK_MAGNET_POCKET_RADIUS,
    LID_DOCK_MAGNET_RADIUS,
    LID_DOCK_MAGNET_THICKNESS,
    LID_DOCK_MAGNET_X_OFFSET,
    LID_DOCK_MAGNET_Y_OUTER,
    LID_TOP_UNDERSIDE_Z,
    LID_WALL_BOTTOM_Z,
    PERIMETER_WALL_THICKNESS,
    REAR_SERVICE_OPENING_WIDTH,
    ROBOT_DIAMETER,
    ROBOT_RADIUS,
    lid_dock_magnet_outer_face_location,
    lid_dock_magnet_theta_deg,
    make_flat_disk_robot_lid,
    place_lid_dock_magnet,
)


def _radial_distance_xy(point) -> float:
    return hypot(point[0], point[1])


def test_lid_dock_magnet_geometry_is_consistent() -> None:
    assert LID_DOCK_MAGNET_DIAMETER == pytest.approx(12.0, abs=1e-6)
    assert LID_DOCK_MAGNET_RADIUS == pytest.approx(6.0, abs=1e-6)
    assert LID_DOCK_MAGNET_THICKNESS == pytest.approx(5.0, abs=1e-6)
    assert LID_DOCK_MAGNET_POCKET_RADIUS == pytest.approx(
        LID_DOCK_MAGNET_RADIUS + LID_DOCK_MAGNET_POCKET_RADIAL_CLEARANCE,
        abs=1e-6,
    )
    assert LID_DOCK_MAGNET_POCKET_DEPTH > LID_DOCK_MAGNET_THICKNESS
    assert LID_DOCK_MAGNET_BOSS_DEPTH > LID_DOCK_MAGNET_POCKET_DEPTH
    assert LID_DOCK_MAGNET_BOSS_RADIUS > LID_DOCK_MAGNET_POCKET_RADIUS

    assert LID_DOCK_MAGNET_X_OFFSET > REAR_SERVICE_OPENING_WIDTH / 2
    assert LID_DOCK_MAGNET_Y_OUTER < 0
    assert LID_DOCK_MAGNET_CENTER_Z > LID_WALL_BOTTOM_Z
    assert LID_DOCK_MAGNET_CENTER_Z < LID_TOP_UNDERSIDE_Z


def test_lid_dock_magnets_are_mirrored_about_y_axis() -> None:
    right_loc = lid_dock_magnet_outer_face_location(1)
    left_loc = lid_dock_magnet_outer_face_location(-1)

    rx, ry, rz = right_loc.position
    lx, ly, lz = left_loc.position

    assert rx == pytest.approx(-lx, abs=1e-6)
    assert ry == pytest.approx(ly, abs=1e-6)
    assert rz == pytest.approx(lz, abs=1e-6)
    assert rx == pytest.approx(LID_DOCK_MAGNET_X_OFFSET, abs=1e-6)
    assert ry == pytest.approx(LID_DOCK_MAGNET_Y_OUTER, abs=1e-6)

    # Outer face of the magnet sits exactly on the lid outer cylinder.
    assert _radial_distance_xy((rx, ry)) == pytest.approx(ROBOT_RADIUS, abs=1e-6)
    assert _radial_distance_xy((lx, ly)) == pytest.approx(ROBOT_RADIUS, abs=1e-6)


def test_lid_dock_magnet_bosses_keep_lid_inside_disk_envelope() -> None:
    """Inward-pointing bosses must not push the lid past the 216 mm envelope."""

    bbox = bounding_box_summary(make_flat_disk_robot_lid())
    assert bbox["size"][:2] == pytest.approx(
        (ROBOT_DIAMETER, ROBOT_DIAMETER),
        abs=0.1,
    )

    # Sanity-check the geometric reason: the worst-case radial extent of the
    # cylindrical boss is well under ROBOT_RADIUS.
    worst_case_radial = (
        (ROBOT_RADIUS - LID_DOCK_MAGNET_BOSS_OUTER_INSET) ** 2
        + LID_DOCK_MAGNET_BOSS_RADIUS**2
    ) ** 0.5
    assert worst_case_radial < ROBOT_RADIUS


def test_lid_dock_magnet_pockets_are_actually_cut_into_the_lid() -> None:
    lid = make_flat_disk_robot_lid()

    for side in (-1, 1):
        theta_rad = radians(lid_dock_magnet_theta_deg(side))
        # Probe the middle of the pocket along the radial axis.
        pocket_center_radial = ROBOT_RADIUS - LID_DOCK_MAGNET_POCKET_DEPTH / 2
        cx = pocket_center_radial * cos(theta_rad)
        cy = pocket_center_radial * sin(theta_rad)

        probe = Location(
            (cx, cy, LID_DOCK_MAGNET_CENTER_Z),
            (0, 0, lid_dock_magnet_theta_deg(side)),
        ) * Cylinder(
            LID_DOCK_MAGNET_POCKET_RADIUS - 0.2,
            LID_DOCK_MAGNET_POCKET_DEPTH - 0.4,
            rotation=(0, 90, 0),
        )
        common = lid.intersect(probe)
        volume = float(common.volume) if common.solids() else 0.0

        assert volume == pytest.approx(0.0, abs=1e-6)


def test_lid_dock_magnet_bosses_add_supporting_material_around_the_pocket() -> None:
    lid = make_flat_disk_robot_lid()

    for side in (-1, 1):
        # Cylindrical shell just outside the pocket but still inside the boss.
        theta_deg = lid_dock_magnet_theta_deg(side)
        theta_rad = radians(theta_deg)
        ring_center_radial = ROBOT_RADIUS - LID_DOCK_MAGNET_POCKET_DEPTH / 2
        cx = ring_center_radial * cos(theta_rad)
        cy = ring_center_radial * sin(theta_rad)

        outer_probe = Location(
            (cx, cy, LID_DOCK_MAGNET_CENTER_Z),
            (0, 0, theta_deg),
        ) * Cylinder(
            LID_DOCK_MAGNET_POCKET_RADIUS + 1.0,
            LID_DOCK_MAGNET_POCKET_DEPTH - 0.4,
            rotation=(0, 90, 0),
        )
        common = lid.intersect(outer_probe)
        volume = float(common.volume) if common.solids() else 0.0

        # The annular boss material should clearly contribute volume.
        assert volume > 5.0


def test_lid_dock_magnet_bosses_clear_rear_service_opening() -> None:
    # The rear service opening is a Box centered on the rear arc; the magnet
    # bosses must sit outboard of that opening so they remain solid plastic.
    half_opening = REAR_SERVICE_OPENING_WIDTH / 2
    boss_outer_x = LID_DOCK_MAGNET_X_OFFSET - LID_DOCK_MAGNET_BOSS_RADIUS
    assert boss_outer_x > half_opening + PERIMETER_WALL_THICKNESS


def test_place_lid_dock_magnet_produces_disc_geometry_at_lid_outer_face() -> None:
    for side in (-1, 1):
        magnet = place_lid_dock_magnet(side)
        bbox = bounding_box_summary(magnet)
        assert bbox["size"][2] == pytest.approx(
            LID_DOCK_MAGNET_DIAMETER,
            abs=1e-6,
        )

        # The magnet's outer face sits flush with the lid outer cylinder.
        cx, cy, _ = bbox["center"]
        face_pull_in = LID_DOCK_MAGNET_THICKNESS / 2
        outer_radial = _radial_distance_xy((cx, cy)) + face_pull_in
        assert outer_radial == pytest.approx(ROBOT_RADIUS, abs=1e-3)
