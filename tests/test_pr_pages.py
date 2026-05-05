import json
from pathlib import Path

import synthcad.pr_pages as pr_pages
from synthcad.review_assets import DisplayExportResult


def _child(label: str, *, size: list[float], center: list[float] | None = None) -> dict:
    center = center or [0.0, 0.0, 0.0]
    return {
        "index": 0,
        "label": label,
        "instance_key": f"{label} @ ({center[0]:.2f}, {center[1]:.2f}, {center[2]:.2f})",
        "bbox_mm": {
            "min": [center[0] - size[0] / 2, center[1] - size[1] / 2, center[2] - size[2] / 2],
            "max": [center[0] + size[0] / 2, center[1] + size[1] / 2, center[2] + size[2] / 2],
            "center": center,
            "size": size,
            "diagonal": sum(component**2 for component in size) ** 0.5,
        },
        "solid_count": 1,
        "volume_mm3": 0.0,
    }


def _snapshot(name: str, *, children: list[dict]) -> dict:
    return {
        "target": {
            "name": name,
            "project": "flat-disk-robot",
            "kind": "robot-reference-assembly",
        },
        "model_summary": {
            "name": name,
            "kind": "robot-reference-assembly",
            "label": name,
            "bbox_mm": {
                "min": [-5.0, -5.0, -5.0],
                "max": [5.0, 5.0, 5.0],
                "center": [0.0, 0.0, 0.0],
                "size": [10.0, 10.0, 10.0],
                "diagonal": 17.3205,
            },
            "child_count": len(children),
            "solid_count": len(children),
            "volume_mm3": 0.0,
        },
        "children": children,
        "inspection": {"projection_urls": [], "detail_projection_urls": []},
    }


def test_compare_snapshots_records_modified_added_and_removed_children() -> None:
    base = _snapshot(
        "flat-disk-robot",
        children=[
            _child("stable chassis", size=[10.0, 10.0, 2.0]),
            _child("TPU press-fit D-bore wheel", size=[20.0, 51.0, 51.0], center=[1.0, 0.0, 0.0]),
            _child("removed sensor", size=[4.0, 4.0, 2.0], center=[2.0, 0.0, 0.0]),
        ],
    )
    head = _snapshot(
        "flat-disk-robot",
        children=[
            _child("stable chassis", size=[10.0, 10.0, 2.0]),
            _child("TPU press-fit D-bore wheel", size=[20.0, 53.0, 53.0], center=[1.0, 0.0, 0.0]),
            _child("added bracket", size=[3.0, 4.0, 5.0], center=[3.0, 0.0, 0.0]),
        ],
    )

    comparison = pr_pages.compare_snapshots(base, head)

    assert comparison["unchanged_count"] == 1
    assert [item["label"] for item in comparison["modified"]] == ["TPU press-fit D-bore wheel"]
    assert [item["label"] for item in comparison["added"]] == ["added bracket"]
    assert [item["label"] for item in comparison["removed"]] == ["removed sensor"]


def test_export_pr_diff_site_writes_viewer_index_and_assets(tmp_path: Path, monkeypatch) -> None:
    def fake_export_batch(repo_root, requests, jobs=None):
        side = "head" if Path(repo_root).name == "head" else "base"
        results = []
        for request in requests:
            request.asset_output_dir.mkdir(parents=True, exist_ok=True)
            (request.asset_output_dir / f"{request.target_name}.glb").write_bytes(b"glb")
            wheel_size = [20.0, 53.0, 53.0] if side == "head" else [20.0, 51.0, 51.0]
            results.append(
                DisplayExportResult(
                    target_name=request.target_name,
                    asset_output_dir=request.asset_output_dir,
                    duration_seconds=0.01,
                    snapshot=_snapshot(
                        request.target_name,
                        children=[
                            _child("stable chassis", size=[10.0, 10.0, 2.0]),
                            _child(
                                "TPU press-fit D-bore wheel",
                                size=wheel_size,
                                center=[1.0, 0.0, 0.0],
                            ),
                        ],
                    ),
                )
            )
        return results

    monkeypatch.setattr(pr_pages, "export_display_assets_batch", fake_export_batch)

    output_dir = tmp_path / "site"
    diff_index = pr_pages.export_pr_diff_site(
        repo_root=tmp_path / "head",
        base_root=tmp_path / "base",
        target_names=["flat-disk-robot"],
        output_dir=output_dir,
        base_ref="base-sha",
        head_ref="head-sha",
    )

    assert diff_index["default_assembly"] == "flat-disk-robot"
    assert (output_dir / "index.html").exists()
    assert (output_dir / "pr-diff.js").exists()
    assert (output_dir / "pr-diff.css").exists()
    assert (output_dir / "assets" / "head" / "flat-disk-robot" / "flat-disk-robot.glb").exists()

    written_index = json.loads((output_dir / "data" / "diff-index.json").read_text())
    assembly = written_index["assemblies"][0]
    assert assembly["base"]["glb_url"] == "assets/base/flat-disk-robot/flat-disk-robot.glb"
    assert assembly["head"]["glb_url"] == "assets/head/flat-disk-robot/flat-disk-robot.glb"
    assert [item["label"] for item in assembly["comparison"]["modified"]] == [
        "TPU press-fit D-bore wheel"
    ]
    assert assembly["base"]["changed_instance_keys"]
    assert assembly["head"]["changed_instance_keys"]


def test_export_pr_diff_site_handles_target_missing_from_base_revision(
    tmp_path: Path,
    monkeypatch,
) -> None:
    def fake_export_batch(repo_root, requests, jobs=None):
        results = []
        for request in requests:
            if Path(repo_root).name == "base":
                results.append(
                    DisplayExportResult(
                        target_name=request.target_name,
                        asset_output_dir=request.asset_output_dir,
                        duration_seconds=0.01,
                        error=f"Unknown build target {request.target_name!r}.",
                    )
                )
            else:
                request.asset_output_dir.mkdir(parents=True, exist_ok=True)
                (request.asset_output_dir / f"{request.target_name}.glb").write_bytes(b"glb")
                results.append(
                    DisplayExportResult(
                        target_name=request.target_name,
                        asset_output_dir=request.asset_output_dir,
                        duration_seconds=0.01,
                        snapshot=_snapshot(
                            request.target_name,
                            children=[_child("new part", size=[1.0, 2.0, 3.0])],
                        ),
                    )
                )
        return results

    monkeypatch.setattr(pr_pages, "export_display_assets_batch", fake_export_batch)

    diff_index = pr_pages.export_pr_diff_site(
        repo_root=tmp_path / "head",
        base_root=tmp_path / "base",
        target_names=["new-assembly"],
        output_dir=tmp_path / "site",
    )

    assembly = diff_index["assemblies"][0]
    assert assembly["base"]["unavailable"] is True
    assert assembly["base"]["glb_url"] is None
    assert [item["label"] for item in assembly["comparison"]["added"]] == ["new part"]
