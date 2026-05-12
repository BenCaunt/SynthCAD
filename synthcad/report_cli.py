from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from typing import Any

from synthcad.build import (
    BUILD_TARGETS,
    BuildTarget,
    filter_targets as registry_filter_targets,
    project_names as registry_project_names,
    target_lookup as registry_target_lookup,
)
from synthcad.paths import project_generated_dir


def _manifest_path(project: str) -> Path:
    return project_generated_dir(project) / "manifest.json"


def _inspection_report_path(project: str) -> Path:
    return project_generated_dir(project) / "inspection" / "inspection-report.json"


def _interference_report_path(project: str) -> Path:
    return project_generated_dir(project) / "inspection" / "interference" / "show-interference-report.json"


def _normalize_label(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _normalize_labels(values: Sequence[str] | None) -> tuple[str, ...]:
    if not values:
        return ()
    labels: list[str] = []
    for value in values:
        label = _normalize_label(value)
        if label and label not in labels:
            labels.append(label)
    return tuple(labels)


def target_project_labels(target: BuildTarget) -> tuple[str, ...]:
    return (_normalize_label(target.project),)


def describe_target_projects(target: BuildTarget) -> str:
    hints = target_project_labels(target)
    if not hints:
        return "unassigned"
    return ", ".join(hints)


def filter_targets_by_project(
    targets: Sequence[BuildTarget],
    project_filters: Sequence[str] | None,
) -> list[BuildTarget]:
    filters = _normalize_labels(project_filters)
    if not filters:
        return list(targets)
    available_projects = set(registry_project_names())
    unknown = [project for project in filters if project not in available_projects]
    if unknown:
        available = ", ".join(sorted(available_projects))
        raise ValueError(
            f"Unknown project filter(s): {', '.join(unknown)}. Available projects: {available}"
        )
    matches = registry_filter_targets(projects=list(filters))
    match_names = {target.name for target in matches}
    return [target for target in targets if target.name in match_names]


def _read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _load_manifest_index(path: Path) -> dict[str, dict[str, Any]]:
    manifest = _read_json(path)
    if not isinstance(manifest, list):
        return {}
    return {
        entry["name"]: entry
        for entry in manifest
        if isinstance(entry, dict) and "name" in entry
    }


def _load_inspection_subjects(path: Path) -> dict[str, dict[str, Any]]:
    report = _read_json(path)
    if not isinstance(report, dict):
        return {}
    subjects = report.get("subjects", [])
    if not isinstance(subjects, list):
        return {}
    return {
        subject["name"]: subject
        for subject in subjects
        if isinstance(subject, dict) and "name" in subject
    }


def _load_interference_subjects(path: Path) -> dict[str, dict[str, Any]]:
    report = _read_json(path)
    if not isinstance(report, dict):
        return {}
    subjects = report.get("subjects", [])
    if not isinstance(subjects, list):
        return {}
    return {
        subject["name"]: subject
        for subject in subjects
        if isinstance(subject, dict) and "name" in subject
    }


def build_report_bundle(
    *,
    selected_targets: Sequence[BuildTarget],
    selected_projects: Sequence[str] | None = None,
    all_targets: Sequence[BuildTarget] | None = None,
) -> dict[str, Any]:
    del all_targets
    selected_project_names = tuple(sorted({target.project for target in selected_targets}))
    manifest_indexes = {
        project: _load_manifest_index(_manifest_path(project))
        for project in selected_project_names
    }
    inspection_subject_indexes = {
        project: _load_inspection_subjects(_inspection_report_path(project))
        for project in selected_project_names
    }
    interference_subject_indexes = {
        project: _load_interference_subjects(_interference_report_path(project))
        for project in selected_project_names
    }

    selected_target_records: list[dict[str, Any]] = []
    for target in selected_targets:
        manifest_entry = manifest_indexes.get(target.project, {}).get(target.name)
        target_record = asdict(target)
        target_record.pop("factory", None)
        target_record["output_prefix"] = str(target.output_prefix())
        target_record["project_labels"] = list(target_project_labels(target))
        target_record["manifest_entry"] = manifest_entry
        target_record["inspection_subject"] = inspection_subject_indexes.get(target.project, {}).get(target.name)
        target_record["interference_subject"] = interference_subject_indexes.get(target.project, {}).get(target.name)
        selected_target_records.append(
            target_record
        )

    selected_names = {target.name for target in selected_targets}
    scoped_inspection_subjects = [
        subject
        for subjects in inspection_subject_indexes.values()
        for name, subject in subjects.items()
        if name in selected_names
    ]
    scoped_interference_subjects = [
        subject
        for subjects in interference_subject_indexes.values()
        for name, subject in subjects.items()
        if name in selected_names
    ]
    manifest_entries = [
        entry
        for indexes in manifest_indexes.values()
        for entry in indexes.values()
    ]

    return {
        "filters": {
            "targets": [target.name for target in selected_targets],
            "projects": list(selected_projects or ()),
        },
        "targets": selected_target_records,
        "artifacts": {
            "manifest": {
                "path": ", ".join(str(_manifest_path(project)) for project in selected_project_names),
                "paths": {
                    project: str(_manifest_path(project))
                    for project in selected_project_names
                },
                "exists": any(_manifest_path(project).exists() for project in selected_project_names),
                "targets": manifest_entries,
            },
            "inspection": {
                "path": ", ".join(str(_inspection_report_path(project)) for project in selected_project_names),
                "paths": {
                    project: str(_inspection_report_path(project))
                    for project in selected_project_names
                },
                "exists": any(_inspection_report_path(project).exists() for project in selected_project_names),
                "subjects": scoped_inspection_subjects,
            },
            "interference": {
                "path": ", ".join(str(_interference_report_path(project)) for project in selected_project_names),
                "paths": {
                    project: str(_interference_report_path(project))
                    for project in selected_project_names
                },
                "exists": any(_interference_report_path(project).exists() for project in selected_project_names),
                "subjects": scoped_interference_subjects,
            },
        },
    }


def _target_summary_line(target: dict[str, Any]) -> str:
    project_text = target.get("project") or ", ".join(target.get("project_labels", [])) or "unassigned"
    return (
        f"- `{target['name']}` ({target['kind']}, project: {project_text}, "
        f"printable: {'yes' if target['printable'] else 'no'})"
    )


def render_markdown_report(bundle: dict[str, Any]) -> str:
    lines: list[str] = ["# synthcad validation report", ""]

    filters = bundle.get("filters", {})
    selected_targets = filters.get("targets", [])
    selected_projects = filters.get("projects", [])
    if selected_targets or selected_projects:
        lines.append("## Scope")
        if selected_targets:
            lines.append(f"- targets: {', '.join(f'`{name}`' for name in selected_targets)}")
        if selected_projects:
            lines.append(f"- projects: {', '.join(f'`{name}`' for name in selected_projects)}")
        lines.append("")

    lines.append("## Build Targets")
    targets = bundle.get("targets", [])
    if not targets:
        lines.append("No targets matched the current filter.")
        lines.append("")
    else:
        for target in targets:
            lines.append(_target_summary_line(target))
            if target.get("status"):
                lines.append(f"  - status: {target['status']}")
            source_refs = target.get("source_refs", [])
            if source_refs:
                lines.append(
                    "  - source refs: "
                    + ", ".join(f"`{source_ref}`" for source_ref in source_refs)
                )
            docs = target.get("docs", [])
            if docs:
                lines.append("  - docs: " + ", ".join(f"`{doc}`" for doc in docs))
            validation = target.get("validation", {})
            if isinstance(validation, dict):
                inspect_enabled = validation.get("inspect")
                interference_targets = validation.get("interference_targets", [])
                notes: list[str] = []
                if inspect_enabled is False:
                    notes.append("inspection disabled")
                if interference_targets:
                    notes.append(f"{len(interference_targets)} interference target(s)")
                if notes:
                    lines.append("  - validation: " + ", ".join(notes))
            intentional_interferences = target.get("intentional_interferences", [])
            if intentional_interferences:
                lines.append(
                    "  - intentional interferences: "
                    f"{len(intentional_interferences)} documented case(s)"
                )
            manifest_entry = target.get("manifest_entry")
            if manifest_entry:
                outputs = manifest_entry.get("outputs", [])
                lines.append(f"  - build outputs: {len(outputs)} files")
            inspection_subject = target.get("inspection_subject")
            if inspection_subject:
                projection_outputs = inspection_subject.get("projection_outputs", [])
                interference_check = inspection_subject.get("interference_check", {})
                lines.append(
                    "  - inspection: "
                    f"{len(projection_outputs)} projection(s), "
                    f"{len(interference_check.get('interferences', []))} interference(s)"
                )
            lines.append("")

    artifacts = bundle.get("artifacts", {})

    inspection = artifacts.get("inspection", {})
    lines.append("## Inspection")
    lines.append(
        f"- report: `{inspection.get('path', '')}` "
        f"({'present' if inspection.get('exists') else 'missing'})"
    )
    subjects = inspection.get("subjects", [])
    if subjects:
        for subject in subjects:
            projection_outputs = subject.get("projection_outputs", [])
            lines.append(
                f"  - `{subject.get('name', 'unknown')}`: "
                f"{len(projection_outputs)} projection(s)"
            )
    elif inspection.get("exists"):
        lines.append("  - no selected target subjects found in the latest inspection report")
    lines.append("")

    interference = artifacts.get("interference", {})
    lines.append("## Interference")
    lines.append(
        f"- report: `{interference.get('path', '')}` "
        f"({'present' if interference.get('exists') else 'missing'})"
    )
    interference_subject_list = interference.get("subjects", [])
    if interference_subject_list:
        for subject in interference_subject_list:
            interferences = subject.get("interference_check", {}).get("interferences", [])
            lines.append(
                f"  - `{subject.get('name', 'unknown')}`: {len(interferences)} interference(s)"
            )
    elif interference.get("exists"):
        lines.append("  - no selected target subjects found in the latest interference report")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize synthcad build targets and generated validation artifacts "
            "as Markdown or JSON."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to include. Defaults to all targets.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to include. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help=(
            "Project metadata name or source-module hint to include. "
            "May be repeated."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of Markdown.",
    )
    return parser.parse_args()


def _resolve_targets(args: argparse.Namespace) -> list[BuildTarget]:
    lookup = {target.name: target for target in BUILD_TARGETS}
    requested_names = [*args.target_options, *args.targets]

    if requested_names:
        unknown = [name for name in requested_names if name not in lookup]
        if unknown:
            available = ", ".join(sorted(lookup))
            raise SystemExit(
                f"Unknown build target(s): {', '.join(unknown)}. "
                f"Available targets: {available}"
            )
        targets = [lookup[name] for name in requested_names]
    else:
        targets = list(BUILD_TARGETS)

    project_filters = _normalize_labels(args.project)
    if project_filters:
        try:
            targets = filter_targets_by_project(targets, project_filters)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc

    if not targets:
        raise SystemExit("No build targets matched the selected filters.")
    return targets


def main() -> int:
    args = _parse_args()
    targets = _resolve_targets(args)
    normalized_projects = _normalize_labels(args.project)
    bundle = build_report_bundle(
        selected_targets=targets,
        selected_projects=normalized_projects,
    )
    bundle["filters"] = {
        "targets": [*args.target_options, *args.targets],
        "projects": list(normalized_projects),
    }

    if args.json:
        print(json.dumps(bundle, indent=2))
    else:
        print(render_markdown_report(bundle), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
