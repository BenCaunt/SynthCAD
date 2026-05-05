import json
from pathlib import Path

from build123d import Box, Compound, Location

import synthcad.viewer_cli as viewer_module
from synthcad.build import BuildTarget
from synthcad.viewer_cli import ViewerData


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def _make_target(name: str, factory) -> BuildTarget:
    return BuildTarget(
        name=name,
        factory=factory,
        kind="reference-assembly",
        source_module="tests.test_viewer_cli",
        printable=False,
        project="viewer-test-project",
        status="sandbox",
        formats=("glb",),
    )


def _seed_viewer_artifacts(tmp_path, monkeypatch, target, *, snapshot_payload=None):
    generated_dir = tmp_path / "generated"
    inspection_dir = generated_dir / "inspection"
    interference_dir = inspection_dir / "interference"
    glb_path = generated_dir / target.project / f"{target.name}.glb"
    glb_path.parent.mkdir(parents=True, exist_ok=True)
    glb_path.write_bytes(b"glb")

    projection_path = inspection_dir / f"{target.name}-isometric.svg"
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_text("<svg></svg>\n", encoding="utf-8")
    detail_projection_path = inspection_dir / f"{target.name}-isometric-detail.svg"
    detail_projection_path.write_text("<svg></svg>\n", encoding="utf-8")

    snapshot_path = generated_dir / target.project / f"{target.name}.snapshot.json"
    if snapshot_payload is not None:
        _write_json(snapshot_path, snapshot_payload)

    _write_json(
        generated_dir / "manifest.json",
        [
            {
                "name": target.name,
                "outputs": [str(glb_path)],
                "display_snapshot": str(snapshot_path) if snapshot_payload is not None else None,
            }
        ],
    )
    _write_json(
        inspection_dir / "inspection-report.json",
        {
            "subjects": [
                {
                    "name": target.name,
                    "projection_outputs": [str(projection_path)],
                    "detail_projection_outputs": [str(detail_projection_path)],
                    "interference_check": {"interferences": []},
                }
            ]
        },
    )
    _write_json(
        interference_dir / "show-interference-report.json",
        {
            "subjects": [
                {
                    "name": target.name,
                    "red_overlay_outputs": [],
                    "interference_check": {"interferences": []},
                }
            ]
        },
    )

    monkeypatch.setattr(viewer_module, "GENERATED_DIR", generated_dir)
    monkeypatch.setattr(viewer_module, "DEFAULT_MANIFEST_PATH", generated_dir / "manifest.json")
    monkeypatch.setattr(
        viewer_module,
        "DEFAULT_INSPECTION_REPORT_PATH",
        inspection_dir / "inspection-report.json",
    )
    monkeypatch.setattr(
        viewer_module,
        "DEFAULT_INTERFERENCE_REPORT_PATH",
        interference_dir / "show-interference-report.json",
    )
    return glb_path


def test_viewer_data_index_reports_selected_target(tmp_path, monkeypatch) -> None:
    target = _make_target("viewer-index-target", lambda: Compound(children=[Box(1, 1, 1)]))
    glb_path = _seed_viewer_artifacts(tmp_path, monkeypatch, target)
    viewer = ViewerData([target], initial_target=target.name)
    viewer._glb_path = lambda _target: glb_path

    payload = viewer.index_payload()

    assert payload["default_target"] == target.name
    assert [entry["name"] for entry in payload["targets"]] == [target.name]
    assert payload["targets"][0]["has_glb"] is True


def test_viewer_data_maps_project_generated_artifacts_to_project_route() -> None:
    target = _make_target("viewer-project-generated-target", lambda: Compound(children=[Box(1, 1, 1)]))
    viewer = ViewerData([target], initial_target=target.name)
    artifact_path = viewer.generated_roots[target.project] / f"{target.name}.glb"

    assert (
        viewer._generated_url(artifact_path)
        == f"/project-generated/{target.project}/{target.name}.glb"
    )


def test_viewer_data_detail_prefers_prebuilt_snapshot_without_calling_factory(
    tmp_path,
    monkeypatch,
) -> None:
    target = _make_target(
        "viewer-snapshot-target",
        lambda: (_ for _ in ()).throw(AssertionError("factory should not be called")),
    )
    snapshot_payload = {
        "target": {"name": target.name},
        "model_summary": {
            "name": target.name,
            "kind": target.kind,
            "label": "snapshot target",
            "bbox_mm": {
                "min": [0.0, 0.0, 0.0],
                "max": [10.0, 20.0, 30.0],
                "center": [5.0, 10.0, 15.0],
                "size": [10.0, 20.0, 30.0],
                "diagonal": 37.4166,
            },
            "child_count": 2,
            "solid_count": 2,
            "volume_mm3": 0.0,
        },
        "children": [
            {
                "index": 0,
                "label": "first child",
                "bbox_mm": {
                    "min": [0.0, 0.0, 0.0],
                    "max": [2.0, 2.0, 2.0],
                    "center": [1.0, 1.0, 1.0],
                    "size": [2.0, 2.0, 2.0],
                    "diagonal": 3.4641,
                },
                "solid_count": 1,
                "volume_mm3": 0.0,
            },
            {
                "index": 1,
                "label": "second child",
                "bbox_mm": {
                    "min": [4.0, 0.0, 0.0],
                    "max": [6.0, 2.0, 2.0],
                    "center": [5.0, 1.0, 1.0],
                    "size": [2.0, 2.0, 2.0],
                    "diagonal": 3.4641,
                },
                "solid_count": 1,
                "volume_mm3": 0.0,
            },
        ],
    }
    glb_path = _seed_viewer_artifacts(
        tmp_path,
        monkeypatch,
        target,
        snapshot_payload=snapshot_payload,
    )
    viewer = ViewerData([target], initial_target=target.name)
    viewer._glb_path = lambda _target: glb_path

    payload = viewer.detail_payload(target.name)

    assert payload["detail_source"] == "prebuilt-snapshot"
    assert payload["target"]["name"] == target.name
    assert payload["glb_url"].endswith(f"/{target.name}.glb")
    assert [child["label"] for child in payload["children"]] == [
        "first child",
        "second child",
    ]
    assert payload["inspection"]["projection_urls"]
    assert payload["inspection"]["detail_projection_urls"]


def test_viewer_data_detail_falls_back_to_live_snapshot_when_prebuilt_missing(
    tmp_path,
    monkeypatch,
) -> None:
    def factory():
        first = Box(2, 2, 2)
        first.label = "first child"
        second = Location((5, 0, 0)) * Box(2, 2, 2)
        second.label = "second child"
        return Compound(children=[first, second], label="live target")

    target = _make_target("viewer-live-target", factory)
    glb_path = _seed_viewer_artifacts(tmp_path, monkeypatch, target)
    viewer = ViewerData([target], initial_target=target.name)
    viewer._glb_path = lambda _target: glb_path

    payload = viewer.detail_payload(target.name)

    assert payload["detail_source"] == "live-snapshot"
    assert payload["model_summary"]["label"] == "live target"
    assert [child["label"] for child in payload["children"]] == [
        "first child",
        "second child",
    ]
