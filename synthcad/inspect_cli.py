from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from build123d import Compound

from synthcad.build import BUILD_TARGETS, BuildTarget
from synthcad.inspection import (
    DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
    PROJECTION_VIEWS,
    find_interferences,
    model_summary,
    render_projection_svg,
)
from synthcad.paths import GENERATED_DIR
from synthcad.report_cli import describe_target_projects, filter_targets_by_project


DEFAULT_INSPECTION_DIR = GENERATED_DIR / "inspection"


@dataclass(frozen=True)
class InspectionSubject:
    name: str
    kind: str
    model: Any
    source_targets: tuple[str, ...]
    model_source: str
    build_seconds: float = 0.0


def _target_lookup() -> dict[str, BuildTarget]:
    return {target.name: target for target in BUILD_TARGETS}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate deterministic isometric SVG projections and assembly "
            "interference reports for synthcad build targets."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to inspect. Defaults to all targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to inspect. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help=(
            "Project metadata name or source-module hint to inspect. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Inspect all build targets.",
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
        default=DEFAULT_INSPECTION_DIR,
        help=(
            "Directory for SVGs and inspection-report.json. "
            f"Defaults to {DEFAULT_INSPECTION_DIR}."
        ),
    )
    parser.add_argument(
        "--view",
        action="append",
        choices=sorted(PROJECTION_VIEWS),
        help="Projection view to render. May be repeated. Defaults to isometric.",
    )
    parser.add_argument(
        "--no-render",
        action="store_true",
        help="Skip SVG projection output.",
    )
    parser.add_argument(
        "--interference",
        choices=("assemblies", "all", "off"),
        default="assemblies",
        help=(
            "Run interference checks for assembly targets, all targets, or no targets. "
            "Defaults to assemblies."
        ),
    )
    parser.add_argument(
        "--min-volume-mm3",
        type=float,
        default=DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
        help=(
            "Minimum volumetric overlap reported as interference. "
            f"Defaults to {DEFAULT_MIN_INTERFERENCE_VOLUME_MM3} mm^3."
        ),
    )
    parser.add_argument(
        "--fail-on-interference",
        action="store_true",
        help="Exit with status 1 when any checked target has reported interferences.",
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Record per-phase timings for target build, summary, render, and interference work.",
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

    if args.all or not requested_names:
        targets = list(BUILD_TARGETS)
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
) -> list[InspectionSubject]:
    if combine_as:
        start = perf_counter()
        children = [target.make_inspection_model() for target in targets]
        combined = Compound(children=children, label=combine_as)
        build_seconds = perf_counter() - start
        return [
            InspectionSubject(
                name=combine_as,
                kind="synthetic-assembly",
                model=combined,
                source_targets=tuple(target.name for target in targets),
                model_source="inspection-factory",
                build_seconds=build_seconds,
            )
        ]

    subjects: list[InspectionSubject] = []
    for target in targets:
        start = perf_counter()
        model = target.make_inspection_model()
        build_seconds = perf_counter() - start
        subjects.append(
            InspectionSubject(
                name=target.name,
                kind=target.kind,
                model=model,
                source_targets=(target.name,),
                model_source=(
                    "inspection-factory"
                    if target.inspection_factory is not None
                    else "factory"
                ),
                build_seconds=build_seconds,
            )
        )
    return subjects


def _should_check_interference(subject: InspectionSubject, mode: str) -> bool:
    if mode == "off":
        return False
    if mode == "all":
        return True
    return "assembly" in subject.kind


def _inspect_subject(
    subject: InspectionSubject,
    *,
    output_dir: Path,
    views: list[str],
    render: bool,
    interference_mode: str,
    min_volume_mm3: float,
    profile: bool,
) -> tuple[dict[str, Any], bool]:
    summary_start = perf_counter()
    summary = model_summary(subject.name, subject.kind, subject.model)
    summary_seconds = perf_counter() - summary_start
    summary["source_targets"] = list(subject.source_targets)
    summary["model_source"] = subject.model_source
    summary["projection_outputs"] = []

    render_seconds = 0.0
    if render:
        for view_name in views:
            output_path = output_dir / f"{subject.name}-{view_name}.svg"
            view_start = perf_counter()
            render_projection_svg(subject.model, output_path, view_name)
            render_seconds += perf_counter() - view_start
            summary["projection_outputs"].append(str(output_path))
            print(f"{subject.name}: wrote {output_path}")

    interference_found = False
    interference_start = perf_counter()
    if _should_check_interference(subject, interference_mode):
        report = find_interferences(subject.model, min_volume_mm3=min_volume_mm3)
        report_data = report.to_dict()
        summary["interference_check"] = report_data
        interference_found = len(report.interferences) > 0
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
    else:
        summary["interference_check"] = {
            "skipped": True,
            "reason": f"interference mode is {interference_mode!r} for kind {subject.kind!r}",
        }
    interference_seconds = perf_counter() - interference_start

    if profile:
        timings = {
            "build_seconds": round(subject.build_seconds, 6),
            "summary_seconds": round(summary_seconds, 6),
            "render_seconds": round(render_seconds, 6),
            "interference_seconds": round(interference_seconds, 6),
            "total_seconds": round(
                subject.build_seconds + summary_seconds + render_seconds + interference_seconds,
                6,
            ),
        }
        summary["timings_seconds"] = timings
        print(
            f"{subject.name}: profile build={timings['build_seconds']:.3f}s "
            f"summary={timings['summary_seconds']:.3f}s "
            f"render={timings['render_seconds']:.3f}s "
            f"interference={timings['interference_seconds']:.3f}s "
            f"total={timings['total_seconds']:.3f}s "
            f"[{subject.model_source}]"
        )

    return summary, interference_found


def main() -> int:
    args = _parse_args()
    if args.list:
        _print_inventory()
        return 0

    targets = _resolve_targets(args)
    subjects = _build_subjects(targets, combine_as=args.combine_as)
    views = args.view or ["isometric"]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "views": views,
        "output_dir": str(args.output_dir),
        "interference_mode": args.interference,
        "min_volume_mm3": args.min_volume_mm3,
        "subjects": [],
    }

    any_interference = False
    for subject in subjects:
        subject_report, subject_has_interference = _inspect_subject(
            subject,
            output_dir=args.output_dir,
            views=views,
            render=not args.no_render,
            interference_mode=args.interference,
            min_volume_mm3=args.min_volume_mm3,
            profile=args.profile,
        )
        report["subjects"].append(subject_report)
        any_interference = any_interference or subject_has_interference

    report_path = args.output_dir / "inspection-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"wrote {report_path}")

    if args.fail_on_interference and any_interference:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
