from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from time import perf_counter
from typing import Sequence

from synthcad.build import BUILD_TARGETS, BuildTarget
from synthcad.report_cli import filter_targets_by_project
from synthcad.review_assets import build_display_snapshot


DEFAULT_CHILD_LIMIT = 25


def _serializable_target_record(target: BuildTarget) -> dict[str, object]:
    record = asdict(target)
    record.pop("factory", None)
    record.pop("inspection_factory", None)
    return record


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe synthcad build targets and print lightweight geometry metadata, "
            "including target bounds and direct child labels/bounding boxes."
        )
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Build target names to probe. Defaults to all targets or the selected project.",
    )
    parser.add_argument(
        "--target",
        dest="target_options",
        action="append",
        default=[],
        help="Build target name to probe. May be repeated.",
    )
    parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Project metadata name to include. May be repeated.",
    )
    parser.add_argument(
        "--inspection-model",
        action="store_true",
        help="Use inspection_factory when available instead of the full factory.",
    )
    parser.add_argument(
        "--children",
        action="store_true",
        help="Print direct child records after the target summary.",
    )
    parser.add_argument(
        "--child-limit",
        type=int,
        default=DEFAULT_CHILD_LIMIT,
        help=(
            "Maximum number of child records to print in text mode. "
            f"Defaults to {DEFAULT_CHILD_LIMIT}. Use 0 for no limit."
        ),
    )
    parser.add_argument(
        "--label-contains",
        action="append",
        default=[],
        help="Restrict child output to labels containing this substring. May be repeated.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    return parser.parse_args(argv)


def _resolve_targets(args: argparse.Namespace) -> list[BuildTarget]:
    requested_names = [*args.target_options, *args.targets]
    lookup = {target.name: target for target in BUILD_TARGETS}

    if requested_names:
        unknown = [name for name in requested_names if name not in lookup]
        if unknown:
            available = ", ".join(sorted(lookup))
            raise SystemExit(
                f"Unknown build target(s): {', '.join(unknown)}. Available targets: {available}"
            )
        targets = [lookup[name] for name in requested_names]
    else:
        targets = list(BUILD_TARGETS)

    try:
        targets = filter_targets_by_project(targets, args.project)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    if not targets:
        raise SystemExit("No build targets matched the selected filters.")

    return targets


def _filtered_children(snapshot: dict[str, object], filters: list[str]) -> list[dict[str, object]]:
    children = list(snapshot.get("children", []) or [])
    if not filters:
        return children

    lowered = [token.lower() for token in filters if token]
    filtered = []
    for child in children:
        label = str(child.get("label", "")).lower()
        if all(token in label for token in lowered):
            filtered.append(child)
    return filtered


def _probe_target(
    target: BuildTarget,
    *,
    inspection_model: bool,
    label_filters: list[str],
) -> dict[str, object]:
    build_start = perf_counter()
    if inspection_model:
        model = target.make_inspection_model()
        model_source = "inspection-factory" if target.inspection_factory is not None else "factory"
    else:
        model = target.factory()
        model_source = "factory"
    build_seconds = perf_counter() - build_start

    snapshot = build_display_snapshot(target, model)
    children = _filtered_children(snapshot, label_filters)

    return {
        "target": _serializable_target_record(target),
        "model_source": model_source,
        "build_seconds": round(build_seconds, 4),
        "model_summary": snapshot.get("model_summary", {}),
        "children": children,
        "filtered_child_count": len(children),
    }


def _print_text_probe(payload: dict[str, object], *, children: bool, child_limit: int) -> None:
    target = payload["target"]
    summary = payload["model_summary"]
    child_records = list(payload.get("children", []) or [])
    bbox = summary.get("bbox_mm", {})
    size = bbox.get("size", [0.0, 0.0, 0.0])

    print(
        f"{target['name']} [{target['kind']}] "
        f"project={target['project']} status={target['status']}"
    )
    print(
        f"  source={payload['model_source']} build={payload['build_seconds']:.4f}s "
        f"children={summary.get('child_count', 0)} filtered={payload.get('filtered_child_count', 0)}"
    )
    print(
        "  bbox="
        f"{size[0]:.2f} × {size[1]:.2f} × {size[2]:.2f} mm "
        f"center={', '.join(f'{value:.2f}' for value in bbox.get('center', [0.0, 0.0, 0.0]))}"
    )

    if not children:
        return

    visible_children = child_records if child_limit == 0 else child_records[:child_limit]
    for child in visible_children:
        child_bbox = child.get("bbox_mm", {})
        child_size = child_bbox.get("size", [0.0, 0.0, 0.0])
        child_center = child_bbox.get("center", [0.0, 0.0, 0.0])
        print(
            f"  - #{child.get('index', 0) + 1:03d} {child.get('label', '-')}: "
            f"size={child_size[0]:.2f} × {child_size[1]:.2f} × {child_size[2]:.2f} mm "
            f"center={', '.join(f'{value:.2f}' for value in child_center)}"
        )

    hidden = len(child_records) - len(visible_children)
    if hidden > 0:
        print(f"  … {hidden} more child record(s) omitted; raise --child-limit or use --json")


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    targets = _resolve_targets(args)
    payloads = [
        _probe_target(
            target,
            inspection_model=args.inspection_model,
            label_filters=args.label_contains,
        )
        for target in targets
    ]

    if args.json:
        print(json.dumps(payloads, indent=2))
        return 0

    for index, payload in enumerate(payloads):
        if index:
            print()
        _print_text_probe(payload, children=args.children, child_limit=args.child_limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
