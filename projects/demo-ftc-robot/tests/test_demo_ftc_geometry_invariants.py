from types import SimpleNamespace

import pytest

import synthcad.library as shared_library
from synthcad.inspection import bounding_box_summary
from synthcad.projects.demo_ftc_robot import parts
from synthcad.projects.demo_ftc_robot.parts import (
    YELLOWJACKET_BODY_DIAMETER_MM,
    YELLOWJACKET_TOTAL_LENGTH_MM,
    make_yellowjacket_motor_proxy,
)
from synthcad.projects.demo_ftc_robot.robot import (
    ARTIFACT_CAPACITY,
    ARTIFACT_CENTERS_MM,
    ARTIFACT_DIAMETER_MM,
    DRIVE_WHEEL_COUNT,
    DRIVE_WHEEL_DIAMETER_MM,
    DRIVE_WHEEL_WIDTH_MM,
    FLYWHEEL_DIAMETER_MM,
    FLYWHEEL_CENTER_MM,
    FLYWHEEL_COMPRESSION_MM,
    FRONT_DIRECTION,
    FTC_STARTING_CUBE_MM,
    HOOD_ROLLER_COMPRESSION_MM,
    HOOD_ROLLER_DIAMETER_MM,
    HOOD_ROLLER_CENTERS_MM,
    INTAKE_ROLLER_CENTER_MM,
    INDEXER_ROLLER_CENTER_MM,
    SHOOTER_BALL_PATH_CENTERS_MM,
    TARGET_ENVELOPE_MM,
    make_demo_ftc_robot,
)
from synthcad.review_assets import build_display_snapshot


def _children():
    return tuple(make_demo_ftc_robot().children)


def _children_matching(token: str):
    token = token.lower()
    return [child for child in _children() if token in child.label.lower()]


def _yz_distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return ((first[1] - second[1]) ** 2 + (first[2] - second[2]) ** 2) ** 0.5


def test_demo_ftc_robot_fits_requested_16_in_concept_envelope() -> None:
    bbox = bounding_box_summary(make_demo_ftc_robot())

    assert bbox["size"][0] <= TARGET_ENVELOPE_MM[0] + 0.1
    assert bbox["size"][1] <= TARGET_ENVELOPE_MM[1] + 0.1
    assert bbox["size"][2] <= TARGET_ENVELOPE_MM[2] + 0.1
    assert max(bbox["size"]) < FTC_STARTING_CUBE_MM


def test_demo_ftc_robot_models_three_decode_artifacts() -> None:
    artifacts = _children_matching("stored decode artifact")

    assert len(artifacts) == ARTIFACT_CAPACITY
    for artifact, expected_center in zip(artifacts, ARTIFACT_CENTERS_MM, strict=True):
        assert bounding_box_summary(artifact)["center"] == pytest.approx(expected_center, abs=0.1)
    for artifact in artifacts:
        assert bounding_box_summary(artifact)["size"] == pytest.approx(
            (ARTIFACT_DIAMETER_MM, ARTIFACT_DIAMETER_MM, ARTIFACT_DIAMETER_MM),
            abs=0.1,
        )


def test_demo_ftc_robot_has_six_wheel_drive_layout() -> None:
    drive_wheels = _children_matching("drive wheel")

    assert len(drive_wheels) == DRIVE_WHEEL_COUNT
    for wheel in drive_wheels:
        assert bounding_box_summary(wheel)["size"] == pytest.approx(
            (DRIVE_WHEEL_WIDTH_MM, DRIVE_WHEEL_DIAMETER_MM, DRIVE_WHEEL_DIAMETER_MM),
            abs=0.1,
        )

    front_wheels = [wheel for wheel in drive_wheels if "front" in wheel.label]
    rear_wheels = [wheel for wheel in drive_wheels if "rear" in wheel.label]
    assert len(front_wheels) == 2
    assert len(rear_wheels) == 2
    assert all(bounding_box_summary(wheel)["center"][1] > 0 for wheel in front_wheels)
    assert all(bounding_box_summary(wheel)["center"][1] < 0 for wheel in rear_wheels)


def test_intake_indexer_and_shooter_point_toward_robot_front() -> None:
    assert FRONT_DIRECTION == (0.0, 1.0, 0.0)
    assert INTAKE_ROLLER_CENTER_MM[1] > 0
    assert INDEXER_ROLLER_CENTER_MM[1] > 0
    assert FLYWHEEL_CENTER_MM[1] > 0
    assert INDEXER_ROLLER_CENTER_MM[1] < FLYWHEEL_CENTER_MM[1] < INTAKE_ROLLER_CENTER_MM[1]

    flywheel = _children_matching("72 mm flywheel shooter wheel")[0]
    assert bounding_box_summary(flywheel)["size"][1] == pytest.approx(FLYWHEEL_DIAMETER_MM, abs=0.1)

    hood_rollers = _children_matching("lid-mounted 1 in hood roller")
    assert len(hood_rollers) == len(HOOD_ROLLER_CENTERS_MM)
    for roller in hood_rollers:
        assert bounding_box_summary(roller)["size"][1] == pytest.approx(
            HOOD_ROLLER_DIAMETER_MM,
            abs=0.1,
        )


def test_shooter_path_places_ball_above_flywheel_under_hood_rollers() -> None:
    flywheel_contact_center = SHOOTER_BALL_PATH_CENTERS_MM[0]
    hood_contact_centers = SHOOTER_BALL_PATH_CENTERS_MM[:2]

    assert all(center[2] > FLYWHEEL_CENTER_MM[2] for center in SHOOTER_BALL_PATH_CENTERS_MM)
    assert all(roller[2] > center[2] for roller, center in zip(
        HOOD_ROLLER_CENTERS_MM,
        hood_contact_centers,
        strict=True,
    ))

    flywheel_contact_distance = (
        ARTIFACT_DIAMETER_MM / 2
        + FLYWHEEL_DIAMETER_MM / 2
        - FLYWHEEL_COMPRESSION_MM
    )
    hood_contact_distance = (
        ARTIFACT_DIAMETER_MM / 2
        + HOOD_ROLLER_DIAMETER_MM / 2
        - HOOD_ROLLER_COMPRESSION_MM
    )

    assert _yz_distance(FLYWHEEL_CENTER_MM, flywheel_contact_center) == pytest.approx(
        flywheel_contact_distance,
        abs=1.0,
    )
    for roller_center, ball_center in zip(
        HOOD_ROLLER_CENTERS_MM,
        hood_contact_centers,
        strict=True,
    ):
        assert _yz_distance(roller_center, ball_center) == pytest.approx(
            hood_contact_distance,
            abs=1.5,
        )


def test_demo_ftc_robot_has_structural_crayon_parts() -> None:
    required_tokens = (
        "flat drivetrain side plate",
        "frame standoff",
        "front intake side plate",
        "queue sidewall plate",
        "shooter side plate",
        "flywheel live shaft",
        "top service plate",
    )

    labels = [child.label.lower() for child in _children()]
    for token in required_tokens:
        assert any(token in label for label in labels), f"missing structural token {token!r}"


def test_yellowjacket_proxy_is_project_owned_not_shared_crayon_library() -> None:
    assert make_yellowjacket_motor_proxy.__module__ == parts.__name__
    assert "crayon_yellowjacket_motor" not in shared_library.__all__

    motor = make_yellowjacket_motor_proxy(
        "test Yellow Jacket",
        (0.0, 0.0, 0.0),
        axis="x",
    )
    assert bounding_box_summary(motor)["size"] == pytest.approx(
        (
            YELLOWJACKET_TOTAL_LENGTH_MM,
            YELLOWJACKET_BODY_DIAMETER_MM,
            YELLOWJACKET_BODY_DIAMETER_MM,
        ),
        abs=0.1,
    )


def test_demo_ftc_robot_snapshot_exposes_distinct_planning_colors() -> None:
    target = SimpleNamespace(
        name="demo-ftc-robot",
        kind="robot-planning-assembly",
        project="demo-ftc-robot",
        status="concept",
        printable=False,
    )
    snapshot = build_display_snapshot(target, make_demo_ftc_robot())
    colors = {
        child["color"]["hex"]
        for child in snapshot["children"]
        if child.get("color")
    }

    assert len(colors) >= 8
