from functools import lru_cache
from pathlib import Path

import pytest
from build123d import Box, Compound, Location

from synthcad.build import BUILD_TARGETS, target_lookup
from synthcad.inspection import (
    find_interferences,
    render_highlighted_projection_svg,
    render_projection_svg,
)


@lru_cache(maxsize=None)
def _interference_pairs(target_name: str) -> set[tuple[str, str]]:
    target = target_lookup()[target_name]
    report = find_interferences(target.factory())
    return {
        tuple(sorted((interference.first, interference.second)))
        for interference in report.interferences
    }


def test_find_interferences_reports_expected_overlap_volume() -> None:
    first = Box(2, 2, 2)
    first.label = "first"
    second = Location((1, 0, 0)) * Box(2, 2, 2)
    second.label = "second"

    report = find_interferences(Compound(children=[first, second], label="test-overlap"))

    assert report.child_count == 2
    assert len(report.interferences) == 1
    interference = report.interferences[0]
    assert {interference.first, interference.second} == {"first", "second"}
    assert interference.volume_mm3 == pytest.approx(4.0, abs=1e-6)


def test_render_projection_svg_writes_svg_file(tmp_path: Path) -> None:
    output_path = render_projection_svg(Box(10, 20, 30), tmp_path / "box.svg")
    assert output_path.exists()
    assert "<svg" in output_path.read_text(encoding="utf-8")


def test_render_highlighted_projection_svg_writes_svg_file(tmp_path: Path) -> None:
    highlighted = Location((5, 0, 0)) * Box(4, 4, 4)
    output_path = render_highlighted_projection_svg(
        Compound(children=[Box(10, 10, 10), highlighted]),
        [highlighted],
        tmp_path / "highlight.svg",
    )
    assert output_path.exists()
    assert "<svg" in output_path.read_text(encoding="utf-8")


def test_validation_interference_targets_without_declared_exceptions_are_clean() -> None:
    lookup = target_lookup()
    for target in BUILD_TARGETS:
        for assembly_name in target.validation.interference_targets:
            assembly_target = lookup[assembly_name]
            if assembly_target.intentional_interferences:
                continue
            assert _interference_pairs(assembly_name) == set(), (
                f"{assembly_name} has unexpected interferences"
            )
