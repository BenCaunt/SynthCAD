from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from build123d import Color, export_brep, import_brep, import_step


@lru_cache(maxsize=None)
def _load_cached_step(step_path: str) -> Any:
    return import_step(Path(step_path))


@lru_cache(maxsize=None)
def _load_cached_brep(brep_path: str) -> Any:
    return import_brep(Path(brep_path))


def _load_with_brep_cache(step_path: Path) -> Any:
    """Load geometry preferring a .brep cache file over STEP parsing.

    OCCT's native BREP format loads 25-45x faster than STEP while
    preserving full B-rep fidelity (all faces, edges, pockets, fillets).
    If a ``.brep`` sibling exists and is at least as new as the STEP
    source, it is loaded directly.  Otherwise the STEP file is parsed
    and a BREP cache is written for next time.
    """
    brep_path = step_path.with_suffix(".brep")
    resolved_step = str(step_path.resolve())
    resolved_brep = str(brep_path.resolve())

    if brep_path.exists():
        try:
            if brep_path.stat().st_mtime >= step_path.stat().st_mtime:
                return _load_cached_brep(resolved_brep)
        except Exception:
            pass

    shape = _load_cached_step(resolved_step)

    try:
        export_brep(shape, brep_path)
    except Exception:
        pass

    return shape


def _clone_cached_shape(shape: Any) -> Any:
    clone = type(shape).cast(shape.wrapped)
    shape.copy_attributes_to(clone)
    return clone


@dataclass(frozen=True)
class ExternalPart:
    name: str
    step_path: Path
    source_kind: str
    notes: str
    project: str

    def load(self):
        # Large vendor STEP imports dominate build time for some reference
        # assemblies.  Prefer a pre-generated .brep cache (25-45x faster
        # than STEP) when available; fall back to STEP and auto-generate
        # the cache for subsequent loads.
        part = _clone_cached_shape(_load_with_brep_cache(self.step_path))
        part.label = self.name
        return part


def load_external_part(part: ExternalPart, color: str | None = None):
    part = part.load()
    if color is not None:
        part.color = Color(color)
    return part
