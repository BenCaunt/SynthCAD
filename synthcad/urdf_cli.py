from __future__ import annotations

import argparse
from pathlib import Path

from synthcad.paths import project_generated_dir
from synthcad.registry import (
    URDF_TARGETS,
    UrdfTarget,
    filter_urdf_targets,
    urdf_project_names,
)
from synthcad.urdf import export_urdf_package


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
        default=None,
        help="Output directory. Defaults to each selected project's generated directory.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List URDF-capable projects and targets, then exit.",
    )
    return parser.parse_args()


def _print_inventory() -> None:
    print("Projects:")
    for project in urdf_project_names():
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
        targets = filter_urdf_targets(
            names=requested_names,
            projects=args.project,
            default_all=not requested_names and not args.project,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    written: list[Path] = []
    for target in targets:
        output_dir = args.output_dir or project_generated_dir(target.project)
        written.extend(export_urdf_package(target.factory(), output_dir=output_dir))

    for path in written:
        print(path)


if __name__ == "__main__":
    main()
