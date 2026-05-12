from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Sequence

from synthcad.project_selection import select_projects_for_paths


def _git_changed_paths(base_ref: str, head_ref: str) -> list[str]:
    if set(base_ref) == {"0"}:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, head_ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _write_github_env(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select SynthCAD projects and targets affected by changed paths."
    )
    parser.add_argument(
        "--base-ref",
        help="Base git ref for change detection. Requires --head-ref.",
    )
    parser.add_argument(
        "--head-ref",
        help="Head git ref for change detection. Requires --base-ref.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Changed path to include directly. May be repeated.",
    )
    parser.add_argument(
        "--github-env",
        type=Path,
        help="Append selected scope values to this GitHub Actions env file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the selected scope as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    paths = list(args.path)
    if args.base_ref or args.head_ref:
        if not args.base_ref or not args.head_ref:
            raise SystemExit("Use both --base-ref and --head-ref, or neither.")
        paths.extend(_git_changed_paths(args.base_ref, args.head_ref))

    selection = select_projects_for_paths(paths)
    if args.github_env:
        _write_github_env(args.github_env, selection.github_env())

    if args.json or not args.github_env:
        print(json.dumps(selection.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
