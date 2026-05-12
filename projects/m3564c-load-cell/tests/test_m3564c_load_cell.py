from math import hypot

import pytest

from synthcad.build import target_lookup
from synthcad.cad.features import candidate_circular_holes
from synthcad.inspection import bounding_box_summary
from m3564c_load_cell.load_cell import (
    M3564C_CENTER_BORE_DIAMETER,
    M3564C_DOWEL_HOLE_COUNT_PER_FACE,
    M3564C_FACE_OFFSET,
    M3564C_OUTER_DIAMETER,
    M3564C_OUTER_RING_THICKNESS,
    M3564C_ROBOT_DOWEL_BOLT_CIRCLE_DIAMETER,
    M3564C_ROBOT_DOWEL_HOLE_DIAMETER,
    M3564C_ROBOT_M5_THREAD_COUNT,
    M3564C_ROBOT_M5_THREAD_DIAMETER,
    M3564C_ROBOT_MOUNT_BOLT_CIRCLE_DIAMETER,
    M3564C_TOOL_CLEARANCE_BOLT_CIRCLE_DIAMETER,
    M3564C_TOOL_CLEARANCE_HOLE_COUNT,
    M3564C_TOOL_CLEARANCE_HOLE_DIAMETER,
    M3564C_TOOL_DOWEL_BOLT_CIRCLE_DIAMETER,
    M3564C_TOOL_DOWEL_HOLE_DIAMETER,
    M3564C_TOTAL_HEIGHT,
    make_m3564c_load_cell,
)


def _body_child():
    model = make_m3564c_load_cell()
    for child in model.children:
        if getattr(child, "label", "") == "M3564C machined load-cell body":
            return child
    raise AssertionError("M3564C machined body child was not found")


def _features_on_bolt_circle(shape, *, diameter: float, hole_diameter: float):
    features = candidate_circular_holes(
        shape,
        radius_min=hole_diameter / 2 - 0.05,
        radius_max=hole_diameter / 2 + 0.05,
    )
    return [
        feature
        for feature in features
        if hypot(feature.center[0], feature.center[1])
        == pytest.approx(diameter / 2, abs=0.05)
    ]


def test_m3564c_build_target_registered_with_source_pdf() -> None:
    target = target_lookup()["m3564c-six-axis-load-cell"]

    assert target.project == "m3564c-load-cell"
    assert target.kind == "vendor-reference-part"
    assert target.printable is False
    assert target.source_refs == (
        "projects/m3564c-load-cell/real-parts/m3564c-drawing.pdf",
    )


def test_m3564c_body_matches_drawing_envelope() -> None:
    body = _body_child()
    bbox = bounding_box_summary(body)

    assert bbox["size"] == pytest.approx(
        (
            M3564C_OUTER_DIAMETER,
            M3564C_OUTER_DIAMETER,
            M3564C_TOTAL_HEIGHT,
        ),
        abs=0.01,
    )
    assert M3564C_TOTAL_HEIGHT == pytest.approx(
        M3564C_OUTER_RING_THICKNESS + M3564C_FACE_OFFSET,
        abs=1e-6,
    )


def test_m3564c_through_hole_patterns_match_drawing() -> None:
    body = _body_child()

    center_bores = _features_on_bolt_circle(
        body,
        diameter=0.0,
        hole_diameter=M3564C_CENTER_BORE_DIAMETER,
    )
    tool_clearance_holes = _features_on_bolt_circle(
        body,
        diameter=M3564C_TOOL_CLEARANCE_BOLT_CIRCLE_DIAMETER,
        hole_diameter=M3564C_TOOL_CLEARANCE_HOLE_DIAMETER,
    )
    robot_m5_holes = _features_on_bolt_circle(
        body,
        diameter=M3564C_ROBOT_MOUNT_BOLT_CIRCLE_DIAMETER,
        hole_diameter=M3564C_ROBOT_M5_THREAD_DIAMETER,
    )

    assert len(center_bores) == 1
    assert len(tool_clearance_holes) == M3564C_TOOL_CLEARANCE_HOLE_COUNT
    assert len(robot_m5_holes) == M3564C_ROBOT_M5_THREAD_COUNT


def test_m3564c_blind_dowel_pockets_match_drawing_bolt_circles() -> None:
    body = _body_child()

    tool_dowels = _features_on_bolt_circle(
        body,
        diameter=M3564C_TOOL_DOWEL_BOLT_CIRCLE_DIAMETER,
        hole_diameter=M3564C_TOOL_DOWEL_HOLE_DIAMETER,
    )
    robot_dowels = _features_on_bolt_circle(
        body,
        diameter=M3564C_ROBOT_DOWEL_BOLT_CIRCLE_DIAMETER,
        hole_diameter=M3564C_ROBOT_DOWEL_HOLE_DIAMETER,
    )

    assert len(tool_dowels) == M3564C_DOWEL_HOLE_COUNT_PER_FACE
    assert len(robot_dowels) == M3564C_DOWEL_HOLE_COUNT_PER_FACE
