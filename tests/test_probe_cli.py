import json

from build123d import Box, Compound, Location

import synthcad.probe_cli as probe_module
from synthcad.build import BuildTarget


def _make_target() -> BuildTarget:
    def factory():
        first = Box(4, 6, 8)
        first.label = "first solid"
        second = Location((10, 0, 0)) * Box(2, 2, 2)
        second.label = "mast bracket"
        return Compound(children=[first, second], label="full target")

    def inspection_factory():
        proxy = Box(3, 3, 3)
        proxy.label = "mast proxy"
        return Compound(children=[proxy], label="inspection target")

    return BuildTarget(
        name="probe-target",
        factory=factory,
        kind="reference-assembly",
        source_module="tests.test_probe_cli",
        printable=False,
        project="probe-project",
        status="sandbox",
        inspection_factory=inspection_factory,
        formats=("glb",),
    )


def test_probe_cli_json_uses_inspection_model(monkeypatch, capsys) -> None:
    monkeypatch.setattr(probe_module, "BUILD_TARGETS", [_make_target()])

    result = probe_module.main(["--target", "probe-target", "--inspection-model", "--json"])

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["target"]["name"] == "probe-target"
    assert payload[0]["model_source"] == "inspection-factory"
    assert payload[0]["model_summary"]["label"] == "inspection target"
    assert payload[0]["filtered_child_count"] == 1


def test_probe_cli_text_filters_children_by_label(monkeypatch, capsys) -> None:
    monkeypatch.setattr(probe_module, "BUILD_TARGETS", [_make_target()])

    result = probe_module.main(
        [
            "--target",
            "probe-target",
            "--children",
            "--label-contains",
            "mast",
            "--child-limit",
            "0",
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert "probe-target [reference-assembly]" in output
    assert "filtered=1" in output
    assert "mast bracket" in output
    assert "first solid" not in output
