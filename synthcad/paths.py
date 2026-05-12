from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS_DIR = ROOT / "projects"
GENERATED_DIR = ROOT / "generated"


def project_dir(project: str) -> Path:
    return PROJECTS_DIR / project


def project_real_parts_dir(project: str) -> Path:
    return project_dir(project) / "real-parts"


def project_generated_dir(project: str) -> Path:
    return project_dir(project) / "generated"
