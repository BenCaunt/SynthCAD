from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Sequence

from synthcad.build import BUILD_TARGETS, BuildTarget, filter_targets, project_names
from synthcad.paths import ROOT


@dataclass(frozen=True)
class CiPlan:
    projects: list[str]
    test_paths: list[str]
    inspect_targets: list[str]
    pr_site_targets: list[str]
    artifact_paths: list[str]

    @property
    def target_label(self) -> str:
        if self.pr_site_targets:
            return ", ".join(self.pr_site_targets)
        return ", ".join(self.projects)

    def to_dict(self) -> dict[str, object]:
        return {
            **asdict(self),
            "target_label": self.target_label,
        }

    def github_outputs(self) -> dict[str, str]:
        return {
            "projects": " ".join(self.projects),
            "test_paths": " ".join(self.test_paths),
            "inspect_targets": " ".join(self.inspect_targets),
            "pr_site_targets": " ".join(self.pr_site_targets),
            "artifact_paths": "\n".join(self.artifact_paths),
            "target_label": self.target_label,
        }


def _project_module_map() -> dict[str, str]:
    modules: dict[str, str] = {}
    for target in BUILD_TARGETS:
        parts = target.source_module.split(".")
        if len(parts) >= 3 and parts[:2] == ["synthcad", "projects"]:
            modules[parts[2]] = target.project
    return modules


def project_from_changed_path(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    known_projects = set(project_names())
    if len(parts) >= 2 and parts[0] == "projects" and parts[1] in known_projects:
        return parts[1]

    module_map = _project_module_map()
    if len(parts) >= 3 and parts[:2] == ("synthcad", "projects"):
        return module_map.get(parts[2])

    return None


def _ordered_projects(projects: set[str]) -> list[str]:
    return [project for project in project_names() if project in projects]


def detect_projects(changed_paths: Sequence[str]) -> list[str]:
    explicit_projects = {
        project
        for path in changed_paths
        if (project := project_from_changed_path(path)) is not None
    }
    if explicit_projects:
        return _ordered_projects(explicit_projects)
    return list(project_names())


def _assembly_targets(projects: Sequence[str]) -> list[BuildTarget]:
    targets = filter_targets(projects=tuple(projects))
    return [
        target
        for target in targets
        if target.is_assembly and target.validation.inspect
    ]


def _project_test_paths(projects: Sequence[str], repo_root: Path) -> list[str]:
    paths = ["tests"]
    for project in projects:
        test_path = Path("projects") / project / "tests"
        if (repo_root / test_path).is_dir():
            paths.append(test_path.as_posix())
    return paths


def plan_for_changed_paths(
    changed_paths: Sequence[str],
    *,
    repo_root: Path = ROOT,
) -> CiPlan:
    projects = detect_projects(changed_paths)
    assembly_targets = _assembly_targets(projects)
    inspect_targets = [target.name for target in assembly_targets]
    pr_site_targets = inspect_targets or [
        target.name for target in filter_targets(projects=tuple(projects))
    ]
    return CiPlan(
        projects=projects,
        test_paths=_project_test_paths(projects, repo_root),
        inspect_targets=inspect_targets,
        pr_site_targets=pr_site_targets,
        artifact_paths=[
            (Path("projects") / project / "generated").as_posix()
            for project in projects
        ],
    )


def changed_paths_from_git(
    *,
    base_ref: str,
    head_ref: str,
    repo_root: Path = ROOT,
) -> list[str]:
    commands = [
        ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
        ["git", "diff", "--name-only", base_ref, head_ref],
    ]
    last_error: subprocess.CalledProcessError | None = None
    for command in commands:
        try:
            result = subprocess.run(
                command,
                cwd=repo_root,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except subprocess.CalledProcessError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return []


def _write_github_output(path: Path, outputs: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as output:
        for key, value in outputs.items():
            if "\n" in value:
                delimiter = f"EOF_{key}"
                output.write(f"{key}<<{delimiter}\n{value}\n{delimiter}\n")
            else:
                output.write(f"{key}={value}\n")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan SynthCAD CI scope from changed files.")
    parser.add_argument("--base-ref", help="Base git ref for diff detection.")
    parser.add_argument("--head-ref", default="HEAD", help="Head git ref for diff detection.")
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="Changed file path. May be repeated; bypasses git diff when provided.",
    )
    parser.add_argument("--github-output", type=Path, help="Append GitHub Actions outputs here.")
    parser.add_argument("--json", action="store_true", help="Print the plan as JSON.")
    return parser.parse_args(argv)


def _main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.changed_file:
        changed_paths = args.changed_file
    elif args.base_ref:
        changed_paths = changed_paths_from_git(
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            repo_root=ROOT,
        )
    else:
        changed_paths = []

    plan = plan_for_changed_paths(changed_paths, repo_root=ROOT)
    if args.github_output:
        _write_github_output(args.github_output, plan.github_outputs())
    if args.json or not args.github_output:
        print(json.dumps(plan.to_dict(), indent=2))
    return 0


def main() -> int:
    return _main()


if __name__ == "__main__":
    raise SystemExit(main())
