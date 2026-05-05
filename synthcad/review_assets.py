from __future__ import annotations

import argparse
import importlib
import json
import math
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

from build123d import export_gltf


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPLAY_EXPORT_ENV_VAR = "LLM_CAD_DISPLAY_EXPORT_JOBS"
DEFAULT_DISPLAY_EXPORT_JOBS = max(1, min(2, os.cpu_count() or 1))

# Viewer-focused PR display meshes: exact assembly geometry with a moderately
# coarse tessellation so holes/fillets still read correctly without exploding
# CI runtime or GitHub Pages payload size.
PR_DISPLAY_GLB_LINEAR_DEFLECTION_MM = 0.5
PR_DISPLAY_GLB_ANGULAR_DEFLECTION_RAD = 0.5


@dataclass(frozen=True)
class DisplayExportRequest:
    target_name: str
    asset_output_dir: Path


@dataclass(frozen=True)
class DisplayExportResult:
    target_name: str
    asset_output_dir: Path
    duration_seconds: float
    snapshot: dict[str, Any] | None = None
    error: str | None = None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _vector_tuple(vector: Any, precision: int = 4) -> tuple[float, float, float]:
    return tuple(round(float(component), precision) for component in vector)


def _bbox_record_from_bounds(
    min_point: tuple[float, float, float],
    max_point: tuple[float, float, float],
) -> dict[str, Any]:
    size = tuple(round(maximum - minimum, 4) for minimum, maximum in zip(min_point, max_point, strict=True))
    center = tuple(round((minimum + maximum) / 2, 4) for minimum, maximum in zip(min_point, max_point, strict=True))
    diagonal = round(math.sqrt(sum(component**2 for component in size)), 4)
    return {
        "min": min_point,
        "max": max_point,
        "center": center,
        "size": size,
        "diagonal": diagonal,
    }


def _bounding_box_summary(shape: Any) -> dict[str, Any]:
    bbox = shape.bounding_box()
    return {
        "min": _vector_tuple(bbox.min),
        "max": _vector_tuple(bbox.max),
        "center": _vector_tuple(bbox.center()),
        "size": _vector_tuple(bbox.size),
        "diagonal": round(float(bbox.diagonal), 4),
    }


def _shape_label(shape: Any, index: int) -> str:
    label = getattr(shape, "label", "")
    return label or f"child-{index:03d}"


def _shape_color_record(shape: Any) -> dict[str, Any] | None:
    color = getattr(shape, "color", None)
    if color is None:
        return None

    try:
        components = tuple(float(component) for component in color)
    except TypeError:
        return None

    if len(components) < 3:
        return None

    rgba = tuple(
        round(max(0.0, min(component, 1.0)), 6)
        for component in (*components[:3], components[3] if len(components) > 3 else 1.0)
    )
    hex_color = "#" + "".join(f"{round(component * 255):02x}" for component in rgba[:3])
    return {
        "hex": hex_color,
        "rgba": rgba,
    }


def _instance_key(label: str, center: tuple[float, float, float]) -> str:
    x, y, z = (round(float(component), 2) for component in center)
    return f"{label} @ ({x:.2f}, {y:.2f}, {z:.2f})"


def _serializable_target_record(target: Any) -> dict[str, Any]:
    if is_dataclass(target):
        record = asdict(target)
        record.pop("factory", None)
        record.pop("inspection_factory", None)
        return record
    return {
        key: value
        for key, value in vars(target).items()
        if key not in {"factory", "inspection_factory"}
    }


def _snapshot_child_record(shape: Any, index: int, seen_keys: dict[str, int]) -> dict[str, Any]:
    label = _shape_label(shape, index)
    bbox = _bounding_box_summary(shape)
    center = tuple(bbox["center"])
    base_key = _instance_key(label, center)
    occurrence = seen_keys.get(base_key, 0) + 1
    seen_keys[base_key] = occurrence
    instance_key = base_key if occurrence == 1 else f"{base_key} [{occurrence}]"
    return {
        "index": index - 1,
        "label": label,
        "instance_key": instance_key,
        "bbox_mm": bbox,
        "color": _shape_color_record(shape),
        # The PR diff viewer only needs labels/bounds/order. Keep snapshot
        # generation cheap by avoiding expensive exact .solids()/.volume()
        # queries on large imported vendor parts.
        "solid_count": 1,
        "volume_mm3": 0.0,
    }


def build_display_snapshot(target: Any, model: Any) -> dict[str, Any]:
    children = tuple(getattr(model, "children", ()) or ())
    seen_keys: dict[str, int] = {}
    child_records = [
        _snapshot_child_record(child, index, seen_keys)
        for index, child in enumerate(children, start=1)
    ]

    if child_records:
        min_point = tuple(
            round(min(child["bbox_mm"]["min"][axis] for child in child_records), 4)
            for axis in range(3)
        )
        max_point = tuple(
            round(max(child["bbox_mm"]["max"][axis] for child in child_records), 4)
            for axis in range(3)
        )
        bbox_mm = _bbox_record_from_bounds(min_point, max_point)
    else:
        bbox_mm = _bounding_box_summary(model)

    return {
        "target": _serializable_target_record(target),
        "model_summary": {
            "name": target.name,
            "kind": target.kind,
            "label": getattr(model, "label", "") or target.name,
            "bbox_mm": bbox_mm,
            "child_count": len(children),
            "solid_count": len(child_records),
            "volume_mm3": 0.0,
        },
        "children": child_records,
        "inspection": {"projection_urls": [], "detail_projection_urls": []},
    }


def export_display_assets(
    target: Any,
    asset_output_dir: Path,
    *,
    glb_url: str | None = None,
) -> dict[str, Any]:
    model = target.factory()
    asset_output_dir.mkdir(parents=True, exist_ok=True)
    export_gltf(
        model,
        str(asset_output_dir / f"{target.name}.glb"),
        binary=True,
        linear_deflection=PR_DISPLAY_GLB_LINEAR_DEFLECTION_MM,
        angular_deflection=PR_DISPLAY_GLB_ANGULAR_DEFLECTION_RAD,
    )
    snapshot = build_display_snapshot(target, model)
    snapshot_path = asset_output_dir / "snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    if glb_url:
        return {
            **snapshot,
            "glb_url": glb_url,
            "artifact_urls": {"glb": glb_url},
        }
    return snapshot


def configured_display_export_jobs() -> int:
    raw = os.getenv(DISPLAY_EXPORT_ENV_VAR, "").strip()
    if not raw:
        return DEFAULT_DISPLAY_EXPORT_JOBS
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_DISPLAY_EXPORT_JOBS


def _export_display_assets_from_repo(
    repo_root: Path,
    target_name: str,
    asset_output_dir: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)

    build_module = importlib.import_module("synthcad.build")
    lookup = {target.name: target for target in build_module.BUILD_TARGETS}
    if target_name not in lookup:
        available = ", ".join(sorted(lookup))
        raise SystemExit(f"Unknown build target {target_name!r}. Available targets: {available}")
    return export_display_assets(lookup[target_name], asset_output_dir)


def _run_export_display_assets_subprocess(
    repo_root: Path,
    target_name: str,
    asset_output_dir: Path,
) -> DisplayExportResult:
    asset_output_dir.mkdir(parents=True, exist_ok=True)
    start = perf_counter()
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "_export-display-assets",
            "--repo-root",
            str(repo_root),
            "--target",
            target_name,
            "--asset-output-dir",
            str(asset_output_dir),
        ],
        capture_output=True,
        text=True,
    )
    duration = perf_counter() - start
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "subprocess failed"
        return DisplayExportResult(
            target_name=target_name,
            asset_output_dir=asset_output_dir,
            duration_seconds=duration,
            error=message,
        )

    snapshot_path = asset_output_dir / "snapshot.json"
    if not snapshot_path.exists():
        return DisplayExportResult(
            target_name=target_name,
            asset_output_dir=asset_output_dir,
            duration_seconds=duration,
            error=f"Display export for {target_name!r} did not write {snapshot_path}",
        )

    return DisplayExportResult(
        target_name=target_name,
        asset_output_dir=asset_output_dir,
        duration_seconds=duration,
        snapshot=_read_json(snapshot_path),
    )


def export_display_assets_batch(
    repo_root: Path,
    requests: Sequence[DisplayExportRequest],
    *,
    jobs: int | None = None,
) -> list[DisplayExportResult]:
    ordered_requests = list(requests)
    if not ordered_requests:
        return []

    worker_count = max(1, jobs or configured_display_export_jobs())
    worker_count = min(worker_count, len(ordered_requests))

    if worker_count == 1:
        return [
            _run_export_display_assets_subprocess(repo_root, request.target_name, request.asset_output_dir)
            for request in ordered_requests
        ]

    ordered_results: list[DisplayExportResult | None] = [None] * len(ordered_requests)
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(
                _run_export_display_assets_subprocess,
                repo_root,
                request.target_name,
                request.asset_output_dir,
            ): index
            for index, request in enumerate(ordered_requests)
        }
        for future in as_completed(future_map):
            ordered_results[future_map[future]] = future.result()

    return [result for result in ordered_results if result is not None]


def _parse_export_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export synthcad display assets for one target.")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--target", required=True)
    parser.add_argument("--asset-output-dir", type=Path, required=True)
    return parser.parse_args(argv)


def _export_assets_main(argv: Sequence[str]) -> int:
    args = _parse_export_args(argv)
    _export_display_assets_from_repo(args.repo_root, args.target, args.asset_output_dir)
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "_export-display-assets":
        return _export_assets_main(sys.argv[2:])
    raise SystemExit("review_assets.py only supports the internal _export-display-assets command")


if __name__ == "__main__":
    raise SystemExit(main())
