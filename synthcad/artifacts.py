from __future__ import annotations

from synthcad.cad.common import load_cad
from synthcad.paths import GENERATED_DIR, project_generated_dir


def generated_artifact_path(name: str, suffix: str = "step", project: str | None = None):
    relative = f"{name}.{suffix.lstrip('.')}"
    if project:
        return project_generated_dir(project) / relative
    return GENERATED_DIR / relative


def load_generated_artifact(name: str, suffix: str = "step", project: str | None = None):
    return load_cad(generated_artifact_path(name, suffix, project))
