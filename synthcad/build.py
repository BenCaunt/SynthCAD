from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Callable

from synthcad.cad.common import export_model, export_model_with_timings
from synthcad.paths import GENERATED_DIR, project_generated_dir
from synthcad.projects.demo_ftc_robot.robot import make_demo_ftc_robot
from synthcad.projects.flat_disk_robot.robot import (
    make_flat_disk_robot,
    make_flat_disk_robot_chassis,
    make_flat_disk_robot_lid,
)
from synthcad.review_assets import build_display_snapshot


@dataclass(frozen=True)
class ValidationPlan:
    inspect: bool = True
    interference_targets: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntentionalInterference:
    first: str
    second: str
    reason: str


@dataclass(frozen=True)
class BuildTarget:
    name: str
    factory: Callable
    kind: str
    source_module: str
    printable: bool
    project: str
    status: str
    source_refs: tuple[str, ...] = ()
    docs: tuple[str, ...] = ()
    validation: ValidationPlan = field(default_factory=ValidationPlan)
    intentional_interferences: tuple[IntentionalInterference, ...] = ()
    inspection_factory: Callable | None = None
    formats: tuple[str, ...] = ("step", "stl", "glb")

    @property
    def is_assembly(self) -> bool:
        return "assembly" in self.kind

    def output_prefix(self, output_dir: str | Path | None = None) -> Path:
        output_path = Path(output_dir) if output_dir is not None else project_generated_dir(self.project)
        if output_path.resolve() == project_generated_dir(self.project).resolve():
            return output_path / self.name
        return output_path / self.project / self.name

    def make_inspection_model(self):
        factory = self.inspection_factory or self.factory
        return factory()


FLAT_DISK_SOURCE_REFS = (
    "projects/flat-disk-robot/real-parts/repeat-drive-compact-1.snapshot.11/Repeat Compact 1806.STEP",
    "projects/flat-disk-robot/real-parts/as5600-magnetic-encoder-module-1.snapshot.5/AS5600_magnetic_encoder.step",
    "projects/flat-disk-robot/real-parts/seeed-studio-xiao-esp32s3-sense-1.snapshot.2/Seeed Studio XIAO-ESP32-S3-Sense.step",
    "projects/flat-disk-robot/real-parts/OV2640_21mm-160_camera.STEP",
    "projects/flat-disk-robot/real-parts/TOF-sensor-drawing.webp",
    "projects/flat-disk-robot/real-parts/battery.png",
)

DEMO_FTC_DOCS = ("projects/demo-ftc-robot/docs/demo-ftc-robot-notes.md",)


BUILD_TARGETS = [
    BuildTarget(
        "flat-disk-robot-chassis",
        make_flat_disk_robot_chassis,
        "generated-printable-part",
        "synthcad.projects.flat_disk_robot.robot",
        True,
        "flat-disk-robot",
        "printable-candidate",
        source_refs=FLAT_DISK_SOURCE_REFS,
        docs=("projects/flat-disk-robot/docs/flat-disk-robot-notes.md",),
        validation=ValidationPlan(interference_targets=("flat-disk-robot",)),
    ),
    BuildTarget(
        "flat-disk-robot-lid",
        make_flat_disk_robot_lid,
        "generated-printable-part",
        "synthcad.projects.flat_disk_robot.robot",
        True,
        "flat-disk-robot",
        "printable-candidate",
        docs=("projects/flat-disk-robot/docs/flat-disk-robot-notes.md",),
        validation=ValidationPlan(interference_targets=("flat-disk-robot",)),
    ),
    BuildTarget(
        "flat-disk-robot",
        make_flat_disk_robot,
        "robot-reference-assembly",
        "synthcad.projects.flat_disk_robot.robot",
        False,
        "flat-disk-robot",
        "active",
        source_refs=FLAT_DISK_SOURCE_REFS,
        docs=("projects/flat-disk-robot/docs/flat-disk-robot-notes.md",),
        intentional_interferences=(
            IntentionalInterference(
                "repeat-compact-1806-gearmotor",
                "TPU press-fit D-bore wheel",
                "The wheel/motor overlap is the modeled TPU press fit, not a hard interference.",
            ),
        ),
    ),
    BuildTarget(
        "demo-ftc-robot",
        make_demo_ftc_robot,
        "robot-planning-assembly",
        "synthcad.projects.demo_ftc_robot.robot",
        False,
        "demo-ftc-robot",
        "concept",
        docs=DEMO_FTC_DOCS,
        formats=("step", "glb"),
    ),
]


def target_lookup() -> dict[str, BuildTarget]:
    return {target.name: target for target in BUILD_TARGETS}


def project_names() -> tuple[str, ...]:
    return tuple(sorted({target.project for target in BUILD_TARGETS}))


def targets_for_project(project: str) -> list[BuildTarget]:
    return [target for target in BUILD_TARGETS if target.project == project]


def filter_targets(
    *,
    names: list[str] | tuple[str, ...] = (),
    projects: list[str] | tuple[str, ...] = (),
    default_all: bool = False,
) -> list[BuildTarget]:
    lookup = target_lookup()
    selected: list[BuildTarget] = []

    if default_all and not names and not projects:
        selected.extend(BUILD_TARGETS)

    for project in projects:
        matches = targets_for_project(project)
        if not matches:
            available = ", ".join(project_names())
            raise ValueError(f"Unknown project {project!r}. Available projects: {available}")
        selected.extend(matches)

    unknown = [name for name in names if name not in lookup]
    if unknown:
        available = ", ".join(sorted(lookup))
        raise ValueError(
            f"Unknown build target(s): {', '.join(unknown)}. Available targets: {available}"
        )
    selected.extend(lookup[name] for name in names)

    deduped: list[BuildTarget] = []
    seen: set[str] = set()
    for target in selected:
        if target.name not in seen:
            deduped.append(target)
            seen.add(target.name)
    return deduped


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
        manifest.append(
            _manifest_entry(target, target_paths, display_snapshot=snapshot_path)
        )

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
        help=(
            "Output directory. Defaults to the selected project's generated/ "
            f"directory when one project is selected, otherwise {GENERATED_DIR}."
        ),
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

    output_dir = args.output_dir
    if output_dir is None:
        selected_projects = {target.project for target in targets}
        output_dir = (
            project_generated_dir(next(iter(selected_projects)))
            if len(selected_projects) == 1
            else GENERATED_DIR
        )

    for path in export_targets(targets, output_dir=output_dir, profile=args.profile):
        print(path)


if __name__ == "__main__":
    main()
