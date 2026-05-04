from __future__ import annotations

from math import cos, hypot, sin, sqrt, tau

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
    RegularPolygon,
    Text,
    TextAlign,
    add,
    extrude,
)

from synthcad.cad.common import (
    BLUE,
    BLACK,
    COPPER_GOLD,
    OFF_WHITE,
    PRINTED_FRAME,
    SILVER,
    TPU_BLACK,
    tag,
)
from synthcad.cad.serviceability import make_vertical_access_keepout
from synthcad.external_parts import (
    AS5600_ENCODER,
    AS5600_MOUNTING_HOLES,
    OV2640_21MM_160_CAMERA,
    REPEAT_COMPACT_1806,
    XIAO_ESP32S3_SENSE,
)
from synthcad.library.batteries import make_small_4s_battery
from synthcad.library.boards import TOF_MOUNTING_HOLES, make_tof_sensor_board
from synthcad.library.repeat_drive import (
    FACE_REGISTER_RADIUS,
    M2_CLEARANCE_RADIUS,
    M2_COUNTERBORE_DEPTH,
    M2_COUNTERBORE_RADIUS,
    MOTOR_FACE_Y,
    MOTOR_PLATE_HEIGHT,
    MOTOR_PLATE_LENGTH,
    MOTOR_PLATE_THICKNESS,
    MOTOR_RIB_DEPTH,
    MOTOR_RIB_HEIGHT,
    MOTOR_RIB_THICKNESS,
    MOTOR_STEP_FACE_Z,
    SHAFT_CLEARANCE_RADIUS,
    WHEEL_CENTER_Y,
    WHEEL_HUB_WIDTH,
    WHEEL_RADIUS,
    WHEEL_SCREW_ACCESS_RADIUS,
    motor_bolt_circle_offsets,
    make_tpu_d_bore_wheel,
)
from synthcad.library.sensors import make_forward_radar_module


ROBOT_DIAMETER = 216.0
ROBOT_RADIUS = ROBOT_DIAMETER / 2
ROBOT_CHASSIS_THICKNESS = 5.0
PERIMETER_WALL_THICKNESS = 3.0
PERIMETER_WALL_HEIGHT = 18.0
MOTOR_MOUNT_BASE_OVERLAP = 1.0
MOTOR_SHAFT_KEYHOLE_EXTRA_Z = 0.5
MOTOR_FACE_REGISTER_CLEARANCE_DEPTH = 2.5
MOTOR_FACE_REGISTER_CLEARANCE_RADIUS = FACE_REGISTER_RADIUS + 0.25

ROBOT_AXLE_Y = -18.0
ROBOT_WHEEL_GROUND_PROTRUSION = 4.5
ROBOT_WHEEL_RADIUS = WHEEL_RADIUS + ROBOT_WHEEL_GROUND_PROTRUSION
ROBOT_AXLE_Z = WHEEL_RADIUS
ROBOT_WHEEL_CENTER_X = 86.5
ROBOT_MOTOR_FACE_X = ROBOT_WHEEL_CENTER_X - (WHEEL_CENTER_Y - MOTOR_FACE_Y)
REPEAT_MOTOR_REAR_LOCAL_Z = -27.3
ROBOT_MOTOR_REAR_X = ROBOT_MOTOR_FACE_X - MOTOR_STEP_FACE_Z + REPEAT_MOTOR_REAR_LOCAL_Z

BATTERY_CENTER = (0.0, -28.0, ROBOT_CHASSIS_THICKNESS)
ESP32_CENTER = (8.0, 82.0, 30.0)
TOF_STANDOFF_EXTENSION = 3.0
TOF_CENTER = (-34.0, 83.0 + TOF_STANDOFF_EXTENSION, 30.0)
TOF_ROTATION = (-90, 0, 180)
RADAR_CENTER = (34.0, 84.0, 28.0)

USB_CUTOUT_SIZE = (25.0, 22.0)
WHEEL_SLOT_CLEARANCE_X = 2.0
WHEEL_SLOT_CLEARANCE_Y = 13.0
WHEEL_SLOT_SIZE = (
    WHEEL_HUB_WIDTH + 2 * WHEEL_SLOT_CLEARANCE_X,
    2 * ROBOT_WHEEL_RADIUS + WHEEL_SLOT_CLEARANCE_Y,
)

M2_MOUNT_HOLE_RADIUS = 1.15
ELECTRONICS_STANDOFF_RADIUS = 3.6
ELECTRONICS_STANDOFF_HEIGHT = 8.0
BATTERY_RAIL_HEIGHT = 8.0
BATTERY_RAIL_THICKNESS = 3.0
BATTERY_TRAY_LENGTH = 82.0
BATTERY_TRAY_WIDTH = 44.0

AS5600_BOARD_THICKNESS = 3.5
ENCODER_SENSOR_GAP = 2.65
ENCODER_MAGNET_RADIUS = 3.0
ENCODER_MAGNET_THICKNESS = 2.0
ENCODER_MOUNT_PLATE_THICKNESS = 2.5
ENCODER_MOUNT_PLATE_WIDTH = 30.0
# The AS5600 hole pattern stays centered on the axle, but the printed plate
# continues down into the chassis base instead of relying on a small tab.
ENCODER_MOUNT_PLATE_ABOVE_AXLE = 15.0
ENCODER_MOUNT_BASE_OVERLAP = 1.0
ENCODER_MOUNT_PLATE_BOTTOM_Z = ROBOT_CHASSIS_THICKNESS - ENCODER_MOUNT_BASE_OVERLAP
ENCODER_MOUNT_PLATE_TOP_Z = ROBOT_AXLE_Z + ENCODER_MOUNT_PLATE_ABOVE_AXLE
ENCODER_MOUNT_PLATE_HEIGHT = ENCODER_MOUNT_PLATE_TOP_Z - ENCODER_MOUNT_PLATE_BOTTOM_Z
ENCODER_MOUNT_PLATE_CENTER_Z = (
    ENCODER_MOUNT_PLATE_BOTTOM_Z + ENCODER_MOUNT_PLATE_HEIGHT / 2
)
AS5600_MOUNT_CLEARANCE_RADIUS = 1.85

FRONT_BULKHEAD_Y = 73.0
FRONT_BULKHEAD_THICKNESS = 3.0
FRONT_BULKHEAD_WIDTH = 116.0
FRONT_BULKHEAD_HEIGHT = 38.0
FRONT_BULKHEAD_CENTER_Z = ROBOT_CHASSIS_THICKNESS + FRONT_BULKHEAD_HEIGHT / 2
TOF_BOARD_CLEARANCE = 0.8
TOF_BOSS_LENGTH = (
    TOF_CENTER[1]
    - (FRONT_BULKHEAD_Y + FRONT_BULKHEAD_THICKNESS / 2)
    - TOF_BOARD_CLEARANCE
)
TOF_BOSS_RADIUS = 3.4
TOF_PLASTIC_THREAD_HOLE_RADIUS = TOF_MOUNTING_HOLES[0][2]
ADHESIVE_PAD_PROJECTION = 7.0
ADHESIVE_PAD_THICKNESS = 1.2
ESP32_ADHESIVE_PAD = (2.0, 27.0, 28.0, 28.0)
RADAR_ADHESIVE_PAD = (34.0, 28.0, 28.0, 20.0)
OV2640_CAMERA_LENS_CENTER_X = 0.0
OV2640_CAMERA_LENS_CENTER_Z = 21.25
OV2640_CAMERA_LENS_RADIUS = 5.5
OV2640_CAMERA_BODY_HALF_SIZE = 4.25
OV2640_CAMERA_LOCAL_BODY_FRONT_Y = 2.0
OV2640_CAMERA_LOCAL_LENS_FRONT_Y = 10.0
OV2640_CAMERA_MOUNT_TOLERANCE = 0.15
OV2640_CAMERA_BODY_SOCKET_DEPTH = 1.0
OV2640_CAMERA_BODY_SOCKET_ENGAGEMENT = 0.5
OV2640_CAMERA_SOCKET_OVERTRAVEL = 0.2
CAMERA_MOUNT_WIDTH = 18.0
CAMERA_MOUNT_HEIGHT = 24.0
CAMERA_MOUNT_THICKNESS = (
    OV2640_CAMERA_LOCAL_LENS_FRONT_Y - OV2640_CAMERA_LOCAL_BODY_FRONT_Y
)
CAMERA_MOUNT_FRONT_EDGE_MARGIN = 0.25
CAMERA_MOUNT_FRONT_FACE_Y = (
    sqrt(ROBOT_RADIUS**2 - (CAMERA_MOUNT_WIDTH / 2) ** 2)
    - CAMERA_MOUNT_FRONT_EDGE_MARGIN
)
CAMERA_MOUNT_BACK_FACE_Y = CAMERA_MOUNT_FRONT_FACE_Y - CAMERA_MOUNT_THICKNESS
OV2640_CAMERA_CENTER = (
    OV2640_CAMERA_LENS_CENTER_X,
    CAMERA_MOUNT_BACK_FACE_Y
    + OV2640_CAMERA_BODY_SOCKET_ENGAGEMENT
    - OV2640_CAMERA_LOCAL_BODY_FRONT_Y,
    OV2640_CAMERA_LENS_CENTER_Z,
)
OV2640_CAMERA_LENS_CLEARANCE_RADIUS = (
    OV2640_CAMERA_LENS_RADIUS + OV2640_CAMERA_MOUNT_TOLERANCE
)
OV2640_CAMERA_BODY_CLEARANCE_HALF_SIZE = (
    OV2640_CAMERA_BODY_HALF_SIZE + OV2640_CAMERA_MOUNT_TOLERANCE
)
INCH_MM = 25.4


def _front_opening_outer_half_chord(opening_depth: float, wall_thickness: float) -> float:
    opening_back_y = ROBOT_RADIUS - wall_thickness / 2 - opening_depth / 2
    return sqrt(max(ROBOT_RADIUS**2 - opening_back_y**2, 0.0))


def _front_opening_depth_for_outer_half_chord(
    half_chord: float,
    wall_thickness: float,
) -> float:
    opening_back_y = sqrt(ROBOT_RADIUS**2 - half_chord**2)
    return 2 * (ROBOT_RADIUS - wall_thickness / 2 - opening_back_y)


FRONT_SENSOR_OPENING_WIDTH = 144.0
# The previous shallow front wall slot was already wider than the local circular
# chord, so more sensor side clearance comes from carrying the opening farther
# around the chassis shoulders.
FRONT_SENSOR_OPENING_BASE_DEPTH = PERIMETER_WALL_THICKNESS * 4
FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE = INCH_MM
FRONT_SENSOR_OPENING_EFFECTIVE_HALF_WIDTH = (
    _front_opening_outer_half_chord(
        FRONT_SENSOR_OPENING_BASE_DEPTH,
        PERIMETER_WALL_THICKNESS,
    )
    + FRONT_SENSOR_OPENING_EXTRA_SIDE_CLEARANCE
)
FRONT_SENSOR_OPENING_EFFECTIVE_WIDTH = 2 * FRONT_SENSOR_OPENING_EFFECTIVE_HALF_WIDTH
FRONT_SENSOR_OPENING_DEPTH = _front_opening_depth_for_outer_half_chord(
    FRONT_SENSOR_OPENING_EFFECTIVE_HALF_WIDTH,
    PERIMETER_WALL_THICKNESS,
)
REAR_SERVICE_OPENING_WIDTH = 62.0

CENTRAL_ELECTRONICS_MOUNT_POINTS = [
    (-34.0, 24.0),
    (34.0, 24.0),
]

LID_MOUNT_POINTS = [
    (-58.0, -78.0),
    (58.0, -78.0),
    (-82.0, 24.0),
    (82.0, 24.0),
    (-68.0, 60.0),
    (68.0, 60.0),
]

# M4 printed clearance and simple screw geometry for lid verification.
M4_CLEARANCE_DIAMETER = 4.25
M4_CLEARANCE_RADIUS = M4_CLEARANCE_DIAMETER / 2
M4_SHANK_DIAMETER = 3.9
M4_SHANK_RADIUS = M4_SHANK_DIAMETER / 2
M4_SOCKET_HEAD_DIAMETER = 7.0
M4_SOCKET_HEAD_RADIUS = M4_SOCKET_HEAD_DIAMETER / 2
M4_SOCKET_HEAD_HEIGHT = 4.0
# Assumed M4 heat-set insert pilot based on common short brass inserts.
M4_INSERT_POCKET_DIAMETER = 5.6
M4_INSERT_POCKET_RADIUS = M4_INSERT_POCKET_DIAMETER / 2
M4_INSERT_POCKET_DEPTH = 8.0

LID_BOSS_RADIUS = 10.0
LID_BOSS_HEIGHT = PERIMETER_WALL_HEIGHT
# Trim the pad diameter slightly so the circular lid envelope stays inside the
# 216 mm chassis footprint instead of poking past it at the rear screws.
LID_PAD_RADIUS = 10.75
LID_PAD_BOTTOM_Z = ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT
LID_SHELL_WALL_THICKNESS = 3.0
LID_OUTER_RADIUS = ROBOT_RADIUS
LID_INNER_RADIUS = LID_OUTER_RADIUS - LID_SHELL_WALL_THICKNESS
# Drop the lid skirt to the top of the printed chassis wall so the two shells
# meet instead of leaving a visible gap around the sides.
LID_WALL_BOTTOM_Z = LID_PAD_BOTTOM_Z
LID_TOP_UNDERSIDE_Z = 46.5
LID_TOP_THICKNESS = 3.0
LID_PAD_TOP_Z = LID_TOP_UNDERSIDE_Z
LID_PAD_THICKNESS = LID_PAD_TOP_Z - LID_PAD_BOTTOM_Z
LID_TOP_CENTER_Z = LID_TOP_UNDERSIDE_Z + LID_TOP_THICKNESS / 2
LID_TOP_SURFACE_Z = LID_TOP_UNDERSIDE_Z + LID_TOP_THICKNESS
LID_WALL_HEIGHT = LID_TOP_UNDERSIDE_Z - LID_WALL_BOTTOM_Z
LID_WALL_CENTER_Z = LID_WALL_BOTTOM_Z + LID_WALL_HEIGHT / 2
LID_FASTENER_HOLE_Z_MIN = LID_WALL_BOTTOM_Z - 0.1
LID_FASTENER_HOLE_Z_MAX = LID_TOP_CENTER_Z + LID_TOP_THICKNESS / 2 + 0.1
LID_FASTENER_HOLE_HEIGHT = LID_FASTENER_HOLE_Z_MAX - LID_FASTENER_HOLE_Z_MIN
LID_FRONT_WALL_OPENING_DEPTH = _front_opening_depth_for_outer_half_chord(
    FRONT_SENSOR_OPENING_EFFECTIVE_HALF_WIDTH,
    LID_SHELL_WALL_THICKNESS,
)
LID_WALL_OPENING_DEPTH = LID_SHELL_WALL_THICKNESS * 4
LID_SIDE_ACCESS_OPENING_WIDTH = 82.0
LID_SIDE_ACCESS_OPENING_LENGTH = 68.0
LID_SIDE_ACCESS_OPENING_CENTER_X = 73.0
LID_SIDE_ACCESS_OPENING_CENTER_Y = -20.0
LID_WHEEL_WELL_CUTOUT_WIDTH = WHEEL_HUB_WIDTH + 6.0
LID_WHEEL_WELL_CUTOUT_LENGTH = 2 * ROBOT_WHEEL_RADIUS + 5.0
LID_WHEEL_WELL_CUTOUT_Z_MIN = LID_TOP_UNDERSIDE_Z - 0.2
LID_WHEEL_WELL_CUTOUT_Z_MAX = LID_TOP_SURFACE_Z + 0.2
LID_WHEEL_WELL_CUTOUT_HEIGHT = (
    LID_WHEEL_WELL_CUTOUT_Z_MAX - LID_WHEEL_WELL_CUTOUT_Z_MIN
)
LID_WHEEL_WELL_CUTOUT_CENTER_Z = (
    LID_WHEEL_WELL_CUTOUT_Z_MIN + LID_WHEEL_WELL_CUTOUT_HEIGHT / 2
)
M4_DRIVER_ACCESS_DIAMETER = 14.0
M4_DRIVER_ACCESS_RADIUS = M4_DRIVER_ACCESS_DIAMETER / 2
M4_DRIVER_ACCESS_Z_MIN = LID_PAD_TOP_Z + 0.05
M4_DRIVER_ACCESS_Z_MAX = LID_TOP_CENTER_Z + LID_TOP_THICKNESS / 2 + 0.5
M4_DRIVER_ACCESS_HEIGHT = M4_DRIVER_ACCESS_Z_MAX - M4_DRIVER_ACCESS_Z_MIN
M4_DRIVER_ACCESS_CUT_Z_MIN = LID_PAD_TOP_Z - 0.1
M4_DRIVER_ACCESS_CUT_Z_MAX = M4_DRIVER_ACCESS_Z_MAX
M4_DRIVER_ACCESS_CUT_HEIGHT = M4_DRIVER_ACCESS_CUT_Z_MAX - M4_DRIVER_ACCESS_CUT_Z_MIN

# Nominal switch body callout from the hardware request is 22 x 27 mm. Add a
# small print allowance so the lid opening behaves like a PETG/ASA press fit.
LID_SWITCH_PANEL_CUTOUT_SIZE = (22.0, 27.0)
LID_SWITCH_PRESS_FIT_CLEARANCE = 0.15
LID_SWITCH_CUTOUT_SIZE = (
    LID_SWITCH_PANEL_CUTOUT_SIZE[0] + 2 * LID_SWITCH_PRESS_FIT_CLEARANCE,
    LID_SWITCH_PANEL_CUTOUT_SIZE[1] + 2 * LID_SWITCH_PRESS_FIT_CLEARANCE,
)
# Keep the switch forward of the battery envelope while staying clear of the
# front sensor cluster and the nearby lid fastener pads.
LID_SWITCH_CUTOUT_CENTER = (0.0, 52.0)

# Lower-chassis service tunnels match the wheel hub screw-access hole so the
# same driver clearance exists all the way to the face-mount screws.
MOTOR_DRIVER_ACCESS_DIAMETER = 2 * WHEEL_SCREW_ACCESS_RADIUS
MOTOR_DRIVER_ACCESS_RADIUS = MOTOR_DRIVER_ACCESS_DIAMETER / 2
MOTOR_DRIVER_ACCESS_OVERTRAVEL = 6.0

# Vent pattern for the lid roof so high-fidelity PR viewers can reveal whether
# circular through-features stay round and evenly spaced in the web UI.
LID_VENT_HOLE_RADIUS = 4.0
LID_VENT_RING_RADIUS = 24.0
LID_VENT_HOLE_COUNT = 8

LID_LOGO_TEXT_LINES = (
    "Designed by GPT-5.4 xhigh with build123d",
)
LID_LOGO_TEXT = "\n".join(LID_LOGO_TEXT_LINES)
LID_LOGO_TEXT_SIZE = 8.0
LID_LOGO_TEXT_ALIGN = (TextAlign.LEFT, TextAlign.CENTER)
LID_LOGO_BLOCK_ALIGN = (Align.CENTER, Align.CENTER)
LID_LOGO_CENTER = (0.0, -50.0)
LID_LOGO_ENGRAVE_DEPTH = 0.35
LID_LOGO_CUT_OVERTRAVEL = 0.1

# Blind top-face weight reduction pockets. The deterministic grid keeps a
# continuous roof floor and explicit webs around every functional lid feature.
LID_HEX_POCKET_VERTEX_RADIUS = 5.2
LID_HEX_POCKET_DEPTH = 1.35
LID_HEX_POCKET_CUT_OVERTRAVEL = 0.15
LID_HEX_POCKET_MIN_FLOOR_THICKNESS = 1.5
LID_HEX_POCKET_PITCH = 15.5
LID_HEX_POCKET_ROW_STEP = LID_HEX_POCKET_PITCH * sqrt(3) / 2
LID_HEX_POCKET_EDGE_MARGIN = 5.0
LID_HEX_POCKET_SCREW_MARGIN = 7.0
LID_HEX_POCKET_SWITCH_MARGIN = 6.0
LID_HEX_POCKET_WHEEL_WELL_MARGIN = 5.0
LID_HEX_POCKET_SIDE_ACCESS_MARGIN = 4.0
LID_HEX_POCKET_VENT_MARGIN = 4.0
LID_HEX_POCKET_LOGO_MARGIN = 1.5
LID_HEX_POCKET_LOGO_KEEP_OUT_SIZE = (155.0, 16.0)
LID_HEX_POCKET_KEEPIN_RADIUS = (
    LID_INNER_RADIUS - LID_HEX_POCKET_VERTEX_RADIUS - LID_HEX_POCKET_EDGE_MARGIN
)
LID_HEX_POCKET_INNER_KEEP_OUT_RADIUS = (
    LID_VENT_RING_RADIUS
    + LID_VENT_HOLE_RADIUS
    + LID_HEX_POCKET_VERTEX_RADIUS
    + LID_HEX_POCKET_VENT_MARGIN
)


def _is_hex_pocket_clear_of_circle(
    x: float,
    y: float,
    center_x: float,
    center_y: float,
    radius: float,
    margin: float,
) -> bool:
    return (
        hypot(x - center_x, y - center_y)
        >= radius + LID_HEX_POCKET_VERTEX_RADIUS + margin
    )


def _is_hex_pocket_clear_of_rectangle(
    x: float,
    y: float,
    center_x: float,
    center_y: float,
    width: float,
    length: float,
    margin: float,
) -> bool:
    clearance = LID_HEX_POCKET_VERTEX_RADIUS + margin
    return (
        abs(x - center_x) >= width / 2 + clearance
        or abs(y - center_y) >= length / 2 + clearance
    )


def _is_lid_hex_pocket_center_safe(x: float, y: float) -> bool:
    if hypot(x, y) > LID_HEX_POCKET_KEEPIN_RADIUS:
        return False
    if hypot(x, y) < LID_HEX_POCKET_INNER_KEEP_OUT_RADIUS:
        return False

    if not _is_hex_pocket_clear_of_rectangle(
        x,
        y,
        LID_SWITCH_CUTOUT_CENTER[0],
        LID_SWITCH_CUTOUT_CENTER[1],
        LID_SWITCH_CUTOUT_SIZE[0],
        LID_SWITCH_CUTOUT_SIZE[1],
        LID_HEX_POCKET_SWITCH_MARGIN,
    ):
        return False

    if not _is_hex_pocket_clear_of_rectangle(
        x,
        y,
        LID_LOGO_CENTER[0],
        LID_LOGO_CENTER[1],
        LID_HEX_POCKET_LOGO_KEEP_OUT_SIZE[0],
        LID_HEX_POCKET_LOGO_KEEP_OUT_SIZE[1],
        LID_HEX_POCKET_LOGO_MARGIN,
    ):
        return False

    for screw_x, screw_y in LID_MOUNT_POINTS:
        if not _is_hex_pocket_clear_of_circle(
            x,
            y,
            screw_x,
            screw_y,
            LID_PAD_RADIUS,
            LID_HEX_POCKET_SCREW_MARGIN,
        ):
            return False

    for index in range(LID_VENT_HOLE_COUNT):
        angle = tau * index / LID_VENT_HOLE_COUNT
        if not _is_hex_pocket_clear_of_circle(
            x,
            y,
            LID_VENT_RING_RADIUS * cos(angle),
            LID_VENT_RING_RADIUS * sin(angle),
            LID_VENT_HOLE_RADIUS,
            LID_HEX_POCKET_VENT_MARGIN,
        ):
            return False

    for side in (-1, 1):
        if not _is_hex_pocket_clear_of_rectangle(
            x,
            y,
            side * ROBOT_WHEEL_CENTER_X,
            ROBOT_AXLE_Y,
            LID_WHEEL_WELL_CUTOUT_WIDTH,
            LID_WHEEL_WELL_CUTOUT_LENGTH,
            LID_HEX_POCKET_WHEEL_WELL_MARGIN,
        ):
            return False
        if not _is_hex_pocket_clear_of_rectangle(
            x,
            y,
            side * LID_SIDE_ACCESS_OPENING_CENTER_X,
            LID_SIDE_ACCESS_OPENING_CENTER_Y,
            LID_SIDE_ACCESS_OPENING_WIDTH,
            LID_SIDE_ACCESS_OPENING_LENGTH,
            LID_HEX_POCKET_SIDE_ACCESS_MARGIN,
        ):
            return False

    return True


def _lid_hex_pocket_centers() -> tuple[tuple[float, float], ...]:
    max_rows = int(LID_HEX_POCKET_KEEPIN_RADIUS / LID_HEX_POCKET_ROW_STEP) + 2
    max_cols = int(LID_HEX_POCKET_KEEPIN_RADIUS / LID_HEX_POCKET_PITCH) + 2
    centers: list[tuple[float, float]] = []

    for row in range(-max_rows, max_rows + 1):
        y = row * LID_HEX_POCKET_ROW_STEP
        x_offset = LID_HEX_POCKET_PITCH / 2 if row % 2 else 0.0
        for column in range(-max_cols, max_cols + 1):
            x = column * LID_HEX_POCKET_PITCH + x_offset
            if _is_lid_hex_pocket_center_safe(x, y):
                centers.append((round(x, 6), round(y, 6)))

    return tuple(centers)


def _motor_plate_center_x(side: int) -> float:
    return side * (ROBOT_MOTOR_FACE_X + MOTOR_PLATE_THICKNESS / 2)


def _motor_register_x(side: int) -> float:
    return side * (ROBOT_MOTOR_FACE_X + MOTOR_FACE_REGISTER_CLEARANCE_DEPTH / 2)


def _motor_counterbore_x(side: int) -> float:
    return side * (
        ROBOT_MOTOR_FACE_X
        + MOTOR_PLATE_THICKNESS
        - M2_COUNTERBORE_DEPTH / 2
    )


def _motor_mount_top_z() -> float:
    return ROBOT_CHASSIS_THICKNESS - MOTOR_MOUNT_BASE_OVERLAP + MOTOR_PLATE_HEIGHT


def _add_motor_shaft_keyhole(plate_x: float):
    slot_bottom_z = ROBOT_AXLE_Z - MOTOR_SHAFT_KEYHOLE_EXTRA_Z
    slot_top_z = _motor_mount_top_z() + MOTOR_SHAFT_KEYHOLE_EXTRA_Z
    with Locations((plate_x, ROBOT_AXLE_Y, (slot_bottom_z + slot_top_z) / 2)):
        Box(
            MOTOR_PLATE_THICKNESS * 4,
            SHAFT_CLEARANCE_RADIUS * 2,
            slot_top_z - slot_bottom_z,
            mode=Mode.SUBTRACT,
        )


def _add_mount_standoff(x: float, y: float, height: float = ELECTRONICS_STANDOFF_HEIGHT):
    with Locations((x, y, ROBOT_CHASSIS_THICKNESS + height / 2)):
        Cylinder(ELECTRONICS_STANDOFF_RADIUS, height)
    with Locations((x, y, (ROBOT_CHASSIS_THICKNESS + height) / 2)):
        Cylinder(
            M2_MOUNT_HOLE_RADIUS,
            ROBOT_CHASSIS_THICKNESS + height + 1.0,
            mode=Mode.SUBTRACT,
        )


def _add_battery_tray():
    rail_x = BATTERY_TRAY_WIDTH / 2
    for side in [-1, 1]:
        with Locations(
            (
                side * rail_x,
                BATTERY_CENTER[1],
                ROBOT_CHASSIS_THICKNESS + BATTERY_RAIL_HEIGHT / 2,
            )
        ):
            Box(BATTERY_RAIL_THICKNESS, BATTERY_TRAY_LENGTH, BATTERY_RAIL_HEIGHT)

    with Locations(
        (
            0,
            BATTERY_CENTER[1] - BATTERY_TRAY_LENGTH / 2,
            ROBOT_CHASSIS_THICKNESS + BATTERY_RAIL_HEIGHT / 2,
        )
    ):
        Box(BATTERY_TRAY_WIDTH, BATTERY_RAIL_THICKNESS, BATTERY_RAIL_HEIGHT)


def _add_central_electronics_bay():
    for x, y in CENTRAL_ELECTRONICS_MOUNT_POINTS:
        _add_mount_standoff(x, y, height=10.0)


def _add_front_electronics_bulkhead():
    with Locations((0, FRONT_BULKHEAD_Y, FRONT_BULKHEAD_CENTER_Z)):
        Box(FRONT_BULKHEAD_WIDTH, FRONT_BULKHEAD_THICKNESS, FRONT_BULKHEAD_HEIGHT)

    front_face_y = FRONT_BULKHEAD_Y + FRONT_BULKHEAD_THICKNESS / 2
    for local_x, local_y, _radius in TOF_MOUNTING_HOLES:
        x = TOF_CENTER[0] - local_x
        z = TOF_CENTER[2] + local_y
        with Locations((x, front_face_y + TOF_BOSS_LENGTH / 2, z)):
            Cylinder(TOF_BOSS_RADIUS, TOF_BOSS_LENGTH, rotation=(90, 0, 0))
        with Locations((x, front_face_y + TOF_BOSS_LENGTH / 2, z)):
            Cylinder(
                TOF_PLASTIC_THREAD_HOLE_RADIUS,
                TOF_BOSS_LENGTH + FRONT_BULKHEAD_THICKNESS + 2.0,
                rotation=(90, 0, 0),
                mode=Mode.SUBTRACT,
            )

    adhesive_y = front_face_y + ADHESIVE_PAD_PROJECTION / 2
    for x, z, width, height in [ESP32_ADHESIVE_PAD, RADAR_ADHESIVE_PAD]:
        with Locations((x, adhesive_y, z)):
            Box(width, ADHESIVE_PAD_PROJECTION, height)
        with Locations((x, front_face_y + ADHESIVE_PAD_THICKNESS / 2, z)):
            Box(width + 4.0, ADHESIVE_PAD_THICKNESS, height + 4.0)

    _add_ov2640_camera_mount()


def _add_ov2640_camera_mount():
    wall_center_y = CAMERA_MOUNT_FRONT_FACE_Y - CAMERA_MOUNT_THICKNESS / 2
    wall_center_z = ROBOT_CHASSIS_THICKNESS + CAMERA_MOUNT_HEIGHT / 2

    with Locations(
        (
            OV2640_CAMERA_LENS_CENTER_X,
            wall_center_y,
            wall_center_z,
        )
    ):
        Box(CAMERA_MOUNT_WIDTH, CAMERA_MOUNT_THICKNESS, CAMERA_MOUNT_HEIGHT)

    with Locations(
        (
            OV2640_CAMERA_LENS_CENTER_X,
            wall_center_y,
            OV2640_CAMERA_LENS_CENTER_Z,
        )
    ):
        Cylinder(
            OV2640_CAMERA_LENS_CLEARANCE_RADIUS,
            CAMERA_MOUNT_THICKNESS + 2.0,
            rotation=(90, 0, 0),
            mode=Mode.SUBTRACT,
        )

    socket_depth = OV2640_CAMERA_BODY_SOCKET_DEPTH + OV2640_CAMERA_SOCKET_OVERTRAVEL
    with Locations(
        (
            OV2640_CAMERA_LENS_CENTER_X,
            CAMERA_MOUNT_BACK_FACE_Y
            + OV2640_CAMERA_BODY_SOCKET_DEPTH / 2
            - OV2640_CAMERA_SOCKET_OVERTRAVEL / 2,
            OV2640_CAMERA_LENS_CENTER_Z,
        )
    ):
        Box(
            OV2640_CAMERA_BODY_CLEARANCE_HALF_SIZE * 2,
            socket_depth,
            OV2640_CAMERA_BODY_CLEARANCE_HALF_SIZE * 2,
            mode=Mode.SUBTRACT,
        )


def _encoder_mount_plate_x(side: int) -> float:
    encoder_center_x = ROBOT_MOTOR_REAR_X - ENCODER_SENSOR_GAP - AS5600_BOARD_THICKNESS / 2
    plate_x = encoder_center_x - AS5600_BOARD_THICKNESS / 2 - ENCODER_MOUNT_PLATE_THICKNESS / 2
    return side * plate_x


def _make_encoder_mount(side: int):
    plate_x = _encoder_mount_plate_x(side)
    with BuildPart() as mount:
        with Locations((plate_x, ROBOT_AXLE_Y, ENCODER_MOUNT_PLATE_CENTER_Z)):
            Box(
                ENCODER_MOUNT_PLATE_THICKNESS,
                ENCODER_MOUNT_PLATE_WIDTH,
                ENCODER_MOUNT_PLATE_HEIGHT,
            )

        for local_x, local_y, _radius in AS5600_MOUNTING_HOLES:
            with Locations((plate_x, ROBOT_AXLE_Y + local_y, ROBOT_AXLE_Z + local_x)):
                Cylinder(
                    AS5600_MOUNT_CLEARANCE_RADIUS,
                    ENCODER_MOUNT_PLATE_THICKNESS * 3,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )

    return mount.part


def _add_encoder_mount(side: int):
    add(_make_encoder_mount(side))


def _add_perimeter_wall():
    with Locations((0, 0, ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT / 2)):
        Cylinder(ROBOT_RADIUS, PERIMETER_WALL_HEIGHT)
        Cylinder(
            ROBOT_RADIUS - PERIMETER_WALL_THICKNESS,
            PERIMETER_WALL_HEIGHT,
            mode=Mode.SUBTRACT,
        )

    with Locations(
        (
            0,
            ROBOT_RADIUS - PERIMETER_WALL_THICKNESS / 2,
            ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT / 2,
        )
    ):
        Box(
            FRONT_SENSOR_OPENING_WIDTH,
            FRONT_SENSOR_OPENING_DEPTH,
            PERIMETER_WALL_HEIGHT,
            mode=Mode.SUBTRACT,
        )

    with Locations(
        (
            0,
            -ROBOT_RADIUS + PERIMETER_WALL_THICKNESS / 2,
            ROBOT_CHASSIS_THICKNESS + PERIMETER_WALL_HEIGHT / 2,
        )
    ):
        Box(
            REAR_SERVICE_OPENING_WIDTH,
            PERIMETER_WALL_THICKNESS * 4,
            PERIMETER_WALL_HEIGHT,
            mode=Mode.SUBTRACT,
        )


def _add_lid_mount_boss(x: float, y: float):
    with Locations((x, y, ROBOT_CHASSIS_THICKNESS + LID_BOSS_HEIGHT / 2)):
        Cylinder(LID_BOSS_RADIUS, LID_BOSS_HEIGHT)

    with Locations((x, y, LID_PAD_BOTTOM_Z - M4_INSERT_POCKET_DEPTH / 2)):
        Cylinder(
            M4_INSERT_POCKET_RADIUS,
            M4_INSERT_POCKET_DEPTH + 0.2,
            mode=Mode.SUBTRACT,
        )


def _motor_driver_access_tunnel_length() -> float:
    return ROBOT_RADIUS - (ROBOT_MOTOR_FACE_X + MOTOR_PLATE_THICKNESS) + MOTOR_DRIVER_ACCESS_OVERTRAVEL


def _motor_driver_access_center_x(side: int) -> float:
    return side * (
        ROBOT_MOTOR_FACE_X
        + MOTOR_PLATE_THICKNESS
        + _motor_driver_access_tunnel_length() / 2
    )


def _add_motor_driver_access(side: int, hole_y: float, hole_z: float):
    with Locations((_motor_driver_access_center_x(side), hole_y, hole_z)):
        Cylinder(
            MOTOR_DRIVER_ACCESS_RADIUS,
            _motor_driver_access_tunnel_length(),
            rotation=(0, 90, 0),
            mode=Mode.SUBTRACT,
        )


def make_flat_disk_robot_chassis():
    """Printable disk chassis for the reference flat differential robot."""

    with BuildPart() as chassis:
        with Locations((0, 0, ROBOT_CHASSIS_THICKNESS / 2)):
            Cylinder(ROBOT_RADIUS, ROBOT_CHASSIS_THICKNESS)

        for side in [-1, 1]:
            with Locations(
                (
                    side * ROBOT_WHEEL_CENTER_X,
                    ROBOT_AXLE_Y,
                    ROBOT_CHASSIS_THICKNESS / 2,
                )
            ):
                Box(
                    WHEEL_SLOT_SIZE[0],
                    WHEEL_SLOT_SIZE[1],
                    ROBOT_CHASSIS_THICKNESS * 3,
                    mode=Mode.SUBTRACT,
                )

        _add_perimeter_wall()

        with Locations((ESP32_CENTER[0], ESP32_CENTER[1] - 5.0, ROBOT_CHASSIS_THICKNESS / 2)):
            Box(
                USB_CUTOUT_SIZE[0],
                USB_CUTOUT_SIZE[1],
                ROBOT_CHASSIS_THICKNESS * 3,
                mode=Mode.SUBTRACT,
            )

        for y in [-54.0, -2.0]:
            with Locations((0, y, ROBOT_CHASSIS_THICKNESS / 2)):
                Box(58.0, 5.0, ROBOT_CHASSIS_THICKNESS * 3, mode=Mode.SUBTRACT)

        _add_battery_tray()
        _add_central_electronics_bay()
        _add_front_electronics_bulkhead()

        for x, y in LID_MOUNT_POINTS:
            _add_lid_mount_boss(x, y)

        for side in [-1, 1]:
            plate_x = _motor_plate_center_x(side)
            with Locations(
                (
                    plate_x,
                    ROBOT_AXLE_Y,
                    ROBOT_CHASSIS_THICKNESS
                    - MOTOR_MOUNT_BASE_OVERLAP
                    + MOTOR_PLATE_HEIGHT / 2,
                )
            ):
                Box(MOTOR_PLATE_THICKNESS, MOTOR_PLATE_LENGTH, MOTOR_PLATE_HEIGHT)

            rib_x = side * (ROBOT_MOTOR_FACE_X - MOTOR_RIB_DEPTH / 2)
            for rib_y in [
                ROBOT_AXLE_Y - MOTOR_PLATE_LENGTH / 2 + 4.0,
                ROBOT_AXLE_Y + MOTOR_PLATE_LENGTH / 2 - 4.0,
            ]:
                with Locations(
                    (
                        rib_x,
                        rib_y,
                        ROBOT_CHASSIS_THICKNESS
                        - MOTOR_MOUNT_BASE_OVERLAP
                        + MOTOR_RIB_HEIGHT / 2,
                    )
                ):
                    Box(MOTOR_RIB_DEPTH, MOTOR_RIB_THICKNESS, MOTOR_RIB_HEIGHT)

            with Locations((plate_x, ROBOT_AXLE_Y, ROBOT_AXLE_Z)):
                Cylinder(
                    SHAFT_CLEARANCE_RADIUS,
                    MOTOR_PLATE_THICKNESS * 4,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )
            _add_motor_shaft_keyhole(plate_x)

            with Locations((_motor_register_x(side), ROBOT_AXLE_Y, ROBOT_AXLE_Z)):
                Cylinder(
                    MOTOR_FACE_REGISTER_CLEARANCE_RADIUS,
                    MOTOR_FACE_REGISTER_CLEARANCE_DEPTH,
                    rotation=(0, 90, 0),
                    mode=Mode.SUBTRACT,
                )

            for y_offset, z_offset in motor_bolt_circle_offsets():
                hole_y = ROBOT_AXLE_Y + y_offset
                hole_z = ROBOT_AXLE_Z + z_offset
                with Locations((plate_x, hole_y, hole_z)):
                    Cylinder(
                        M2_CLEARANCE_RADIUS,
                        MOTOR_PLATE_THICKNESS * 4,
                        rotation=(0, 90, 0),
                        mode=Mode.SUBTRACT,
                    )
                with Locations((_motor_counterbore_x(side), hole_y, hole_z)):
                    Cylinder(
                        M2_COUNTERBORE_RADIUS,
                        M2_COUNTERBORE_DEPTH + 0.1,
                        rotation=(0, 90, 0),
                        mode=Mode.SUBTRACT,
                    )
                _add_motor_driver_access(side, hole_y, hole_z)

            _add_encoder_mount(side)

    return tag(chassis.part, "216 mm flat disk robot chassis", PRINTED_FRAME)


def _make_circular_lid_shell(*, outer_radius: float, inner_radius: float, height: float):
    with BuildPart() as shell:
        with Locations((0, 0, height / 2)):
            Cylinder(outer_radius, height)
            Cylinder(inner_radius, height + 0.2, mode=Mode.SUBTRACT)
    return shell.part


def _make_circular_lid_roof(*, radius: float, thickness: float):
    with BuildPart() as roof:
        with Locations((0, 0, thickness / 2)):
            Cylinder(radius, thickness)
    return roof.part


def _make_lid_logo_engraving():
    with BuildPart() as logo:
        with BuildSketch(Plane.XY):
            Text(
                LID_LOGO_TEXT,
                LID_LOGO_TEXT_SIZE,
                text_align=LID_LOGO_TEXT_ALIGN,
                align=LID_LOGO_BLOCK_ALIGN,
            )
        extrude(amount=LID_LOGO_ENGRAVE_DEPTH + LID_LOGO_CUT_OVERTRAVEL)
    return logo.part


def _make_lid_hex_weight_pocket_cutters():
    if LID_TOP_THICKNESS - LID_HEX_POCKET_DEPTH < LID_HEX_POCKET_MIN_FLOOR_THICKNESS:
        raise ValueError("Lid hex pockets would leave too little roof floor thickness")

    with BuildPart() as pocket_cutters:
        with BuildSketch(Plane.XY):
            for x, y in _lid_hex_pocket_centers():
                with Locations((x, y)):
                    RegularPolygon(
                        LID_HEX_POCKET_VERTEX_RADIUS,
                        6,
                        rotation=30,
                    )
        extrude(amount=LID_HEX_POCKET_DEPTH + LID_HEX_POCKET_CUT_OVERTRAVEL)

    return pocket_cutters.part


def make_flat_disk_robot_lid():
    """Raised M4-fastened lid over the central battery and controller bay."""

    with BuildPart() as lid:
        for x, y in LID_MOUNT_POINTS:
            with Locations((x, y, LID_PAD_BOTTOM_Z + LID_PAD_THICKNESS / 2)):
                Cylinder(LID_PAD_RADIUS, LID_PAD_THICKNESS)

        add(
            Location((0, 0, LID_WALL_BOTTOM_Z))
            * _make_circular_lid_shell(
                outer_radius=LID_OUTER_RADIUS,
                inner_radius=LID_INNER_RADIUS,
                height=LID_WALL_HEIGHT,
            )
        )
        add(
            Location((0, 0, LID_TOP_UNDERSIDE_Z))
            * _make_circular_lid_roof(
                radius=LID_OUTER_RADIUS,
                thickness=LID_TOP_THICKNESS,
            )
        )

        for opening_width, opening_depth, opening_y in [
            (
                FRONT_SENSOR_OPENING_WIDTH,
                LID_FRONT_WALL_OPENING_DEPTH,
                ROBOT_RADIUS - LID_SHELL_WALL_THICKNESS / 2,
            ),
            (
                REAR_SERVICE_OPENING_WIDTH,
                LID_WALL_OPENING_DEPTH,
                -ROBOT_RADIUS + LID_SHELL_WALL_THICKNESS / 2,
            ),
        ]:
            with Locations((0, opening_y, LID_WALL_CENTER_Z)):
                Box(
                    opening_width,
                    opening_depth,
                    LID_WALL_HEIGHT + 0.2,
                    mode=Mode.SUBTRACT,
                )

        for side in [-1, 1]:
            with Locations(
                (
                    side * LID_SIDE_ACCESS_OPENING_CENTER_X,
                    LID_SIDE_ACCESS_OPENING_CENTER_Y,
                    LID_WALL_CENTER_Z,
                )
            ):
                Box(
                    LID_SIDE_ACCESS_OPENING_WIDTH,
                    LID_SIDE_ACCESS_OPENING_LENGTH,
                    LID_WALL_HEIGHT + 0.2,
                    mode=Mode.SUBTRACT,
                )

            with Locations(
                (
                    side * ROBOT_WHEEL_CENTER_X,
                    ROBOT_AXLE_Y,
                    LID_WHEEL_WELL_CUTOUT_CENTER_Z,
                )
            ):
                Box(
                    LID_WHEEL_WELL_CUTOUT_WIDTH,
                    LID_WHEEL_WELL_CUTOUT_LENGTH,
                    LID_WHEEL_WELL_CUTOUT_HEIGHT,
                    mode=Mode.SUBTRACT,
                )

        with Locations((LID_SWITCH_CUTOUT_CENTER[0], LID_SWITCH_CUTOUT_CENTER[1], LID_TOP_CENTER_Z)):
            Box(
                LID_SWITCH_CUTOUT_SIZE[0],
                LID_SWITCH_CUTOUT_SIZE[1],
                LID_TOP_THICKNESS + 1.0,
                mode=Mode.SUBTRACT,
            )

        for x, y in LID_MOUNT_POINTS:
            with Locations((x, y, LID_FASTENER_HOLE_Z_MIN + LID_FASTENER_HOLE_HEIGHT / 2)):
                Cylinder(
                    M4_CLEARANCE_RADIUS,
                    LID_FASTENER_HOLE_HEIGHT,
                    mode=Mode.SUBTRACT,
                )

        vent_center_z = LID_TOP_UNDERSIDE_Z + LID_TOP_THICKNESS / 2
        for index in range(LID_VENT_HOLE_COUNT):
            angle = tau * index / LID_VENT_HOLE_COUNT
            with Locations(
                (
                    LID_VENT_RING_RADIUS * cos(angle),
                    LID_VENT_RING_RADIUS * sin(angle),
                    vent_center_z,
                )
            ):
                Cylinder(
                    LID_VENT_HOLE_RADIUS,
                    LID_TOP_THICKNESS + 1.0,
                    mode=Mode.SUBTRACT,
                )

        add(
            Location((0, 0, LID_TOP_SURFACE_Z - LID_HEX_POCKET_DEPTH))
            * _make_lid_hex_weight_pocket_cutters(),
            mode=Mode.SUBTRACT,
        )

        add(
            Location(
                (
                    LID_LOGO_CENTER[0],
                    LID_LOGO_CENTER[1],
                    LID_TOP_SURFACE_Z - LID_LOGO_ENGRAVE_DEPTH,
                )
            )
            * _make_lid_logo_engraving(),
            mode=Mode.SUBTRACT,
        )

    return tag(lid.part, "M4-fastened flat disk robot service lid", PRINTED_FRAME)


def place_repeat_drive_motor_on_x_axis(side: int):
    rotation_y = 90 * side
    motor = REPEAT_COMPACT_1806.load()
    placed = (
        Location(
            (
                side * (ROBOT_MOTOR_FACE_X - MOTOR_STEP_FACE_Z),
                ROBOT_AXLE_Y,
                ROBOT_AXLE_Z,
            ),
            (0, rotation_y, 0),
        )
        * motor
    )
    label = (
        "right Repeat Compact 1806 gearmotor"
        if side > 0
        else "left Repeat Compact 1806 gearmotor"
    )
    return tag(placed, label, SILVER)


def place_wheel_on_x_axis(side: int):
    wheel = make_tpu_d_bore_wheel(radius=ROBOT_WHEEL_RADIUS)
    placed = Location(
        (side * ROBOT_WHEEL_CENTER_X, ROBOT_AXLE_Y, ROBOT_AXLE_Z),
        (0, 0, 90),
    ) * wheel
    label = "right TPU press-fit wheel" if side > 0 else "left TPU press-fit wheel"
    return tag(placed, label, TPU_BLACK)


def place_as5600_encoder(side: int):
    encoder = AS5600_ENCODER.load()
    encoder_center_x = ROBOT_MOTOR_REAR_X - ENCODER_SENSOR_GAP - AS5600_BOARD_THICKNESS / 2
    placed = (
        Location(
            (
                side * encoder_center_x,
                ROBOT_AXLE_Y,
                ROBOT_AXLE_Z,
            ),
            (0, 90 * side, 0),
        )
        * encoder
    )
    label = "right AS5600 drive encoder" if side > 0 else "left AS5600 drive encoder"
    return tag(placed, label, BLUE)


def place_encoder_magnet(side: int):
    magnet_center_x = ROBOT_MOTOR_REAR_X - ENCODER_MAGNET_THICKNESS / 2
    magnet = Location((side * magnet_center_x, ROBOT_AXLE_Y, ROBOT_AXLE_Z)) * Cylinder(
        ENCODER_MAGNET_RADIUS,
        ENCODER_MAGNET_THICKNESS,
        rotation=(0, 90, 0),
    )
    label = "right glued encoder magnet" if side > 0 else "left glued encoder magnet"
    return tag(magnet, label, BLACK)


def place_esp32_s3_sense():
    esp32 = XIAO_ESP32S3_SENSE.load()
    placed = Location(ESP32_CENTER, (0, 90, 0)) * esp32
    return tag(placed, "XIAO ESP32-S3 Sense controller reference, USB down", BLACK)


def place_ov2640_camera():
    camera = OV2640_21MM_160_CAMERA.load()
    placed = Location(OV2640_CAMERA_CENTER) * camera
    return tag(placed, "front OV2640 160 degree camera", BLACK)


def place_tof_sensor_forward():
    tof = make_tof_sensor_board()
    placed = Location(TOF_CENTER, TOF_ROTATION) * tof
    return tag(placed, "flipped forward-facing TOF sensor board", COPPER_GOLD)


def place_radar_forward():
    radar = make_forward_radar_module()
    placed = Location(RADAR_CENTER, (-90, 0, 0)) * radar
    return tag(placed, "forward-facing radar module", COPPER_GOLD)


def place_small_4s_battery():
    battery = make_small_4s_battery()
    placed = Location(BATTERY_CENTER, (0, 0, 90)) * battery
    return tag(placed, "centered 4S 1550 mAh battery", BLACK)


def _motor_screw_heads(side: int):
    screw_heads = []
    for index, (y_offset, z_offset) in enumerate(motor_bolt_circle_offsets(), start=1):
        screw = Location(
            (
                side
                * (
                    ROBOT_MOTOR_FACE_X
                    + MOTOR_PLATE_THICKNESS
                    + M2_COUNTERBORE_DEPTH / 2
                ),
                ROBOT_AXLE_Y + y_offset,
                ROBOT_AXLE_Z + z_offset,
            )
        ) * Cylinder(
            M2_COUNTERBORE_RADIUS * 0.82,
            M2_COUNTERBORE_DEPTH,
            rotation=(0, 90, 0),
        )
        screw_heads.append(tag(screw, f"M2 motor screw head {index}", SILVER))
    return screw_heads


def make_lid_screw_reference(index: int, x: float, y: float):
    shank_top_z = LID_TOP_CENTER_Z + LID_TOP_THICKNESS / 2
    head_center_z = shank_top_z + M4_SOCKET_HEAD_HEIGHT / 2
    shank_bottom_z = LID_PAD_BOTTOM_Z - (M4_INSERT_POCKET_DEPTH - 1.0)
    shank_length = shank_top_z - shank_bottom_z

    with BuildPart() as screw:
        with Locations((x, y, head_center_z)):
            Cylinder(M4_SOCKET_HEAD_RADIUS, M4_SOCKET_HEAD_HEIGHT)
        with Locations((x, y, shank_bottom_z + shank_length / 2)):
            Cylinder(M4_SHANK_RADIUS, shank_length)

    return tag(screw.part, f"M4 lid screw {index} clearance reference", SILVER)


def make_lid_driver_access_reference(index: int, x: float, y: float):
    return make_vertical_access_keepout(
        label=f"M4 lid driver access {index} keep-out",
        x=x,
        y=y,
        z_min=M4_DRIVER_ACCESS_Z_MIN,
        z_max=M4_DRIVER_ACCESS_Z_MAX,
        radius=M4_DRIVER_ACCESS_RADIUS,
        color=OFF_WHITE,
        alpha=0.1,
    )


def make_flat_disk_robot(*, include_lid_driver_access_refs: bool = False) -> Compound:
    """Reference assembly for the flat differential-drive robot."""

    children = [
        make_flat_disk_robot_chassis(),
        make_flat_disk_robot_lid(),
        place_small_4s_battery(),
        place_esp32_s3_sense(),
        place_ov2640_camera(),
        place_tof_sensor_forward(),
        place_radar_forward(),
    ]

    for index, (x, y) in enumerate(LID_MOUNT_POINTS, start=1):
        children.append(make_lid_screw_reference(index, x, y))
        if include_lid_driver_access_refs:
            children.append(make_lid_driver_access_reference(index, x, y))

    for side in [-1, 1]:
        children.append(place_repeat_drive_motor_on_x_axis(side))
        children.append(place_wheel_on_x_axis(side))
        children.append(place_encoder_magnet(side))
        children.append(place_as5600_encoder(side))
        children.extend(_motor_screw_heads(side))

    return Compound(children=children, label="flat-disk-robot")
