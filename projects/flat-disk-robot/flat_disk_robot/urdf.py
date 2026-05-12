from __future__ import annotations

from build123d import Cylinder, Location

from synthcad.cad.common import BLACK, BLUE, COPPER_GOLD, PRINTED_FRAME, SILVER, TPU_BLACK
from flat_disk_robot.external_parts import (
    AS5600_ENCODER,
    OV2640_21MM_160_CAMERA,
    REPEAT_COMPACT_1806,
    XIAO_ESP32S3_SENSE,
)
from flat_disk_robot.batteries import BATTERY_HEIGHT, BATTERY_LENGTH, BATTERY_WIDTH, make_small_4s_battery
from flat_disk_robot.boards import make_tof_sensor_board
from flat_disk_robot.repeat_drive import WHEEL_HUB_WIDTH, make_tpu_d_bore_wheel
from flat_disk_robot.sensors import make_forward_radar_module
import flat_disk_robot.robot as flat_robot
from synthcad.urdf import (
    CollisionSpec,
    JointDynamics,
    JointLimit,
    JointSpec,
    LinkSpec,
    MeshAsset,
    RobotDescription,
    VisualSpec,
    fixed_joint,
    hex_to_rgba,
    inertial_from_bbox,
    inertial_from_box,
    inertial_from_cylinder,
)


CHASSIS_MASS_KG = 0.230
LID_MASS_KG = 0.075
BATTERY_MASS_KG = 0.180
MOTOR_MASS_KG = 0.090
WHEEL_MASS_KG = 0.032
ENCODER_MASS_KG = 0.006
MAGNET_MASS_KG = 0.001
ESP32_MASS_KG = 0.008
OV2640_CAMERA_MASS_KG = 0.004
TOF_MASS_KG = 0.006
RADAR_MASS_KG = 0.004

WHEEL_JOINT_EFFORT_NM = 1.5
WHEEL_JOINT_VELOCITY_RAD_S = 40.0
WHEEL_JOINT_DAMPING = 0.05
WHEEL_JOINT_FRICTION = 0.02


def _encoder_center_x() -> float:
    return (
        flat_robot.ROBOT_MOTOR_REAR_X
        - flat_robot.ENCODER_SENSOR_GAP
        - flat_robot.AS5600_BOARD_THICKNESS / 2
    )


def _magnet_center_x() -> float:
    return flat_robot.ROBOT_MOTOR_REAR_X - flat_robot.ENCODER_MAGNET_THICKNESS / 2


def _base_visual(name: str, asset: MeshAsset, color: str) -> VisualSpec:
    return VisualSpec(mesh=asset, material_name=f"{name}_material", rgba=hex_to_rgba(color))


def _base_collision(asset: MeshAsset) -> CollisionSpec:
    return CollisionSpec(mesh=asset)


def make_flat_disk_robot_urdf() -> RobotDescription:
    chassis_asset = MeshAsset("flat_disk_robot_base_link", flat_robot.make_flat_disk_robot_chassis())
    lid_asset = MeshAsset("flat_disk_robot_lid_link", flat_robot.make_flat_disk_robot_lid())
    battery_asset = MeshAsset("flat_disk_robot_battery", make_small_4s_battery())
    motor_asset = MeshAsset("repeat_compact_1806_motor", REPEAT_COMPACT_1806.load())
    wheel_asset = MeshAsset(
        "repeat_drive_wheel_x_axis",
        Location((0.0, 0.0, 0.0), (0.0, 0.0, 90.0))
        * make_tpu_d_bore_wheel(radius=flat_robot.ROBOT_WHEEL_RADIUS),
    )
    encoder_asset = MeshAsset("as5600_encoder_module", AS5600_ENCODER.load())
    magnet_asset = MeshAsset(
        "encoder_magnet",
        Cylinder(
            flat_robot.ENCODER_MAGNET_RADIUS,
            flat_robot.ENCODER_MAGNET_THICKNESS,
            rotation=(0.0, 90.0, 0.0),
        ),
    )
    esp32_asset = MeshAsset("seeed_xiao_esp32s3_sense", XIAO_ESP32S3_SENSE.load())
    ov2640_camera_asset = MeshAsset("ov2640_21mm_160_camera", OV2640_21MM_160_CAMERA.load())
    tof_asset = MeshAsset("tof_sensor_board", make_tof_sensor_board())
    radar_asset = MeshAsset("forward_radar_module", make_forward_radar_module())

    links: list[LinkSpec] = [
        LinkSpec("base_footprint"),
        LinkSpec(
            name="base_link",
            inertial=inertial_from_bbox(chassis_asset.model, CHASSIS_MASS_KG),
            visual=_base_visual("base_link", chassis_asset, PRINTED_FRAME),
            collision=_base_collision(chassis_asset),
        ),
        LinkSpec(
            name="lid_link",
            inertial=inertial_from_bbox(lid_asset.model, LID_MASS_KG),
            visual=_base_visual("lid_link", lid_asset, PRINTED_FRAME),
            collision=_base_collision(lid_asset),
        ),
        LinkSpec(
            name="battery_link",
            inertial=inertial_from_box(
                mass_kg=BATTERY_MASS_KG,
                size_mm=(BATTERY_LENGTH, BATTERY_WIDTH, BATTERY_HEIGHT),
                xyz_mm=(0.0, 0.0, BATTERY_HEIGHT / 2),
            ),
            visual=_base_visual("battery_link", battery_asset, BLACK),
            collision=_base_collision(battery_asset),
        ),
        LinkSpec(
            name="esp32_link",
            inertial=inertial_from_bbox(esp32_asset.model, ESP32_MASS_KG),
            visual=_base_visual("esp32_link", esp32_asset, BLACK),
            collision=_base_collision(esp32_asset),
        ),
        LinkSpec(
            name="ov2640_camera_link",
            inertial=inertial_from_bbox(ov2640_camera_asset.model, OV2640_CAMERA_MASS_KG),
            visual=_base_visual("ov2640_camera_link", ov2640_camera_asset, BLACK),
            collision=_base_collision(ov2640_camera_asset),
        ),
        LinkSpec(
            name="tof_link",
            inertial=inertial_from_bbox(tof_asset.model, TOF_MASS_KG),
            visual=_base_visual("tof_link", tof_asset, COPPER_GOLD),
            collision=_base_collision(tof_asset),
        ),
        LinkSpec(
            name="radar_link",
            inertial=inertial_from_bbox(radar_asset.model, RADAR_MASS_KG),
            visual=_base_visual("radar_link", radar_asset, COPPER_GOLD),
            collision=_base_collision(radar_asset),
        ),
    ]

    joints: list[JointSpec] = [
        fixed_joint(
            "base_footprint_to_base_link",
            parent="base_footprint",
            child="base_link",
            xyz_mm=(0.0, 0.0, flat_robot.ROBOT_WHEEL_GROUND_PROTRUSION),
        ),
        fixed_joint("base_link_to_lid", parent="base_link", child="lid_link"),
        fixed_joint(
            "base_link_to_battery",
            parent="base_link",
            child="battery_link",
            xyz_mm=flat_robot.BATTERY_CENTER,
            rpy_deg=(0.0, 0.0, 90.0),
        ),
        fixed_joint(
            "base_link_to_esp32",
            parent="base_link",
            child="esp32_link",
            xyz_mm=flat_robot.ESP32_CENTER,
            rpy_deg=(0.0, 90.0, 0.0),
        ),
        fixed_joint(
            "base_link_to_ov2640_camera",
            parent="base_link",
            child="ov2640_camera_link",
            xyz_mm=flat_robot.OV2640_CAMERA_CENTER,
        ),
        fixed_joint(
            "base_link_to_tof",
            parent="base_link",
            child="tof_link",
            xyz_mm=flat_robot.TOF_CENTER,
            rpy_deg=flat_robot.TOF_ROTATION,
        ),
        fixed_joint(
            "base_link_to_radar",
            parent="base_link",
            child="radar_link",
            xyz_mm=flat_robot.RADAR_CENTER,
            rpy_deg=(-90.0, 0.0, 0.0),
        ),
    ]

    wheel_limit = JointLimit(
        effort=WHEEL_JOINT_EFFORT_NM,
        velocity=WHEEL_JOINT_VELOCITY_RAD_S,
    )
    wheel_dynamics = JointDynamics(
        damping=WHEEL_JOINT_DAMPING,
        friction=WHEEL_JOINT_FRICTION,
    )

    for side, side_name in [(-1, "left"), (1, "right")]:
        motor_link = f"{side_name}_motor_link"
        wheel_link = f"{side_name}_wheel_link"
        encoder_link = f"{side_name}_encoder_link"
        magnet_link = f"{side_name}_encoder_magnet_link"

        links.extend(
            [
                LinkSpec(
                    name=motor_link,
                    inertial=inertial_from_bbox(motor_asset.model, MOTOR_MASS_KG),
                    visual=_base_visual(motor_link, motor_asset, SILVER),
                    collision=_base_collision(motor_asset),
                ),
                LinkSpec(
                    name=wheel_link,
                    inertial=inertial_from_cylinder(
                        mass_kg=WHEEL_MASS_KG,
                        radius_mm=flat_robot.ROBOT_WHEEL_RADIUS,
                        length_mm=WHEEL_HUB_WIDTH,
                        axis="x",
                    ),
                    visual=_base_visual(wheel_link, wheel_asset, TPU_BLACK),
                    collision=_base_collision(wheel_asset),
                ),
                LinkSpec(
                    name=encoder_link,
                    inertial=inertial_from_bbox(encoder_asset.model, ENCODER_MASS_KG),
                    visual=_base_visual(encoder_link, encoder_asset, BLUE),
                    collision=_base_collision(encoder_asset),
                ),
                LinkSpec(
                    name=magnet_link,
                    inertial=inertial_from_cylinder(
                        mass_kg=MAGNET_MASS_KG,
                        radius_mm=flat_robot.ENCODER_MAGNET_RADIUS,
                        length_mm=flat_robot.ENCODER_MAGNET_THICKNESS,
                        axis="x",
                    ),
                    visual=_base_visual(magnet_link, magnet_asset, BLACK),
                    collision=_base_collision(magnet_asset),
                ),
            ]
        )

        joints.extend(
            [
                fixed_joint(
                    f"base_link_to_{side_name}_motor",
                    parent="base_link",
                    child=motor_link,
                    xyz_mm=(
                        side
                        * (flat_robot.ROBOT_MOTOR_FACE_X - flat_robot.MOTOR_STEP_FACE_Z),
                        flat_robot.ROBOT_AXLE_Y,
                        flat_robot.ROBOT_AXLE_Z,
                    ),
                    rpy_deg=(0.0, 90.0 * side, 0.0),
                ),
                JointSpec(
                    name=f"{side_name}_wheel_joint",
                    joint_type="continuous",
                    parent="base_link",
                    child=wheel_link,
                    xyz_mm=(
                        side * flat_robot.ROBOT_WHEEL_CENTER_X,
                        flat_robot.ROBOT_AXLE_Y,
                        flat_robot.ROBOT_AXLE_Z,
                    ),
                    axis=(-1.0, 0.0, 0.0),
                    limit=wheel_limit,
                    dynamics=wheel_dynamics,
                ),
                fixed_joint(
                    f"base_link_to_{side_name}_encoder",
                    parent="base_link",
                    child=encoder_link,
                    xyz_mm=(
                        side * _encoder_center_x(),
                        flat_robot.ROBOT_AXLE_Y,
                        flat_robot.ROBOT_AXLE_Z,
                    ),
                    rpy_deg=(0.0, 90.0 * side, 0.0),
                ),
                fixed_joint(
                    f"base_link_to_{side_name}_encoder_magnet",
                    parent="base_link",
                    child=magnet_link,
                    xyz_mm=(
                        side * _magnet_center_x(),
                        flat_robot.ROBOT_AXLE_Y,
                        flat_robot.ROBOT_AXLE_Z,
                    ),
                ),
            ]
        )

    return RobotDescription(
        name="flat_disk_robot",
        project="flat-disk-robot",
        artifact_name="flat-disk-robot",
        links=tuple(links),
        joints=tuple(joints),
        notes=(
            "All coordinates originate from projects/flat-disk-robot/flat_disk_robot/robot.py.",
            "URDF mesh geometry is exported in millimeters and scaled to meters with mesh scale 0.001.",
            "Wheel joints are continuous around the robot X axis; all other joints are fixed reference placements.",
            "Mass and inertia values are first-pass assumptions for visualization, TF, and basic simulation setup.",
        ),
    )
