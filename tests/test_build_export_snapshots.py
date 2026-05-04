import json
from pathlib import Path

from build123d import Box, Compound, Location

import synthcad.build as build_module
from synthcad.build import BuildTarget, export_targets


def _make_target(name: str) -> BuildTarget:
    def factory():
        first = Box(2, 2, 2)
        first.label = "first child"
        second = Location((5, 0, 0)) * Box(2, 2, 2)
        second.label = "second child"
        return Compound(children=[first, second], label="export snapshot target")

    return BuildTarget(
        name=name,
        factory=factory,
        kind="reference-assembly",
        source_module="tests.test_build_export_snapshots",
        printable=False,
        project="build-export-test",
        status="sandbox",
        formats=("glb",),
    )


def test_export_targets_writes_display_snapshot_and_manifest_entry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    target = _make_target("snapshot-export-target")

    def fake_export_model(model, path_base: Path, formats):
        written = []
        for fmt in formats:
            output_path = Path(f"{path_base}.{fmt}")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(b"artifact")
            written.append(output_path)
        return written

    monkeypatch.setattr(build_module, "export_model", fake_export_model)

    written = export_targets([target], output_dir=tmp_path)

    snapshot_path = tmp_path / target.project / f"{target.name}.snapshot.json"
    manifest_path = tmp_path / "manifest.json"

    assert snapshot_path in written
    assert manifest_path in written

    snapshot = json.loads(snapshot_path.read_text())
    assert snapshot["target"]["name"] == target.name
    assert [child["label"] for child in snapshot["children"]] == [
        "first child",
        "second child",
    ]

    manifest = json.loads(manifest_path.read_text())
    assert manifest[0]["display_snapshot"] == str(snapshot_path)
    assert manifest[0]["outputs"] == [
        str(tmp_path / target.project / f"{target.name}.glb")
    ]
