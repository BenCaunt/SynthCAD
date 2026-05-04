from math import hypot

import pytest
from build123d import (
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Location,
    Plane,
    Text,
    extrude,
)

from synthcad.cad.features import candidate_circular_holes
from synthcad.inspection import bounding_box_summary
from synthcad.library.repeat_drive import (
    MOTOR_BOLT_CIRCLE_RADIUS,
    WHEEL_HUB_WIDTH,
    WHEEL_RADIUS,
    WHEEL_SCREW_ACCESS_RADIUS,
    make_tpu_d_bore_wheel,
    motor_bolt_circle_offsets,
)
from synthcad.projects.flat_disk_robot.robot import (
    ENCODER_MOUNT_PLATE_THICKNESS,
    ENCODER_MOUNT_PLATE_WIDTH,
    ENCODER_MOUNT_PLATE_BOTTOM_Z,
    ENCODER_MOUNT_PLATE_TOP_Z,
    FRONT_SENSOR_OPENING_DEPTH,
    FRONT_SENSOR_OPENING_EFFECTIVE_WIDTH,
    FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE,
    FRONT_SENSOR_OPENING_WIDTH,
    LID_LOGO_BLOCK_ALIGN,
    LID_LOGO_CENTER,
    LID_LOGO_ENGRAVE_DEPTH,
    LID_LOGO_TEXT,
    LID_LOGO_TEXT_ALIGN,
    LID_LOGO_TEXT_LINES,
    LID_LOGO_TEXT_SIZE,
    LID_MOUNT_POINTS,
    LID_FRONT_WALL_OPENING_DEPTH,
    LID_SHELL_WALL_THICKNESS,
    LID_SWITCH_CUTOUT_CENTER,
    LID_SWITCH_CUTOUT_SIZE,
    LID_SIDE_ACCESS_OPENING_CENTER_X,
    LID_SIDE_ACCESS_OPENING_CENTER_Y,
    LID_SIDE_ACCESS_OPENING_LENGTH,
    LID_SIDE_ACCESS_OPENING_WIDTH,
    LID_TOP_CENTER_Z,
    LID_TOP_SURFACE_Z,
    LID_TOP_THICKNESS,
    LID_VENT_HOLE_COUNT,
    LID_VENT_HOLE_RADIUS,
    LID_VENT_RING_RADIUS,
    LID_WALL_BOTTOM_Z,
    LID_WALL_CENTER_Z,
    LID_WALL_HEIGHT,
    LID_WHEEL_WELL_CUTOUT_HEIGHT,
    LID_WHEEL_WELL_CUTOUT_LENGTH,
    LID_WHEEL_WELL_CUTOUT_WIDTH,
    LID_WHEEL_WELL_CUTOUT_Z_MAX,
    LID_WHEEL_WELL_CUTOUT_Z_MIN,
    M4_CLEARANCE_RADIUS,
    M4_SOCKET_HEAD_RADIUS,
    CAMERA_MOUNT_BACK_FACE_Y,
    CAMERA_MOUNT_FRONT_FACE_Y,
    CAMERA_MOUNT_THICKNESS,
    MOTOR_DRIVER_ACCESS_RADIUS,
    OV2640_CAMERA_BODY_CLEARANCE_HALF_SIZE,
    OV2640_CAMERA_BODY_HALF_SIZE,
    OV2640_CAMERA_BODY_SOCKET_ENGAGEMENT,
    OV2640_CAMERA_BODY_SOCKET_DEPTH,
    OV2640_CAMERA_CENTER,
    OV2640_CAMERA_LENS_CLEARANCE_RADIUS,
    OV2640_CAMERA_LENS_RADIUS,
    OV2640_CAMERA_LOCAL_BODY_FRONT_Y,
    OV2640_CAMERA_LOCAL_LENS_FRONT_Y,
    OV2640_CAMERA_LENS_CENTER_X,
    OV2640_CAMERA_LENS_CENTER_Z,
    PERIMETER_WALL_HEIGHT,
    PERIMETER_WALL_THICKNESS,
    ROBOT_AXLE_Y,
    ROBOT_AXLE_Z,
    ROBOT_CHASSIS_THICKNESS,
    ROBOT_DIAMETER,
    ROBOT_RADIUS,
    ROBOT_WHEEL_CENTER_X,
    ROBOT_WHEEL_GROUND_PROTRUSION,
    ROBOT_WHEEL_RADIUS,
    TOF_BOSS_LENGTH,
    TOF_PLASTIC_THREAD_HOLE_RADIUS,
    TOF_STANDOFF_EXTENSION,
    WHEEL_SLOT_CLEARANCE_Y,
    WHEEL_SLOT_SIZE,
    _make_encoder_mount,
    _motor_driver_access_center_x,
    _motor_driver_access_tunnel_length,
    make_flat_disk_robot_chassis,
    make_flat_disk_robot_lid,
    place_ov2640_camera,
    place_small_4s_battery,
    place_wheel_on_x_axis,
)


def test_tpu_wheel_envelope_matches_radius_parameter() -> None:
    wheel = make_tpu_d_bore_wheel(radius=30.0)
    bbox = bounding_box_summary(wheel)
    assert bbox["size"] == pytest.approx((60.0, WHEEL_HUB_WIDTH, 60.0), abs=1e-6)


def test_tpu_wheel_volume_increases_with_radius() -> None:
    small = make_tpu_d_bore_wheel(radius=18.0)
    large = make_tpu_d_bore_wheel(radius=28.0)
    assert float(large.volume) > float(small.volume)


def test_flat_disk_robot_uses_larger_drive_wheels_with_matching_slot_clearance() -> None:
    assert ROBOT_WHEEL_GROUND_PROTRUSION == pytest.approx(3.5, abs=1e-6)
    assert ROBOT_WHEEL_RADIUS == pytest.approx(WHEEL_RADIUS + 3.5, abs=1e-6)
    assert 2 * ROBOT_WHEEL_RADIUS == pytest.approx(51.0, abs=1e-6)
    assert WHEEL_SLOT_SIZE[1] == pytest.approx(
        2 * ROBOT_WHEEL_RADIUS + WHEEL_SLOT_CLEARANCE_Y,
        abs=1e-6,
    )

    wheel_bbox = bounding_box_summary(place_wheel_on_x_axis(1))

    assert wheel_bbox["size"] == pytest.approx(
        (WHEEL_HUB_WIDTH, 51.0, 51.0),
        abs=0.1,
    )


def test_motor_bolt_circle_offsets_stay_on_nominal_circle() -> None:
    for x_offset, z_offset in motor_bolt_circle_offsets():
        assert hypot(x_offset, z_offset) == pytest.approx(MOTOR_BOLT_CIRCLE_RADIUS, abs=1e-6)


def test_flat_disk_robot_lid_matches_chassis_disk_envelope_in_plan() -> None:
    lid_bbox = bounding_box_summary(make_flat_disk_robot_lid())
    chassis_bbox = bounding_box_summary(make_flat_disk_robot_chassis())

    assert lid_bbox["size"][:2] == pytest.approx(
        (ROBOT_DIAMETER, ROBOT_DIAMETER),
        abs=0.1,
    )
    assert lid_bbox["size"][:2] == pytest.approx(chassis_bbox["size"][:2], abs=0.1)


def test_flat_disk_robot_front_sensor_opening_clears_chassis_and_lid() -> None:
    assert FRONT_SENSOR_OPENING_WIDTH == pytest.approx(144.0, abs=1e-6)
    assert FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE == pytest.approx(25.4, abs=1e-6)
    assert FRONT_SENSOR_OPENING_EFFECTIVE_WIDTH == pytest.approx(129.89, abs=0.01)

    previous_half_width = (
        FRONT_SENSOR_OPENING_EFFECTIVE_WIDTH / 2
        - FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE
    )
    side_probe_width = FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE - 1.0

    chassis = make_flat_disk_robot_chassis()
    for side in (-1, 1):
        chassis_probe = Location(
            (
                side * (previous_half_width + side_probe_width / 2),
                ROBOT_RADIUS - PERIMETER_WALL_THICKNESS / 2,
                ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT / 2,
            )
        ) * Box(
            side_probe_width,
            FRONT_SENSOR_OPENING_DEPTH - 1.0,
            PERIMETER_WALL_HEIGHT - 1.0,
        )
        chassis_common = chassis.intersect(chassis_probe)
        chassis_volume = float(chassis_common.volume) if chassis_common.solids() else 0.0
        assert chassis_volume == pytest.approx(0.0, abs=1e-6)

    lid = make_flat_disk_robot_lid()
    for side in (-1, 1):
        lid_probe = Location(
            (
                side * (previous_half_width + side_probe_width / 2),
                ROBOT_RADIUS - LID_SHELL_WALL_THICKNESS / 2,
                LID_WALL_CENTER_Z,
            )
        ) * Box(
            side_probe_width,
            LID_FRONT_WALL_OPENING_DEPTH - 1.0,
            LID_WALL_HEIGHT - 0.5,
        )
        lid_common = lid.intersect(lid_probe)
        lid_volume = float(lid_common.volume) if lid_common.solids() else 0.0
        assert lid_volume == pytest.approx(0.0, abs=1e-6)


def test_flat_disk_robot_lid_adds_visible_circular_vent_pattern() -> None:
    lid = make_flat_disk_robot_lid()
    vent_holes = [
        hole
        for hole in candidate_circular_holes(
            lid,
            radius_min=LID_VENT_HOLE_RADIUS - 0.2,
            radius_max=LID_VENT_HOLE_RADIUS + 0.2,
            center_axes=("X", "Y"),
        )
        if hypot(hole.center[0], hole.center[1]) == pytest.approx(LID_VENT_RING_RADIUS, abs=0.5)
    ]

    assert len(vent_holes) == LID_VENT_HOLE_COUNT


def test_flat_disk_robot_lid_adds_switch_press_fit_cutout() -> None:
    lid = make_flat_disk_robot_lid()
    probe = Location(
        (LID_SWITCH_CUTOUT_CENTER[0], LID_SWITCH_CUTOUT_CENTER[1], LID_TOP_CENTER_Z)
    ) * Box(
        LID_SWITCH_CUTOUT_SIZE[0] - 0.4,
        LID_SWITCH_CUTOUT_SIZE[1] - 0.4,
        LID_TOP_THICKNESS + 2.0,
    )
    common = lid.intersect(probe)
    volume = float(common.volume) if common.solids() else 0.0

    assert volume == pytest.approx(0.0, abs=1e-6)


def test_flat_disk_robot_lid_adds_recessed_top_logo() -> None:
    assert LID_LOGO_TEXT_LINES == ("Designed by GPT-5.4 xhigh with build123d",)
    assert LID_LOGO_TEXT_SIZE == pytest.approx(8.0, abs=1e-6)

    lid = make_flat_disk_robot_lid()
    with BuildPart() as lettering_probe:
        with BuildSketch(Plane.XY):
            Text(
                LID_LOGO_TEXT,
                LID_LOGO_TEXT_SIZE,
                text_align=LID_LOGO_TEXT_ALIGN,
                align=LID_LOGO_BLOCK_ALIGN,
            )
        extrude(amount=LID_LOGO_ENGRAVE_DEPTH - 0.1)

    probe = Location(
        (
            LID_LOGO_CENTER[0],
            LID_LOGO_CENTER[1],
            LID_TOP_SURFACE_Z - LID_LOGO_ENGRAVE_DEPTH + 0.05,
        )
    ) * lettering_probe.part
    common = lid.intersect(probe)
    volume = float(common.volume) if common.solids() else 0.0

    assert volume == pytest.approx(0.0, abs=1e-6)


def test_flat_disk_robot_lid_switch_cutout_stays_clear_of_battery_plan_area() -> None:
    battery_bbox = bounding_box_summary(place_small_4s_battery())
    switch_rear_y = LID_SWITCH_CUTOUT_CENTER[1] - LID_SWITCH_CUTOUT_SIZE[1] / 2

    assert switch_rear_y > battery_bbox["max"][1] + 5.0


def test_flat_disk_robot_lid_side_skirt_meets_chassis_wall_top() -> None:
    assert LID_WALL_BOTTOM_Z == pytest.approx(
        ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT,
        abs=1e-6,
    )


def test_flat_disk_robot_lid_side_wheel_wells_clear_larger_wheels() -> None:
    lid = make_flat_disk_robot_lid()

    for side in (-1, 1):
        wheel_well_probe = Location(
            (
                side * ROBOT_WHEEL_CENTER_X,
                ROBOT_AXLE_Y,
                ROBOT_AXLE_Z,
            )
        ) * Box(
            WHEEL_HUB_WIDTH - 1.0,
            2 * ROBOT_WHEEL_RADIUS - 1.0,
            2 * ROBOT_WHEEL_RADIUS - 1.0,
        )
        common = lid.intersect(wheel_well_probe)
        volume = float(common.volume) if common.solids() else 0.0

        assert volume == pytest.approx(0.0, abs=1e-6)

        assert abs(side * ROBOT_WHEEL_CENTER_X - side * LID_SIDE_ACCESS_OPENING_CENTER_X) < (
            LID_SIDE_ACCESS_OPENING_WIDTH - WHEEL_HUB_WIDTH
        ) / 2
        assert abs(ROBOT_AXLE_Y - LID_SIDE_ACCESS_OPENING_CENTER_Y) < (
            LID_SIDE_ACCESS_OPENING_LENGTH - 2 * ROBOT_WHEEL_RADIUS
        ) / 2
        assert LID_WHEEL_WELL_CUTOUT_WIDTH > WHEEL_HUB_WIDTH
        assert LID_WHEEL_WELL_CUTOUT_LENGTH > 2 * ROBOT_WHEEL_RADIUS
        assert LID_WHEEL_WELL_CUTOUT_Z_MIN < ROBOT_AXLE_Z + ROBOT_WHEEL_RADIUS
        assert LID_WHEEL_WELL_CUTOUT_Z_MAX > ROBOT_AXLE_Z + ROBOT_WHEEL_RADIUS
        assert LID_WHEEL_WELL_CUTOUT_HEIGHT == pytest.approx(
            LID_WHEEL_WELL_CUTOUT_Z_MAX - LID_WHEEL_WELL_CUTOUT_Z_MIN,
            abs=1e-6,
        )



def test_flat_disk_robot_lid_captures_m4_screw_heads_at_roof_surface() -> None:
    lid = make_flat_disk_robot_lid()

    for x, y in LID_MOUNT_POINTS:
        shank_probe = Location((x, y, LID_TOP_CENTER_Z)) * Cylinder(
            M4_CLEARANCE_RADIUS - 0.2,
            LID_TOP_THICKNESS + 1.0,
        )
        shank_common = lid.intersect(shank_probe)
        shank_volume = float(shank_common.volume) if shank_common.solids() else 0.0
        assert shank_volume == pytest.approx(0.0, abs=1e-6)

        head_capture_probe = Location((x, y, LID_TOP_CENTER_Z)) * Cylinder(
            M4_SOCKET_HEAD_RADIUS - 0.2,
            LID_TOP_THICKNESS + 0.5,
        )
        head_capture_common = lid.intersect(head_capture_probe)
        head_capture_volume = (
            float(head_capture_common.volume) if head_capture_common.solids() else 0.0
        )
        assert head_capture_volume > 1.0



def test_flat_disk_robot_chassis_adds_motor_driver_service_tunnels() -> None:
    assert MOTOR_DRIVER_ACCESS_RADIUS == pytest.approx(WHEEL_SCREW_ACCESS_RADIUS, abs=1e-6)

    chassis = make_flat_disk_robot_chassis()

    for side in (-1, 1):
        for y_offset, z_offset in motor_bolt_circle_offsets():
            probe = Location(
                (
                    _motor_driver_access_center_x(side),
                    ROBOT_AXLE_Y + y_offset,
                    ROBOT_AXLE_Z + z_offset,
                )
            ) * Cylinder(
                MOTOR_DRIVER_ACCESS_RADIUS - 0.2,
                _motor_driver_access_tunnel_length() - 0.5,
                rotation=(0, 90, 0),
            )
            common = chassis.intersect(probe)
            volume = float(common.volume) if common.solids() else 0.0

            assert volume == pytest.approx(0.0, abs=1e-6)


def test_flat_disk_robot_tof_bosses_are_extended_for_connector_clearance() -> None:
    assert TOF_STANDOFF_EXTENSION == pytest.approx(3.0, abs=1e-6)
    assert TOF_BOSS_LENGTH > 10.0
    assert TOF_PLASTIC_THREAD_HOLE_RADIUS == pytest.approx(1.55, abs=1e-6)


def test_flat_disk_robot_ov2640_mount_matches_wider_lens_profile() -> None:
    assert OV2640_CAMERA_LENS_RADIUS > OV2640_CAMERA_BODY_HALF_SIZE
    assert OV2640_CAMERA_LENS_CLEARANCE_RADIUS == pytest.approx(
        OV2640_CAMERA_LENS_RADIUS + 0.15,
        abs=1e-6,
    )
    assert OV2640_CAMERA_BODY_CLEARANCE_HALF_SIZE == pytest.approx(
        OV2640_CAMERA_BODY_HALF_SIZE + 0.15,
        abs=1e-6,
    )
    assert CAMERA_MOUNT_THICKNESS == pytest.approx(
        OV2640_CAMERA_LOCAL_LENS_FRONT_Y - OV2640_CAMERA_LOCAL_BODY_FRONT_Y,
        abs=1e-6,
    )
    assert CAMERA_MOUNT_FRONT_FACE_Y < ROBOT_RADIUS
    assert CAMERA_MOUNT_FRONT_FACE_Y > ROBOT_RADIUS - 1.0
    assert OV2640_CAMERA_CENTER[1] + OV2640_CAMERA_LOCAL_LENS_FRONT_Y < ROBOT_RADIUS
    assert OV2640_CAMERA_CENTER[1] + OV2640_CAMERA_LOCAL_BODY_FRONT_Y > (
        CAMERA_MOUNT_BACK_FACE_Y
    )
    assert OV2640_CAMERA_CENTER[1] + OV2640_CAMERA_LOCAL_BODY_FRONT_Y < (
        CAMERA_MOUNT_BACK_FACE_Y + OV2640_CAMERA_BODY_SOCKET_DEPTH
    )
    assert OV2640_CAMERA_CENTER[1] + OV2640_CAMERA_LOCAL_BODY_FRONT_Y == pytest.approx(
        CAMERA_MOUNT_BACK_FACE_Y + OV2640_CAMERA_BODY_SOCKET_ENGAGEMENT,
        abs=1e-6,
    )

    chassis = make_flat_disk_robot_chassis()
    lens_probe = Location(
        (
            OV2640_CAMERA_LENS_CENTER_X,
            (CAMERA_MOUNT_BACK_FACE_Y + CAMERA_MOUNT_FRONT_FACE_Y) / 2,
            OV2640_CAMERA_LENS_CENTER_Z,
        )
    ) * Cylinder(
        OV2640_CAMERA_LENS_RADIUS,
        CAMERA_MOUNT_THICKNESS - 0.5,
        rotation=(90, 0, 0),
    )
    common = chassis.intersect(lens_probe)
    volume = float(common.volume) if common.solids() else 0.0

    assert volume == pytest.approx(0.0, abs=1e-6)


def test_flat_disk_robot_places_ov2640_camera_inside_disk_envelope() -> None:
    camera_bbox = bounding_box_summary(place_ov2640_camera())

    assert camera_bbox["max"][1] < ROBOT_RADIUS
    assert camera_bbox["size"][0] == pytest.approx(12.5, abs=0.1)
    assert camera_bbox["size"][2] == pytest.approx(21.75, abs=0.1)


def test_flat_disk_robot_encoder_mounts_extend_to_chassis_base_edges() -> None:
    for side in (-1, 1):
        bbox = bounding_box_summary(_make_encoder_mount(side))

        assert bbox["min"][2] == pytest.approx(ENCODER_MOUNT_PLATE_BOTTOM_Z, abs=1e-6)
        assert bbox["max"][2] == pytest.approx(ENCODER_MOUNT_PLATE_TOP_Z, abs=1e-6)
        assert bbox["min"][2] < ROBOT_CHASSIS_THICKNESS
        assert bbox["size"][:2] == pytest.approx(
            (ENCODER_MOUNT_PLATE_THICKNESS, ENCODER_MOUNT_PLATE_WIDTH),
            abs=1e-6,
        )
