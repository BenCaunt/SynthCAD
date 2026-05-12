from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

from synthcad.cad.common import export_model, export_model_with_timings
from synthcad.paths import GENERATED_DIR, project_generated_dir
from synthcad.registry import (
    BUILD_TARGETS,
    BuildTarget,
    IntentionalInterference,
    ValidationPlan,
    filter_targets,
    project_names,
    target_lookup,
    targets_for_project,
)
from synthcad.review_assets import build_display_snapshot


def _snapshot_path_for_target(target: BuildTarget, output_path: Path) -> Path:
    return target.output_prefix(output_path).with_suffix(".snapshot.json")


def _write_display_snapshot(target: BuildTarget, model, output_path: Path) -> Path:
    snapshot_path = _snapshot_path_for_target(target, output_path)
    snapshot = build_display_snapshot(target, model)
    snapshot_path.write_text(json.dumps(snapshot, indent=2) + "\n")
    return snapshot_path


def _manifest_entry(
    target: BuildTarget,
    written: list[Path],
    *,
    display_snapshot: Path | None = None,
) -> dict:
    data = asdict(target)
    data.pop("factory")
    data.pop("inspection_factory")
    data["outputs"] = [str(path) for path in written]
    data["display_snapshot"] = str(display_snapshot) if display_snapshot is not None else None
    return data


def export_targets(
    targets: list[BuildTarget] | tuple[BuildTarget, ...],
    output_dir: str | Path = GENERATED_DIR,
    *,
    profile: bool = False,
) -> list[Path]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    manifest = []
    total_build_seconds = 0.0
    total_export_seconds = 0.0
    for target in targets:
        build_start = perf_counter()
        model = target.factory()
        build_seconds = perf_counter() - build_start
        total_build_seconds += build_seconds

        if profile:
            target_paths, export_timings = export_model_with_timings(
                model,
                target.output_prefix(output_path),
                target.formats,
            )
            export_seconds = sum(export_timings.values())
            total_export_seconds += export_seconds
            timing_parts = [f"build={build_seconds:.3f}s"]
            timing_parts.extend(
                f"{fmt}={export_timings[fmt]:.3f}s"
                for fmt in target.formats
                if fmt in export_timings
            )
            timing_parts.append(f"total={build_seconds + export_seconds:.3f}s")
            print(f"{target.name}: profile " + " ".join(timing_parts))
        else:
            target_paths = export_model(model, target.output_prefix(output_path), target.formats)

        snapshot_path = _write_display_snapshot(target, model, output_path)
        written.extend([*target_paths, snapshot_path])
        manifest.append(_manifest_entry(target, target_paths, display_snapshot=snapshot_path))

    manifest_path = output_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    written.append(manifest_path)

    if profile:
        total_seconds = total_build_seconds + total_export_seconds
        print(
            "build-export totals: "
            f"build={total_build_seconds:.3f}s "
            f"export={total_export_seconds:.3f}s "
            f"total={total_seconds:.3f}s"
        )

    return written


def export_all(
    output_dir: str | Path = GENERATED_DIR,
    *,
    profile: bool = False,
) -> list[Path]:
    return export_targets(BUILD_TARGETS, output_dir=output_dir, profile=profile)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export synthcad build targets to STEP, STL, and GLB artifacts."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to export. Defaults to all targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to export. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Project slug to export. May be repeated.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to each selected project's generated directory.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List projects and build targets, then exit.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Print per-target build and export timings.",
    )
    return parser.parse_args()


def _print_inventory() -> None:
    print("Projects:")
    for project in project_names():
        print(f"  {project}")
    print("\nBuild targets:")
    for target in BUILD_TARGETS:
        printable = "printable" if target.printable else "reference"
        print(f"  {target.name} ({target.kind}, {printable}, project: {target.project})")


def main() -> None:
    args = _parse_args()
    if args.list:
        _print_inventory()
        return

    requested_names = [*args.target_options, *args.targets]
    try:
        targets = filter_targets(
            names=requested_names,
            projects=args.project,
            default_all=not requested_names and not args.project,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if args.output_dir is not None:
        written = export_targets(targets, output_dir=args.output_dir, profile=args.profile)
    else:
        written = []
        for project in sorted({target.project for target in targets}):
            project_targets = [target for target in targets if target.project == project]
            written.extend(
                export_targets(
                    project_targets,
                    output_dir=project_generated_dir(project),
                    profile=args.profile,
                )
            )

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
