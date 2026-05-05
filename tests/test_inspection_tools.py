from pathlib import Path

import pytest
from build123d import Box, Color, Compound, Location

from synthcad.build import target_lookup
from synthcad.inspect_cli import _default_output_dir
from synthcad.inspection import (
    find_interferences,
    render_highlighted_projection_svg,
    render_projection_svg,
    render_quick_detail_svg,
)
from synthcad.paths import project_generated_dir


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


def test_render_quick_detail_svg_writes_colored_labeled_overview(tmp_path: Path) -> None:
    first = Box(10, 20, 30)
    first.label = "red planning block"
    first.color = Color("#ff0000")
    second = Location((20, 0, 0)) * Box(8, 8, 8)
    second.label = "green planning block"
    second.color = Color("#00ff00")

    output_path = render_quick_detail_svg(
        Compound(children=[first, second], label="detail target"),
        tmp_path / "detail.svg",
    )
    content = output_path.read_text(encoding="utf-8")

    assert output_path.exists()
    assert "red planning block" in content
    assert "green planning block" in content
    assert "#ff0000" in content
    assert "#00ff00" in content


def test_inspect_cli_defaults_to_selected_project_generated_dir() -> None:
    target = target_lookup()["demo-ftc-robot"]
    assert _default_output_dir([target]) == project_generated_dir("demo-ftc-robot") / "inspection"
