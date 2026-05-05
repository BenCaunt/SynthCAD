from __future__ import annotations

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

DRIVE_WHEEL_DIAMETER_MM = 96.0
DRIVE_WHEEL_RADIUS_MM = DRIVE_WHEEL_DIAMETER_MM / 2
DRIVE_WHEEL_WIDTH_MM = 24.0
DRIVE_WHEEL_X_MM = 188.0
DRIVE_WHEEL_Y_POSITIONS_MM = (-126.0, 0.0, 126.0)
DRIVE_WHEEL_CENTER_Z_MM = DRIVE_WHEEL_RADIUS_MM
DRIVE_WHEEL_COUNT = 6

INTAKE_ROLLER_DIAMETER_MM = 38.0
INTAKE_ROLLER_WIDTH_MM = 310.0
INTAKE_ROLLER_CENTER_MM = (0.0, 174.0, 78.0)
INDEXER_ROLLER_DIAMETER_MM = 25.4
INDEXER_ROLLER_WIDTH_MM = 160.0
INDEXER_ROLLER_CENTER_MM = (0.0, 58.0, 154.0)

FLYWHEEL_DIAMETER_MM = 72.0
FLYWHEEL_WIDTH_MM = 42.0
FLYWHEEL_CENTER_MM = (0.0, 126.0, 236.0)
HOOD_ROLLER_DIAMETER_MM = 25.4
HOOD_ROLLER_WIDTH_MM = 170.0
HOOD_ROLLER_CENTERS_MM = (
    (0.0, 132.0, 286.0),
    (0.0, 172.0, 312.0),
)

FRONT_DIRECTION = (0.0, 1.0, 0.0)


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
            "top lid and hood roller mounting plate",
            (0.0, 22.0, 326.0),
            (316.0, 332.0, 6.0),
            CRAYON_FRAME,
            alpha=0.5,
            intent=CrayonIntent(
                interfaces=("1 in hood roller axles", "shooter hood", "service access"),
                refine_with=("removable lid", "bearing pockets", "fasteners"),
            ),
        ),
    ]


def _drive_children():
    children = []
    for side_label, x, shaft_direction in (
        ("left", -DRIVE_WHEEL_X_MM, -1),
        ("right", DRIVE_WHEEL_X_MM, 1),
    ):
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
    return children


def _intake_and_indexer_children():
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
            "three artifact queue channel",
            (0.0, -6.0, 116.0),
            (146.0, 342.0, 132.0),
            CRAYON_INDEXER,
            alpha=0.24,
            intent=CrayonIntent(
                interfaces=("3 artifact capacity", "main intake handoff", "shooter feed wheel"),
                refine_with=("sidewalls", "polycarbonate guides", "anti-jam clearances"),
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
    return [
        crayon_box(
            "front-facing shooter throat envelope",
            (0.0, 148.0, 252.0),
            (154.0, 94.0, 88.0),
            CRAYON_SHOOTER,
            alpha=0.3,
            intent=CrayonIntent(
                interfaces=("artifact feed tangent", "front shot exit", "hood roller path"),
                refine_with=("hood plates", "flywheel guard", "compression tuning"),
            ),
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
        make_yellowjacket_motor_proxy(
            "shooter Yellow Jacket proxy",
            (-124.0, 112.0, 236.0),
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
        crayon_box(
            "front shooter exit keepout",
            (0.0, 184.0, 252.0),
            (136.0, 34.0, 62.0),
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
