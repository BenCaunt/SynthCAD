from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from synthcad.paths import GENERATED_DIR
from synthcad.projects.flat_disk_robot.urdf import make_flat_disk_robot_urdf
from synthcad.urdf import RobotDescription, export_urdf_package


@dataclass(frozen=True)
class UrdfTarget:
    name: str
    project: str
    factory: Callable[[], RobotDescription]
    docs: tuple[str, ...] = ()


URDF_TARGETS = [
    UrdfTarget(
        name="flat-disk-robot",
        project="flat-disk-robot",
        factory=make_flat_disk_robot_urdf,
        docs=("docs/flat-disk-robot-notes.md",),
    ),
]


def target_lookup() -> dict[str, UrdfTarget]:
    return {target.name: target for target in URDF_TARGETS}


def project_names() -> tuple[str, ...]:
    return tuple(sorted({target.project for target in URDF_TARGETS}))


def filter_targets(
    *,
    names: list[str] | tuple[str, ...] = (),
    projects: list[str] | tuple[str, ...] = (),
    default_all: bool = False,
) -> list[UrdfTarget]:
    lookup = target_lookup()
    selected: list[UrdfTarget] = []

    if default_all and not names and not projects:
        selected.extend(URDF_TARGETS)

    for project in projects:
        matches = [target for target in URDF_TARGETS if target.project == project]
        if not matches:
            available = ", ".join(project_names())
            raise ValueError(f"Unknown project {project!r}. Available projects: {available}")
        selected.extend(matches)

    unknown = [name for name in names if name not in lookup]
    if unknown:
        available = ", ".join(sorted(lookup))
        raise ValueError(
            f"Unknown URDF target(s): {', '.join(unknown)}. Available targets: {available}"
        )
    selected.extend(lookup[name] for name in names)

    deduped: list[UrdfTarget] = []
    seen: set[str] = set()
    for target in selected:
        if target.name not in seen:
            deduped.append(target)
            seen.add(target.name)
    return deduped


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export URDF packages for synthcad robot targets."
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="URDF target names to export. Defaults to all URDF-capable targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="URDF target name to export. May be repeated.",
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
        default=GENERATED_DIR,
        help=f"Output directory. Defaults to {GENERATED_DIR}.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List URDF-capable projects and targets, then exit.",
    )
    return parser.parse_args()


def _print_inventory() -> None:
    print("Projects:")
    for project in project_names():
        print(f"  {project}")
    print("\nURDF targets:")
    for target in URDF_TARGETS:
        docs = f"; docs: {', '.join(target.docs)}" if target.docs else ""
        print(f"  {target.name} (project: {target.project}{docs})")


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

    written: list[Path] = []
    for target in targets:
        written.extend(export_urdf_package(target.factory(), output_dir=args.output_dir))

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
