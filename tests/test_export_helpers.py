from pathlib import Path

from build123d import Box, Color, Compound, Location

import synthcad.cad.common as common
import synthcad.external_parts as external_parts
from synthcad.external_parts import ExternalPart
from glb_helpers import glb_material_colors


def test_export_model_uses_viewer_focused_glb_tessellation(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_export_gltf(model, path, **kwargs):
        captured["model"] = model
        captured["path"] = Path(path)
        captured.update(kwargs)
        Path(path).write_bytes(b"glb")
        return True

    monkeypatch.setattr(common, "export_gltf", fake_export_gltf)

    written = common.export_model(Box(1, 2, 3), tmp_path / "sample", ("glb",))

    assert written == [tmp_path / "sample.glb"]
    assert captured["binary"] is True
    assert captured["linear_deflection"] == common.GLB_LINEAR_DEFLECTION_MM
    assert captured["angular_deflection"] == common.GLB_ANGULAR_DEFLECTION_RAD


def test_export_model_preserves_child_material_colors_in_glb(tmp_path: Path) -> None:
    first = Box(1, 2, 3)
    first.label = "red child"
    first.color = Color("#ff0000")
    second = Location((4, 0, 0)) * Box(1, 2, 3)
    second.label = "green child"
    second.color = Color("#00ff00")

    common.export_model(
        Compound(children=[first, second], label="colored assembly"),
        tmp_path / "colored-assembly",
        ("glb",),
    )

    assert glb_material_colors(tmp_path / "colored-assembly.glb") >= {
        (1.0, 0.0, 0.0, 1.0),
        (0.0, 1.0, 0.0, 1.0),
    }


def test_external_part_load_reuses_imported_step_and_returns_fresh_wrappers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    calls: list[Path] = []

    def fake_import_step(path: Path):
        calls.append(Path(path))
        shape = Box(1, 2, 3)
        shape.label = "imported"
        shape.color = Color("#123456")
        return shape

    monkeypatch.setattr(external_parts, "import_step", fake_import_step)
    external_parts._load_cached_step.cache_clear()

    part = ExternalPart(
        name="cached-test-part",
        step_path=tmp_path / "test.step",
        source_kind="external-step",
        notes="test fixture",
    )

    first = part.load()
    second = part.load()

    assert calls == [part.step_path.resolve()]
    assert first is not second
    assert first.wrapped is second.wrapped
    assert first.label == part.name
    assert second.label == part.name

    first.label = "changed-on-first"
    assert second.label == part.name
    assert tuple(second.color) == tuple(Color("#123456"))
