from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
DEFAULT_PROJECT = "flat-disk-robot"


def project_dir(project: str) -> Path:
    return PROJECTS_DIR / project


def project_real_parts_dir(project: str) -> Path:
    return project_dir(project) / "real-parts"


def project_generated_dir(project: str) -> Path:
    return project_dir(project) / "generated"


REAL_PARTS_DIR = project_real_parts_dir(DEFAULT_PROJECT)
GENERATED_DIR = project_generated_dir(DEFAULT_PROJECT)
