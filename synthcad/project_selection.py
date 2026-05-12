from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

from synthcad.registry import BUILD_TARGETS, URDF_TARGETS, project_slugs


CORE_PATH_PREFIXES = (
    "synthcad/",
    "tests/",
)
CORE_PATHS = {
    ".github/workflows/synthcad-ci.yml",
    ".python-version",
    "main.py",
    "pyproject.toml",
    "uv.lock",
}
ROOT_NON_SCOPING_PATHS = {
    "LICENSE",
    "README.md",
}


@dataclass(frozen=True)
class ProjectSelection:
    projects: tuple[str, ...]
    reason: str
    changed_paths: tuple[str, ...]
    test_paths: tuple[str, ...]
    build_target_args: tuple[str, ...]
    build_targets: tuple[str, ...]
    inspection_targets: tuple[str, ...]
    assembly_targets: tuple[str, ...]
    assembly_projects: tuple[str, ...]
    urdf_targets: tuple[str, ...]
    urdf_projects: tuple[str, ...]
    pr_site_targets: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)

    def github_env(self) -> dict[str, str]:
        return {
            "SYNTHCAD_PROJECTS": " ".join(self.projects),
            "SYNTHCAD_SCOPE_REASON": self.reason,
            "SYNTHCAD_TEST_PATHS": " ".join(self.test_paths),
            "SYNTHCAD_BUILD_TARGET_ARGS": " ".join(self.build_target_args),
            "SYNTHCAD_BUILD_TARGETS": " ".join(self.build_targets),
            "SYNTHCAD_INSPECTION_TARGETS": " ".join(self.inspection_targets),
            "SYNTHCAD_ASSEMBLY_TARGETS": " ".join(self.assembly_targets),
            "SYNTHCAD_ASSEMBLY_PROJECTS": " ".join(self.assembly_projects),
            "SYNTHCAD_URDF_TARGETS": " ".join(self.urdf_targets),
            "SYNTHCAD_URDF_PROJECTS": " ".join(self.urdf_projects),
            "SYNTHCAD_PR_SITE_TARGETS": " ".join(self.pr_site_targets),
        }


def _normalize_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").lstrip("./")


def _path_project(path: str, known_projects: set[str]) -> str | None:
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "projects" and parts[1] in known_projects:
        return parts[1]
    return None


def _is_core_path(path: str) -> bool:
    if path in CORE_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in CORE_PATH_PREFIXES)


def _existing_project_test_paths(projects: Sequence[str]) -> tuple[str, ...]:
    paths = ["tests"]
    for project in projects:
        project_tests = Path("projects") / project / "tests"
        if project_tests.exists():
            paths.append(str(project_tests))
    return tuple(paths)


def _target_names_for_projects(projects: Sequence[str]) -> tuple[str, ...]:
    selected = [target.name for target in BUILD_TARGETS if target.project in projects]
    return tuple(selected)


def _inspection_targets_for_projects(projects: Sequence[str]) -> tuple[str, ...]:
    selected = [
        target.name
        for target in BUILD_TARGETS
        if target.project in projects and target.validation.inspect
    ]
    return tuple(selected)


def _assembly_targets_for_projects(projects: Sequence[str]) -> tuple[str, ...]:
    selected = [
        target.name
        for target in BUILD_TARGETS
        if target.project in projects and target.is_assembly
    ]
    return tuple(selected)


def _urdf_targets_for_projects(projects: Sequence[str]) -> tuple[str, ...]:
    selected = [target.name for target in URDF_TARGETS if target.project in projects]
    return tuple(selected)


def _projects_with_assembly_targets(projects: Sequence[str]) -> tuple[str, ...]:
    selected = {
        target.project
        for target in BUILD_TARGETS
        if target.project in projects and target.is_assembly
    }
    return tuple(sorted(selected))


def _projects_with_urdf_targets(projects: Sequence[str]) -> tuple[str, ...]:
    selected = {target.project for target in URDF_TARGETS if target.project in projects}
    return tuple(sorted(selected))


def select_projects_for_paths(changed_paths: Sequence[str | Path]) -> ProjectSelection:
    paths = tuple(_normalize_path(path) for path in changed_paths if _normalize_path(path))
    known_projects = set(project_slugs())
    all_projects = tuple(sorted(known_projects))

    changed_projects: set[str] = set()
    core_changed = False
    unscoped_paths: list[str] = []
    for path in paths:
        project = _path_project(path, known_projects)
        if project is not None:
            changed_projects.add(project)
        elif _is_core_path(path):
            core_changed = True
        elif path not in ROOT_NON_SCOPING_PATHS:
            unscoped_paths.append(path)

    if core_changed:
        projects = all_projects
        reason = "core changes"
    elif changed_projects:
        projects = tuple(sorted(changed_projects))
        reason = "project-local changes"
    elif unscoped_paths:
        projects = all_projects
        reason = "unscoped repository changes"
    else:
        projects = all_projects
        reason = "no project-specific changes"

    build_targets = _target_names_for_projects(projects)
    assembly_targets = _assembly_targets_for_projects(projects)
    build_target_args = tuple(
        part
        for project in projects
        for part in ("--project", project)
    )

    return ProjectSelection(
        projects=projects,
        reason=reason,
        changed_paths=paths,
        test_paths=_existing_project_test_paths(projects),
        build_target_args=build_target_args,
        build_targets=build_targets,
        inspection_targets=_inspection_targets_for_projects(projects),
        assembly_targets=assembly_targets,
        assembly_projects=_projects_with_assembly_targets(projects),
        urdf_targets=_urdf_targets_for_projects(projects),
        urdf_projects=_projects_with_urdf_targets(projects),
        pr_site_targets=build_targets,
    )
