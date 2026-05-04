from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from build123d import Compound

from synthcad.build import BUILD_TARGETS, BuildTarget
from synthcad.inspection import (
    DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
    PROJECTION_VIEWS,
    collect_interference_solids,
    model_summary,
    render_interference_projection_svg,
)
from synthcad.paths import GENERATED_DIR
from synthcad.report_cli import describe_target_projects, filter_targets_by_project


DEFAULT_SHOW_INTERFERENCE_DIR = GENERATED_DIR / "inspection" / "interference"
DEFAULT_SHOW_INTERFERENCE_VIEWS = tuple(PROJECTION_VIEWS)


@dataclass(frozen=True)
class InterferenceSubject:
    name: str
    kind: str
    model: Any
    source_targets: tuple[str, ...]


def _target_lookup() -> dict[str, BuildTarget]:
    return {target.name: target for target in BUILD_TARGETS}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Show direct-child CAD interferences by projecting overlap volumes "
            "as red overlays from multiple isometric angles."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to check. Defaults to assembly targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to check. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help=(
            "Project metadata name or source-module hint to check. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check all build targets instead of only assembly targets.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List build targets and projection views, then exit.",
    )
    parser.add_argument(
        "--combine-as",
        metavar="NAME",
        help=(
            "Treat selected targets as direct children of one synthetic assembly. "
            "Use only when the selected targets share a meaningful coordinate frame."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_SHOW_INTERFERENCE_DIR,
        help=(
            "Directory for red-overlay SVGs and show-interference-report.json. "
            f"Defaults to {DEFAULT_SHOW_INTERFERENCE_DIR}."
        ),
    )
    parser.add_argument(
        "--view",
        action="append",
        choices=sorted(PROJECTION_VIEWS),
        help=(
            "Projection view to render. May be repeated. Defaults to all "
            "isometric views."
        ),
    )
    parser.add_argument(
        "--min-volume-mm3",
        type=float,
        default=DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
        help=(
            "Minimum volumetric overlap highlighted as interference. "
            f"Defaults to {DEFAULT_MIN_INTERFERENCE_VOLUME_MM3} mm^3."
        ),
    )
    parser.add_argument(
        "--fail-on-interference",
        action="store_true",
        help="Exit with status 1 when any checked target has reported interferences.",
    )
    return parser.parse_args()


def _print_inventory() -> None:
    print("Build targets:")
    for target in BUILD_TARGETS:
        print(f"  {target.name} ({target.kind}) [{describe_target_projects(target)}]")
    print("\nProjection views:")
    for view_name in sorted(PROJECTION_VIEWS):
        print(f"  {view_name}")


def _resolve_targets(args: argparse.Namespace) -> list[BuildTarget]:
    lookup = _target_lookup()
    requested_names = [*args.target_options, *args.targets]

    if args.all and requested_names:
        raise SystemExit("Use either --all or explicit target names, not both.")

    if args.all:
        targets = list(BUILD_TARGETS)

    elif not requested_names:
        targets = [target for target in BUILD_TARGETS if "assembly" in target.kind]
    else:
        unknown = [name for name in requested_names if name not in lookup]
        if unknown:
            available = ", ".join(sorted(lookup))
            raise SystemExit(
                f"Unknown build target(s): {', '.join(unknown)}. Available targets: {available}"
            )
        targets = [lookup[name] for name in requested_names]

    try:
        targets = filter_targets_by_project(targets, args.project)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not targets:
        raise SystemExit("No build targets matched the selected filters.")

    return targets


def _build_subjects(
    targets: list[BuildTarget],
    *,
    combine_as: str | None,
) -> list[InterferenceSubject]:
    if combine_as:
        children = [target.make_inspection_model() for target in targets]
        combined = Compound(children=children, label=combine_as)
        return [
            InterferenceSubject(
                name=combine_as,
                kind="synthetic-assembly",
                model=combined,
                source_targets=tuple(target.name for target in targets),
            )
        ]

    return [
        InterferenceSubject(
            name=target.name,
            kind=target.kind,
            model=target.make_inspection_model(),
            source_targets=(target.name,),
        )
        for target in targets
    ]


def _show_subject_interference(
    subject: InterferenceSubject,
    *,
    output_dir: Path,
    views: tuple[str, ...] | list[str],
    min_volume_mm3: float,
) -> tuple[dict[str, Any], bool]:
    report, interference_solids = collect_interference_solids(
        subject.model,
        min_volume_mm3=min_volume_mm3,
    )
    subject_report = model_summary(subject.name, subject.kind, subject.model)
    subject_report["source_targets"] = list(subject.source_targets)
    subject_report["interference_check"] = report.to_dict()
    subject_report["red_overlay_outputs"] = []

    print(
        f"{subject.name}: {len(report.interferences)} interferences "
        f">= {min_volume_mm3:g} mm^3 "
        f"({report.tested_pair_count}/{report.candidate_pair_count} candidate pairs tested)"
    )
    for interference in report.interferences:
        print(
            "  "
            f"{interference.first} <-> {interference.second}: "
            f"{interference.volume_mm3:g} mm^3"
        )
    for error in report.errors:
        print(
            "  "
            f"boolean check failed: {error.first} <-> {error.second}: {error.error}"
        )

    if not interference_solids:
        return subject_report, False

    for view_name in views:
        output_path = output_dir / f"{subject.name}-{view_name}-interference.svg"
        render_interference_projection_svg(
            subject.model,
            interference_solids,
            output_path,
            view_name,
        )
        subject_report["red_overlay_outputs"].append(str(output_path))
        print(f"{subject.name}: wrote {output_path}")

    return subject_report, True


def main() -> int:
    args = _parse_args()
    if args.list:
        _print_inventory()
        return 0

    targets = _resolve_targets(args)
    subjects = _build_subjects(targets, combine_as=args.combine_as)
    views = tuple(args.view or DEFAULT_SHOW_INTERFERENCE_VIEWS)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "views": list(views),
        "output_dir": str(args.output_dir),
        "min_volume_mm3": args.min_volume_mm3,
        "subjects": [],
    }

    any_interference = False
    for subject in subjects:
        subject_report, subject_has_interference = _show_subject_interference(
            subject,
            output_dir=args.output_dir,
            views=views,
            min_volume_mm3=args.min_volume_mm3,
        )
        report["subjects"].append(subject_report)
        any_interference = any_interference or subject_has_interference

    report_path = args.output_dir / "show-interference-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {report_path}")

    if args.fail_on_interference and any_interference:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
