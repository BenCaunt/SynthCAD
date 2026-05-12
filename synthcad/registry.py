from __future__ import annotations

import importlib.util
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from synthcad.paths import PROJECTS_DIR, project_generated_dir
from synthcad.urdf import RobotDescription


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
        output_path = project_generated_dir(self.project) if output_dir is None else Path(output_dir)
        if output_path.resolve() == project_generated_dir(self.project).resolve():
            return output_path / self.name
        return output_path / self.project / self.name

    def make_inspection_model(self):
        factory = self.inspection_factory or self.factory
        return factory()


@dataclass(frozen=True)
class UrdfTarget:
    name: str
    project: str
    factory: Callable[[], RobotDescription]
    docs: tuple[str, ...] = ()


def project_dirs() -> tuple[Path, ...]:
    if not PROJECTS_DIR.exists():
        return ()
    return tuple(
        path
        for path in sorted(PROJECTS_DIR.iterdir())
        if path.is_dir() and (path / "project.toml").exists()
    )


def project_slugs() -> tuple[str, ...]:
    return tuple(path.name for path in project_dirs())


def _project_module_name(project_dir: Path) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", project_dir.name).strip("_")
    return f"_synthcad_project_{slug}_targets"


def _load_project_targets_module(project_dir: Path):
    targets_path = project_dir / "targets.py"
    if not targets_path.exists():
        return None

    project_path = str(project_dir.resolve())
    if project_path not in sys.path:
        sys.path.insert(0, project_path)

    module_name = _project_module_name(project_dir)
    spec = importlib.util.spec_from_file_location(module_name, targets_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load project targets from {targets_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _discover_targets() -> tuple[tuple[BuildTarget, ...], tuple[UrdfTarget, ...]]:
    build_targets: list[BuildTarget] = []
    urdf_targets: list[UrdfTarget] = []
    for project_dir in project_dirs():
        module = _load_project_targets_module(project_dir)
        if module is None:
            continue
        build_targets.extend(getattr(module, "BUILD_TARGETS", ()) or ())
        urdf_targets.extend(getattr(module, "URDF_TARGETS", ()) or ())
    return tuple(build_targets), tuple(urdf_targets)


BUILD_TARGETS, URDF_TARGETS = _discover_targets()


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


def urdf_target_lookup() -> dict[str, UrdfTarget]:
    return {target.name: target for target in URDF_TARGETS}


def urdf_project_names() -> tuple[str, ...]:
    return tuple(sorted({target.project for target in URDF_TARGETS}))


def filter_urdf_targets(
    *,
    names: list[str] | tuple[str, ...] = (),
    projects: list[str] | tuple[str, ...] = (),
    default_all: bool = False,
) -> list[UrdfTarget]:
    lookup = urdf_target_lookup()
    selected: list[UrdfTarget] = []

    if default_all and not names and not projects:
        selected.extend(URDF_TARGETS)

    for project in projects:
        matches = [target for target in URDF_TARGETS if target.project == project]
        if not matches:
            available = ", ".join(urdf_project_names())
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
