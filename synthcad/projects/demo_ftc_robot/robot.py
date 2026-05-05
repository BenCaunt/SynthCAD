from __future__ import annotations

from math import atan2, degrees, sqrt

from build123d import Compound

from synthcad.library.crayon import (
    CRAYON_DRIVE,
    CRAYON_FRAME,
    CRAYON_GAME_PIECE_GREEN,
    CRAYON_GAME_PIECE_PURPLE,
    CRAYON_INDEXER,
    CRAYON_INTAKE,
    CRAYON_KEEP_OUT,
    CRAYON_SENSOR,
    CRAYON_SHOOTER,
    CrayonIntent,
    crayon_box,
    crayon_cylinder,
    crayon_sphere,
)
from synthcad.projects.demo_ftc_robot.parts import make_yellowjacket_motor_proxy


INCH_MM = 25.4
TARGET_ENVELOPE_IN = (16.0, 16.0, 16.0)
TARGET_ENVELOPE_MM = tuple(value * INCH_MM for value in TARGET_ENVELOPE_IN)
FTC_STARTING_CUBE_IN = 18.0
FTC_STARTING_CUBE_MM = FTC_STARTING_CUBE_IN * INCH_MM

ARTIFACT_DIAMETER_IN = 5.0
ARTIFACT_DIAMETER_MM = ARTIFACT_DIAMETER_IN * INCH_MM
ARTIFACT_RADIUS_MM = ARTIFACT_DIAMETER_MM / 2
ARTIFACT_CAPACITY = 3
ARTIFACT_CENTERS_MM = (
    (0.0, -128.0, 116.0),
    (0.0, -2.0, 116.0),
    (0.0, 124.0, 116.0),
)

ROBOT_LENGTH_MM = TARGET_ENVELOPE_MM[1]
ROBOT_WIDTH_MM = TARGET_ENVELOPE_MM[0]
ROBOT_HEIGHT_MM = TARGET_ENVELOPE_MM[2]
FRAME_LENGTH_MM = 382.0
FRAME_WIDTH_MM = 360.0
FRAME_RAIL_THICKNESS_MM = 18.0
FRAME_RAIL_HEIGHT_MM = 34.0
FRAME_PLATE_THICKNESS_MM = 4.0
FRAME_SIDE_PLATE_HEIGHT_MM = 92.0
FRAME_STANDOFF_DIAMETER_MM = 12.0

DRIVE_WHEEL_DIAMETER_MM = 96.0
DRIVE_WHEEL_RADIUS_MM = DRIVE_WHEEL_DIAMETER_MM / 2
DRIVE_WHEEL_WIDTH_MM = 24.0
DRIVE_WHEEL_X_MM = 188.0
DRIVE_WHEEL_Y_POSITIONS_MM = (-126.0, 0.0, 126.0)
DRIVE_WHEEL_CENTER_Z_MM = DRIVE_WHEEL_RADIUS_MM
DRIVE_WHEEL_COUNT = 6
DRIVE_SHAFT_DIAMETER_MM = 8.0
DRIVE_PULLEY_DIAMETER_MM = 34.0
DRIVE_BELT_WIDTH_MM = 10.0
DRIVE_BELT_THICKNESS_MM = 4.0

INTAKE_ROLLER_DIAMETER_MM = 38.0
INTAKE_ROLLER_WIDTH_MM = 310.0
INTAKE_ROLLER_CENTER_MM = (0.0, 174.0, 78.0)
INTAKE_SIDE_PLATE_X_MM = 164.0
INTAKE_COMPLIANT_WHEEL_DIAMETER_MM = 60.0
INTAKE_COMPLIANT_WHEEL_WIDTH_MM = 18.0
INTAKE_COMPLIANT_WHEEL_X_POSITIONS_MM = (-120.0, -72.0, -24.0, 24.0, 72.0, 120.0)
INDEXER_ROLLER_DIAMETER_MM = 25.4
INDEXER_ROLLER_WIDTH_MM = 160.0
INDEXER_ROLLER_CENTER_MM = (0.0, 58.0, 154.0)
QUEUE_SIDEWALL_X_MM = 77.0

FLYWHEEL_DIAMETER_MM = 72.0
FLYWHEEL_WIDTH_MM = 42.0
FLYWHEEL_CENTER_MM = (0.0, 88.0, 210.0)
FLYWHEEL_COMPRESSION_MM = 8.0
HOOD_ROLLER_DIAMETER_MM = 25.4
HOOD_ROLLER_WIDTH_MM = 170.0
HOOD_ROLLER_COMPRESSION_MM = 4.8
HOOD_ROLLER_CENTERS_MM = (
    (0.0, 96.0, 368.0),
    (0.0, 140.0, 381.0),
)
SHOOTER_BALL_PATH_CENTERS_MM = (
    (0.0, 74.0, 300.0),
    (0.0, 116.0, 314.0),
    (0.0, 150.0, 334.0),
)

FRONT_DIRECTION = (0.0, 1.0, 0.0)


def _yz_span_box(
    label: str,
    x: float,
    start_yz: tuple[float, float],
    end_yz: tuple[float, float],
    *,
    width_x: float,
    thickness_z: float,
    color: str,
    alpha: float = 1.0,
    intent: CrayonIntent | None = None,
):
    start_y, start_z = start_yz
    end_y, end_z = end_yz
    delta_y = end_y - start_y
    delta_z = end_z - start_z
    return crayon_box(
        label,
        (x, (start_y + end_y) / 2, (start_z + end_z) / 2),
        (width_x, sqrt(delta_y**2 + delta_z**2), thickness_z),
        color,
        alpha=alpha,
        rotation=(degrees(atan2(delta_z, delta_y)), 0.0, 0.0),
        intent=intent,
    )


def _frame_children():
    side_rail_intent = CrayonIntent(
        interfaces=("16 in target envelope", "6 wheel drivetrain bearing line"),
        refine_with=("FTC channel or plate rails", "bearing blocks", "drive shaft supports"),
    )
    cross_rail_intent = CrayonIntent(
        interfaces=("front intake mount", "rear battery/service bay"),
        refine_with=("front/rear plates", "gussets", "fasteners"),
    )
    return [
        crayon_box(
            "left side frame rail blockout",
            (-FRAME_WIDTH_MM / 2, 0.0, 42.0),
            (FRAME_RAIL_THICKNESS_MM, FRAME_LENGTH_MM, FRAME_RAIL_HEIGHT_MM),
            CRAYON_FRAME,
            intent=side_rail_intent,
        ),
        crayon_box(
            "right side frame rail blockout",
            (FRAME_WIDTH_MM / 2, 0.0, 42.0),
            (FRAME_RAIL_THICKNESS_MM, FRAME_LENGTH_MM, FRAME_RAIL_HEIGHT_MM),
            CRAYON_FRAME,
            intent=side_rail_intent,
        ),
        crayon_box(
            "front frame cross rail and intake hardpoint",
            (0.0, FRAME_LENGTH_MM / 2 - FRAME_RAIL_THICKNESS_MM / 2, 42.0),
            (FRAME_WIDTH_MM, FRAME_RAIL_THICKNESS_MM, FRAME_RAIL_HEIGHT_MM),
            CRAYON_FRAME,
            intent=cross_rail_intent,
        ),
        crayon_box(
            "rear frame cross rail",
            (0.0, -FRAME_LENGTH_MM / 2 + FRAME_RAIL_THICKNESS_MM / 2, 42.0),
            (FRAME_WIDTH_MM, FRAME_RAIL_THICKNESS_MM, FRAME_RAIL_HEIGHT_MM),
            CRAYON_FRAME,
            intent=cross_rail_intent,
        ),
        crayon_box(
            "thin electronics bellypan blockout",
            (0.0, -22.0, 18.0),
            (312.0, 300.0, 5.0),
            "#64748b",
            intent=CrayonIntent(
                interfaces=("REV control hub", "battery", "wire routing"),
                refine_with=("mounting holes", "standoffs", "wire pass-throughs"),
            ),
        ),
        crayon_box(
            "left flat drivetrain side plate",
            (-172.0, 0.0, 84.0),
            (FRAME_PLATE_THICKNESS_MM, 344.0, FRAME_SIDE_PLATE_HEIGHT_MM),
            CRAYON_FRAME,
            alpha=0.82,
            intent=CrayonIntent(
                interfaces=("drive bearing line", "Yellow Jacket motor mounts", "front intake plate"),
                refine_with=("waterjet side plate", "bearing holes", "motor slots"),
            ),
        ),
        crayon_box(
            "right flat drivetrain side plate",
            (172.0, 0.0, 84.0),
            (FRAME_PLATE_THICKNESS_MM, 344.0, FRAME_SIDE_PLATE_HEIGHT_MM),
            CRAYON_FRAME,
            alpha=0.82,
            intent=CrayonIntent(
                interfaces=("drive bearing line", "Yellow Jacket motor mounts", "front intake plate"),
                refine_with=("waterjet side plate", "bearing holes", "motor slots"),
            ),
        ),
        *[
            crayon_cylinder(
                f"{label} 12 mm frame standoff",
                (0.0, y, z),
                radius=FRAME_STANDOFF_DIAMETER_MM / 2,
                length=326.0,
                axis="x",
                color="#94a3b8",
                intent=CrayonIntent(
                    interfaces=("left side plate", "right side plate"),
                    refine_with=("threaded standoff", "spacers", "through bolts"),
                ),
            )
            for label, y, z in (
                ("rear upper", -150.0, 116.0),
                ("center lower", -12.0, 72.0),
                ("front upper", 150.0, 116.0),
            )
        ],
        crayon_box(
            "removable top service plate and shooter hood bridge",
            (0.0, 92.0, 397.0),
            (260.0, 214.0, 5.0),
            CRAYON_FRAME,
            alpha=0.58,
            intent=CrayonIntent(
                interfaces=("1 in hood roller axles", "shooter side plates", "service access"),
                refine_with=("removable top plate", "bearing pockets", "fastener pattern"),
            ),
        ),
    ]


def _drive_children():
    children = []
    for side_label, x, shaft_direction in (
        ("left", -DRIVE_WHEEL_X_MM, -1),
        ("right", DRIVE_WHEEL_X_MM, 1),
    ):
        plate_x = 172.0 * shaft_direction
        pulley_x = 154.0 * shaft_direction
        belt_intent = CrayonIntent(
            interfaces=("Yellow Jacket shaft pulley", "drive wheel pulley"),
            refine_with=("HTD belt", "pulley tooth counts", "tensioner slot"),
        )
        for position_label, y in (("rear", -126.0), ("center", 0.0), ("front", 126.0)):
            children.append(
                crayon_cylinder(
                    f"{side_label} {position_label} 96 mm drive wheel",
                    (x, y, DRIVE_WHEEL_CENTER_Z_MM),
                    radius=DRIVE_WHEEL_RADIUS_MM,
                    length=DRIVE_WHEEL_WIDTH_MM,
                    axis="x",
                    color=CRAYON_DRIVE,
                    intent=CrayonIntent(
                        interfaces=("wheel axle", "side rail bearing line"),
                        refine_with=("96 mm FTC traction wheel STEP", "bearings", "spacers"),
                    ),
                )
            )
            children.append(
                crayon_cylinder(
                    f"{side_label} {position_label} 8 mm axle shaft",
                    (178.0 * shaft_direction, y, DRIVE_WHEEL_CENTER_Z_MM),
                    radius=DRIVE_SHAFT_DIAMETER_MM / 2,
                    length=44.0,
                    axis="x",
                    color="#d1d5db",
                    intent=CrayonIntent(
                        interfaces=("96 mm wheel", "side plate bearing", "drive pulley"),
                        refine_with=("8 mm REX shaft", "bearings", "shaft collars"),
                    ),
                )
            )
            children.append(
                crayon_box(
                    f"{side_label} {position_label} drive bearing block",
                    (plate_x, y, DRIVE_WHEEL_CENTER_Z_MM),
                    (14.0, 24.0, 24.0),
                    "#64748b",
                    intent=CrayonIntent(
                        interfaces=("side plate", "8 mm drive axle"),
                        refine_with=("flanged bearing", "bolt pattern", "spacer stack"),
                    ),
                )
            )
            children.append(
                crayon_cylinder(
                    f"{side_label} {position_label} drive pulley",
                    (pulley_x, y, DRIVE_WHEEL_CENTER_Z_MM),
                    radius=DRIVE_PULLEY_DIAMETER_MM / 2,
                    length=12.0,
                    axis="x",
                    color="#111827",
                    intent=CrayonIntent(
                        interfaces=("8 mm axle", "drive belt"),
                        refine_with=("HTD pulley STEP", "set screws", "belt clearance"),
                    ),
                )
            )

        for y in (-84.0, 84.0):
            children.append(
                make_yellowjacket_motor_proxy(
                    f"{side_label} drive Yellow Jacket proxy y={y:g}",
                    (x * 0.64, y, 64.0),
                    axis="x",
                    shaft_direction=shaft_direction,
                    intent=CrayonIntent(
                        interfaces=("drive gearbox face", "wheel axle power transfer"),
                        refine_with=("real Yellow Jacket STEP", "pulley/sprocket", "mount plate"),
                    ),
                )
            )
            children.append(
                crayon_box(
                    f"{side_label} drive motor mount plate y={y:g}",
                    (plate_x * 0.88, y, 64.0),
                    (5.0, 56.0, 54.0),
                    "#6b7280",
                    intent=CrayonIntent(
                        interfaces=("Yellow Jacket gearbox face", "side plate", "belt tension slots"),
                        refine_with=("motor bolt circle", "slotted adjustment", "pulley guard"),
                    ),
                )
            )

        motor_rear_yz = (-84.0, 64.0)
        motor_front_yz = (84.0, 64.0)
        children.extend(
            [
                _yz_span_box(
                    f"{side_label} rear wheel drive belt span",
                    pulley_x,
                    motor_rear_yz,
                    (-126.0, DRIVE_WHEEL_CENTER_Z_MM),
                    width_x=DRIVE_BELT_WIDTH_MM,
                    thickness_z=DRIVE_BELT_THICKNESS_MM,
                    color="#111827",
                    alpha=0.72,
                    intent=belt_intent,
                ),
                _yz_span_box(
                    f"{side_label} center rear drive belt span",
                    pulley_x,
                    motor_rear_yz,
                    (0.0, DRIVE_WHEEL_CENTER_Z_MM),
                    width_x=DRIVE_BELT_WIDTH_MM,
                    thickness_z=DRIVE_BELT_THICKNESS_MM,
                    color="#111827",
                    alpha=0.72,
                    intent=belt_intent,
                ),
                _yz_span_box(
                    f"{side_label} center front drive belt span",
                    pulley_x,
                    motor_front_yz,
                    (0.0, DRIVE_WHEEL_CENTER_Z_MM),
                    width_x=DRIVE_BELT_WIDTH_MM,
                    thickness_z=DRIVE_BELT_THICKNESS_MM,
                    color="#111827",
                    alpha=0.72,
                    intent=belt_intent,
                ),
                _yz_span_box(
                    f"{side_label} front wheel drive belt span",
                    pulley_x,
                    motor_front_yz,
                    (126.0, DRIVE_WHEEL_CENTER_Z_MM),
                    width_x=DRIVE_BELT_WIDTH_MM,
                    thickness_z=DRIVE_BELT_THICKNESS_MM,
                    color="#111827",
                    alpha=0.72,
                    intent=belt_intent,
                ),
            ]
        )
    return children


def _intake_and_indexer_children():
    intake_side_plate_intent = CrayonIntent(
        interfaces=("front frame cross rail", "intake roller axle", "artifact side guidance"),
        refine_with=("polycarbonate side plates", "bearing blocks", "belt guard"),
    )
    queue_sidewall_intent = CrayonIntent(
        interfaces=("3 artifact queue", "indexer roller axle", "shooter feed throat"),
        refine_with=("polycarbonate sidewalls", "low-friction liners", "anti-jam relief"),
    )
    return [
        crayon_box(
            "front intake swept volume",
            (0.0, 168.0, 102.0),
            (328.0, 58.0, 100.0),
            CRAYON_INTAKE,
            alpha=0.28,
            intent=CrayonIntent(
                interfaces=("front frame cross rail", "artifact handoff to storage queue"),
                refine_with=("intake side plates", "compliant wheels", "belt path"),
            ),
        ),
        crayon_box(
            "left front intake side plate",
            (-INTAKE_SIDE_PLATE_X_MM, 158.0, 96.0),
            (5.0, 88.0, 100.0),
            CRAYON_INTAKE,
            alpha=0.75,
            intent=intake_side_plate_intent,
        ),
        crayon_box(
            "right front intake side plate",
            (INTAKE_SIDE_PLATE_X_MM, 158.0, 96.0),
            (5.0, 88.0, 100.0),
            CRAYON_INTAKE,
            alpha=0.75,
            intent=intake_side_plate_intent,
        ),
        crayon_cylinder(
            "front intake 8 mm roller shaft",
            INTAKE_ROLLER_CENTER_MM,
            radius=4.0,
            length=326.0,
            axis="x",
            color="#d1d5db",
            intent=CrayonIntent(
                interfaces=("intake side plate bearings", "compliant wheel stack", "intake pulley"),
                refine_with=("8 mm REX shaft", "spacers", "shaft collars"),
            ),
        ),
        crayon_cylinder(
            "front-facing main intake roller",
            INTAKE_ROLLER_CENTER_MM,
            radius=INTAKE_ROLLER_DIAMETER_MM / 2,
            length=INTAKE_ROLLER_WIDTH_MM,
            axis="x",
            color=CRAYON_INTAKE,
            intent=CrayonIntent(
                interfaces=("front artifact contact line", "intake motor belt path"),
                refine_with=("roller tube", "bearings", "compliant wheel stack"),
            ),
        ),
        *[
            crayon_cylinder(
                f"front intake compliant wheel {index}",
                (x, INTAKE_ROLLER_CENTER_MM[1], INTAKE_ROLLER_CENTER_MM[2]),
                radius=INTAKE_COMPLIANT_WHEEL_DIAMETER_MM / 2,
                length=INTAKE_COMPLIANT_WHEEL_WIDTH_MM,
                axis="x",
                color="#60a5fa",
                intent=CrayonIntent(
                    interfaces=("front intake shaft", "artifact contact patch"),
                    refine_with=("FTC compliant wheel STEP", "spacers", "durometer choice"),
                ),
            )
            for index, x in enumerate(INTAKE_COMPLIANT_WHEEL_X_POSITIONS_MM, start=1)
        ],
        *[
            crayon_box(
                f"{side} front intake bearing block",
                (x, INTAKE_ROLLER_CENTER_MM[1], INTAKE_ROLLER_CENTER_MM[2]),
                (14.0, 24.0, 28.0),
                "#60a5fa",
                intent=CrayonIntent(
                    interfaces=("front intake side plate", "intake shaft"),
                    refine_with=("flanged bearing", "bolt pattern", "guard clearance"),
                ),
            )
            for side, x in (("left", -INTAKE_SIDE_PLATE_X_MM), ("right", INTAKE_SIDE_PLATE_X_MM))
        ],
        crayon_cylinder(
            "front intake pulley",
            (-145.0, INTAKE_ROLLER_CENTER_MM[1], INTAKE_ROLLER_CENTER_MM[2]),
            radius=18.0,
            length=12.0,
            axis="x",
            color="#111827",
            intent=CrayonIntent(
                interfaces=("intake shaft", "intake belt"),
                refine_with=("HTD pulley STEP", "set screws", "belt guard"),
            ),
        ),
        _yz_span_box(
            "intake belt span",
            -145.0,
            (160.0, 84.0),
            (INTAKE_ROLLER_CENTER_MM[1], INTAKE_ROLLER_CENTER_MM[2]),
            width_x=10.0,
            thickness_z=4.0,
            color="#111827",
            alpha=0.72,
            intent=CrayonIntent(
                interfaces=("intake motor pulley", "intake roller pulley"),
                refine_with=("belt path", "tensioner slot", "guard"),
            ),
        ),
        make_yellowjacket_motor_proxy(
            "intake Yellow Jacket proxy",
            (-124.0, 160.0, 84.0),
            axis="x",
            shaft_direction=1,
            intent=CrayonIntent(
                interfaces=("intake roller power", "left side plate"),
                refine_with=("real Yellow Jacket STEP", "belt reduction", "guarding"),
            ),
        ),
        crayon_box(
            "three artifact queue swept volume",
            (0.0, -6.0, 116.0),
            (146.0, 342.0, 132.0),
            CRAYON_INDEXER,
            alpha=0.24,
            intent=CrayonIntent(
                interfaces=("3 artifact capacity", "main intake handoff", "shooter feed wheel"),
                refine_with=("sidewalls", "polycarbonate guides", "anti-jam clearances"),
            ),
        ),
        crayon_box(
            "left three-ball queue sidewall plate",
            (-QUEUE_SIDEWALL_X_MM, -6.0, 116.0),
            (5.0, 342.0, 132.0),
            CRAYON_INDEXER,
            alpha=0.78,
            intent=queue_sidewall_intent,
        ),
        crayon_box(
            "right three-ball queue sidewall plate",
            (QUEUE_SIDEWALL_X_MM, -6.0, 116.0),
            (5.0, 342.0, 132.0),
            CRAYON_INDEXER,
            alpha=0.78,
            intent=queue_sidewall_intent,
        ),
        crayon_box(
            "sloped queue floor feeding shooter throat",
            (0.0, 40.0, 132.0),
            (138.0, 184.0, 5.0),
            CRAYON_INDEXER,
            alpha=0.72,
            rotation=(-14.0, 0.0, 0.0),
            intent=CrayonIntent(
                interfaces=("stored artifacts", "second stage indexer", "flywheel throat"),
                refine_with=("polycarbonate ramp", "low-friction tape", "clearance slots"),
            ),
        ),
        crayon_cylinder(
            "front-facing second stage indexer wheel",
            INDEXER_ROLLER_CENTER_MM,
            radius=INDEXER_ROLLER_DIAMETER_MM / 2,
            length=INDEXER_ROLLER_WIDTH_MM,
            axis="x",
            color=CRAYON_INDEXER,
            intent=CrayonIntent(
                interfaces=("queued artifact release", "flywheel throat"),
                refine_with=("1 in roller", "bearing blocks", "timing pulley"),
            ),
        ),
        crayon_cylinder(
            "second stage indexer 8 mm shaft",
            INDEXER_ROLLER_CENTER_MM,
            radius=4.0,
            length=176.0,
            axis="x",
            color="#d1d5db",
            intent=CrayonIntent(
                interfaces=("queue sidewall bearings", "indexer roller", "indexer pulley"),
                refine_with=("8 mm shaft", "bearings", "shaft collars"),
            ),
        ),
        *[
            crayon_box(
                f"{side} second stage indexer bearing block",
                (x, INDEXER_ROLLER_CENTER_MM[1], INDEXER_ROLLER_CENTER_MM[2]),
                (14.0, 22.0, 28.0),
                CRAYON_INDEXER,
                intent=CrayonIntent(
                    interfaces=("queue sidewall plate", "indexer shaft"),
                    refine_with=("flanged bearing", "slot for compression", "fasteners"),
                ),
            )
            for side, x in (("left", -88.0), ("right", 88.0))
        ],
        crayon_cylinder(
            "second stage indexer pulley",
            (-88.0, INDEXER_ROLLER_CENTER_MM[1], INDEXER_ROLLER_CENTER_MM[2]),
            radius=16.0,
            length=12.0,
            axis="x",
            color="#111827",
            intent=CrayonIntent(
                interfaces=("indexer shaft", "indexer belt"),
                refine_with=("HTD pulley STEP", "belt guard", "spacer stack"),
            ),
        ),
        crayon_box(
            "indexer belt span",
            (-105.0, 50.0, 154.0),
            (42.0, 8.0, 5.0),
            "#111827",
            alpha=0.72,
            intent=CrayonIntent(
                interfaces=("indexer motor pulley", "second stage indexer pulley"),
                refine_with=("belt path", "tension slot", "guarding"),
            ),
        ),
        make_yellowjacket_motor_proxy(
            "indexer Yellow Jacket proxy",
            (-122.0, 42.0, 154.0),
            axis="x",
            shaft_direction=1,
            intent=CrayonIntent(
                interfaces=("second stage indexer wheel", "queue sidewall"),
                refine_with=("real Yellow Jacket STEP", "belt or gear handoff"),
            ),
        ),
    ]


def _shooter_children():
    side_plate_intent = CrayonIntent(
        interfaces=("flywheel shaft", "hood roller axles", "top service plate"),
        refine_with=("shooter side plates", "bearing holes", "compression slots"),
    )
    bearing_block_intent = CrayonIntent(
        interfaces=("hood roller axle", "shooter side plate"),
        refine_with=("bearing block", "slotted compression adjustment", "fasteners"),
    )
    return [
        crayon_box(
            "front-facing shooter ball path envelope above flywheel",
            (0.0, 124.0, 318.0),
            (154.0, 154.0, 128.0),
            CRAYON_SHOOTER,
            alpha=0.22,
            intent=CrayonIntent(
                interfaces=("artifact feed tangent", "front shot exit", "hood roller contact path"),
                refine_with=("hood plates", "flywheel guard", "compression tuning"),
            ),
        ),
        crayon_box(
            "left shooter side plate with roller slots",
            (-92.0, 124.0, 304.0),
            (5.0, 164.0, 162.0),
            CRAYON_SHOOTER,
            alpha=0.78,
            intent=side_plate_intent,
        ),
        crayon_box(
            "right shooter side plate with roller slots",
            (92.0, 124.0, 304.0),
            (5.0, 164.0, 162.0),
            CRAYON_SHOOTER,
            alpha=0.78,
            intent=side_plate_intent,
        ),
        crayon_cylinder(
            "72 mm flywheel shooter wheel",
            FLYWHEEL_CENTER_MM,
            radius=FLYWHEEL_DIAMETER_MM / 2,
            length=FLYWHEEL_WIDTH_MM,
            axis="x",
            color=CRAYON_SHOOTER,
            intent=CrayonIntent(
                interfaces=("front-facing launch tangent", "Yellow Jacket shooter motor"),
                refine_with=("72 mm flywheel STEP", "shaft", "bearings", "spacers"),
            ),
        ),
        crayon_cylinder(
            "8 mm flywheel live shaft",
            FLYWHEEL_CENTER_MM,
            radius=4.0,
            length=194.0,
            axis="x",
            color="#d1d5db",
            intent=CrayonIntent(
                interfaces=("flywheel", "shooter side plate bearings", "motor coupling"),
                refine_with=("8 mm REX shaft", "bearings", "shaft collars"),
            ),
        ),
        make_yellowjacket_motor_proxy(
            "shooter Yellow Jacket proxy",
            (-124.0, 74.0, 210.0),
            axis="x",
            shaft_direction=1,
            intent=CrayonIntent(
                interfaces=("flywheel shaft", "shooter side plate"),
                refine_with=("real Yellow Jacket STEP", "coupler", "flywheel hub"),
            ),
        ),
        *[
            crayon_cylinder(
                f"lid-mounted 1 in hood roller {index}",
                center,
                radius=HOOD_ROLLER_DIAMETER_MM / 2,
                length=HOOD_ROLLER_WIDTH_MM,
                axis="x",
                color="#f97316",
                intent=CrayonIntent(
                    interfaces=("top lid", "artifact compression path"),
                    refine_with=("1 in roller tube", "bearing pocket", "removable axle"),
                ),
            )
            for index, center in enumerate(HOOD_ROLLER_CENTERS_MM, start=1)
        ],
        *[
            crayon_box(
                f"{side} hood roller {index} bearing block",
                (x, center[1], center[2]),
                (14.0, 24.0, 30.0),
                "#fb923c",
                intent=bearing_block_intent,
            )
            for index, center in enumerate(HOOD_ROLLER_CENTERS_MM, start=1)
            for side, x in (("left", -92.0), ("right", 92.0))
        ],
        *[
            crayon_sphere(
                f"shooter ball path ghost {index}",
                center,
                radius=ARTIFACT_RADIUS_MM,
                color=CRAYON_KEEP_OUT,
                alpha=0.18,
                intent=CrayonIntent(
                    interfaces=("flywheel compression path", "hood roller compression path"),
                    refine_with=("dynamic shot simulation", "compression tuning", "exit angle"),
                ),
            )
            for index, center in enumerate(SHOOTER_BALL_PATH_CENTERS_MM, start=1)
        ],
        crayon_box(
            "front shooter exit keepout",
            (0.0, 190.0, 334.0),
            (136.0, 30.0, 72.0),
            CRAYON_KEEP_OUT,
            alpha=0.24,
            intent=CrayonIntent(
                interfaces=("front bumper/frame opening", "artifact launch path"),
                refine_with=("final exit slot", "guarding", "targeting camera clearance"),
            ),
        ),
    ]


def _artifact_children():
    colors = (CRAYON_GAME_PIECE_PURPLE, CRAYON_GAME_PIECE_GREEN, CRAYON_GAME_PIECE_PURPLE)
    return [
        crayon_sphere(
            f"stored DECODE artifact {index}",
            center,
            radius=ARTIFACT_RADIUS_MM,
            color=color,
            alpha=0.78,
            intent=CrayonIntent(
                interfaces=("3 artifact queue", "5 in nominal artifact diameter"),
                refine_with=("real artifact STEP", "compression allowance", "anti-jam guides"),
            ),
        )
        for index, (center, color) in enumerate(zip(ARTIFACT_CENTERS_MM, colors, strict=True), start=1)
    ]


def _electronics_children():
    return [
        crayon_box(
            "REV control hub placeholder",
            (54.0, -88.0, 56.0),
            (110.0, 72.0, 26.0),
            CRAYON_SENSOR,
            intent=CrayonIntent(
                interfaces=("electronics bellypan", "USB/service access", "wiring clearance"),
                refine_with=("REV Hub STEP", "mounting holes", "wire clips"),
            ),
        ),
        crayon_box(
            "12V FTC battery placeholder",
            (-66.0, -92.0, 52.0),
            (92.0, 48.0, 48.0),
            "#111111",
            intent=CrayonIntent(
                interfaces=("battery strap", "main power wiring", "service access"),
                refine_with=("legal FTC battery STEP", "retaining strap", "connector guard"),
            ),
        ),
    ]


def make_demo_ftc_robot() -> Compound:
    children = [
        *_frame_children(),
        *_drive_children(),
        *_intake_and_indexer_children(),
        *_shooter_children(),
        *_artifact_children(),
        *_electronics_children(),
    ]
    return Compound(children=children, label="demo-ftc-robot crayon concept")
