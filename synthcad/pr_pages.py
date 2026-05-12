from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any, Sequence

from synthcad.build import filter_targets
from synthcad.paths import GENERATED_DIR
from synthcad.review_assets import DisplayExportRequest, export_display_assets_batch


REPO_ROOT = Path(__file__).resolve().parents[1]
WEBVIEWER_DIR = Path(__file__).resolve().with_name("webviewer")
DEFAULT_PR_PAGES_DIR = GENERATED_DIR / "pr-pages"


def _with_snapshot_urls(snapshot: dict[str, Any], glb_url: str) -> dict[str, Any]:
    return {
        **snapshot,
        "glb_url": glb_url,
        "artifact_urls": {"glb": glb_url},
    }


def _unavailable_snapshot(
    target_name: str,
    *,
    reason: str,
) -> dict[str, Any]:
    return {
        "target": {
            "name": target_name,
            "project": None,
            "kind": "unavailable-build-target",
        },
        "glb_url": None,
        "artifact_urls": {},
        "model_summary": {
            "name": target_name,
            "kind": "unavailable-build-target",
            "label": target_name,
            "bbox_mm": {
                "min": [0.0, 0.0, 0.0],
                "max": [0.0, 0.0, 0.0],
                "center": [0.0, 0.0, 0.0],
                "size": [0.0, 0.0, 0.0],
                "diagonal": 0.0,
            },
            "child_count": 0,
            "solid_count": 0,
            "volume_mm3": 0.0,
        },
        "children": [],
        "inspection": {"projection_urls": []},
        "unavailable": True,
        "unavailable_reason": reason,
    }


def _looks_like_missing_target(error: str, target_name: str) -> bool:
    return (
        f"Unknown build target {target_name!r}" in error
        or f"Unknown build target(s): {target_name}" in error
    )


def _export_side_snapshots(
    *,
    repo_root: Path,
    target_names: Sequence[str],
    output_dir: Path,
    side: str,
) -> dict[str, dict[str, Any]]:
    asset_root = output_dir / "assets" / side
    requests = [
        DisplayExportRequest(target_name, asset_root / target_name)
        for target_name in target_names
    ]
    results = export_display_assets_batch(repo_root, requests)
    snapshots: dict[str, dict[str, Any]] = {}

    for result in results:
        target_name = result.target_name
        glb_url = f"assets/{side}/{target_name}/{target_name}.glb"
        if result.error:
            if _looks_like_missing_target(result.error, target_name):
                snapshots[target_name] = _unavailable_snapshot(
                    target_name,
                    reason="Target is unavailable in this revision.",
                )
                continue
            raise SystemExit(result.error)
        if result.snapshot is None:
            raise SystemExit(f"Display export for {target_name!r} did not return a snapshot.")
        snapshots[target_name] = _with_snapshot_urls(result.snapshot, glb_url)

    return snapshots


def _normalized_label_tokens(label: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.sub(r"[^a-z0-9]+", " ", label.lower()).split()
        if token not in {"proxy", "reference"}
    )


def _child_signature(child: dict[str, Any]) -> tuple[Any, ...]:
    bbox = child.get("bbox_mm", {})
    return (
        tuple(_normalized_label_tokens(str(child.get("label", "")))),
        tuple(bbox.get("center", ())),
        tuple(bbox.get("size", ())),
        child.get("solid_count", 0),
        child.get("volume_mm3", 0.0),
    )


def _delta_record(
    label: str,
    *,
    base_child: dict[str, Any] | None = None,
    head_child: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "label": label,
        "base_instance_key": base_child.get("instance_key") if base_child else None,
        "head_instance_key": head_child.get("instance_key") if head_child else None,
        "base_bbox_mm": base_child.get("bbox_mm") if base_child else None,
        "head_bbox_mm": head_child.get("bbox_mm") if head_child else None,
    }


def compare_snapshots(
    base_snapshot: dict[str, Any],
    head_snapshot: dict[str, Any],
) -> dict[str, Any]:
    base_children = list(base_snapshot.get("children", []) or [])
    head_children = list(head_snapshot.get("children", []) or [])
    base_by_key = {
        child.get("instance_key"): child
        for child in base_children
        if child.get("instance_key")
    }
    head_by_key = {
        child.get("instance_key"): child
        for child in head_children
        if child.get("instance_key")
    }

    common_keys = set(base_by_key) & set(head_by_key)
    modified: list[dict[str, Any]] = []
    unchanged_count = 0
    for key in sorted(common_keys):
        base_child = base_by_key[key]
        head_child = head_by_key[key]
        if _child_signature(base_child) == _child_signature(head_child):
            unchanged_count += 1
        else:
            modified.append(
                _delta_record(
                    str(head_child.get("label") or base_child.get("label") or key),
                    base_child=base_child,
                    head_child=head_child,
                )
            )

    removed = [
        _delta_record(str(child.get("label") or child.get("instance_key")), base_child=child)
        for child in base_children
        if child.get("instance_key") not in head_by_key
    ]
    added = [
        _delta_record(str(child.get("label") or child.get("instance_key")), head_child=child)
        for child in head_children
        if child.get("instance_key") not in base_by_key
    ]

    return {
        "unchanged_count": unchanged_count,
        "added": added,
        "modified": modified,
        "removed": removed,
    }


def _changed_instance_keys(
    snapshot: dict[str, Any],
    deltas: Sequence[dict[str, Any]],
    *,
    side: str,
) -> list[str]:
    available_keys = {child.get("instance_key") for child in snapshot.get("children", []) or []}
    changed: list[str] = []
    seen: set[str] = set()
    for delta in deltas:
        key = delta.get(f"{side}_instance_key")
        if key in available_keys and key not in seen:
            changed.append(key)
            seen.add(key)
    return changed


def build_diff_index(
    *,
    base_ref: str | None,
    head_ref: str | None,
    assembly_snapshots: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    default_assembly = assembly_snapshots[0]["name"] if assembly_snapshots else None
    return {
        "base_ref": base_ref,
        "head_ref": head_ref,
        "default_assembly": default_assembly,
        "assemblies": list(assembly_snapshots),
    }


def export_pr_diff_site(
    *,
    repo_root: Path,
    base_root: Path,
    target_names: Sequence[str],
    output_dir: Path,
    base_ref: str | None = None,
    head_ref: str | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ordered_targets = list(dict.fromkeys(target_names))

    head_snapshots = _export_side_snapshots(
        repo_root=repo_root,
        target_names=ordered_targets,
        output_dir=output_dir,
        side="head",
    )
    base_snapshots = _export_side_snapshots(
        repo_root=base_root,
        target_names=ordered_targets,
        output_dir=output_dir,
        side="base",
    )

    assembly_snapshots: list[dict[str, Any]] = []
    for name in ordered_targets:
        head_snapshot = head_snapshots[name]
        base_snapshot = base_snapshots[name]
        target_record = head_snapshot.get("target", {}) or base_snapshot.get("target", {})
        comparison = compare_snapshots(base_snapshot, head_snapshot)
        base_deltas = [*comparison["modified"], *comparison["removed"]]
        head_deltas = [*comparison["modified"], *comparison["added"]]
        assembly_snapshots.append(
            {
                "name": name,
                "project": target_record.get("project"),
                "kind": target_record.get("kind"),
                "comparison": comparison,
                "base": {
                    **base_snapshot,
                    "changed_instance_keys": _changed_instance_keys(
                        base_snapshot,
                        base_deltas,
                        side="base",
                    ),
                },
                "head": {
                    **head_snapshot,
                    "changed_instance_keys": _changed_instance_keys(
                        head_snapshot,
                        head_deltas,
                        side="head",
                    ),
                },
                "review_outputs": [],
            }
        )

    diff_index = build_diff_index(
        base_ref=base_ref,
        head_ref=head_ref,
        assembly_snapshots=assembly_snapshots,
    )

    data_dir = output_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "diff-index.json").write_text(json.dumps(diff_index, indent=2) + "\n")

    shutil.copy2(WEBVIEWER_DIR / "pr-diff.js", output_dir / "pr-diff.js")
    shutil.copy2(WEBVIEWER_DIR / "pr-diff.css", output_dir / "pr-diff.css")
    shutil.copy2(WEBVIEWER_DIR / "pr-diff.html", output_dir / "index.html")
    (output_dir / ".nojekyll").write_text("")
    return diff_index


def _select_target_names(
    *,
    targets: Sequence[str],
    projects: Sequence[str],
) -> list[str]:
    selected = filter_targets(
        names=tuple(targets),
        projects=tuple(projects),
        default_all=not targets and not projects,
    )
    return [target.name for target in selected]


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export a static base/head diff viewer site for SynthCAD PR reviews."
    )
    parser.add_argument("targets", nargs="*", help="Build target names to include.")
    parser.add_argument("--target", dest="target_options", action="append", default=[])
    parser.add_argument("--project", action="append", default=[])
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--base-ref")
    parser.add_argument("--head-ref")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_PR_PAGES_DIR)
    return parser.parse_args(argv)


def _main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    target_names = _select_target_names(
        targets=[*args.target_options, *args.targets],
        projects=args.project,
    )
    export_pr_diff_site(
        repo_root=args.repo_root,
        base_root=args.base_root,
        target_names=target_names,
        output_dir=args.output_dir,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
    )
    print((args.output_dir / "index.html").resolve())
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
