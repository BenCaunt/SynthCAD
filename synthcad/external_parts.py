from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from build123d import Color, export_brep, import_brep, import_step

from synthcad.paths import REAL_PARTS_DIR, project_real_parts_dir


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
    project: str = "library"

    def load(self):
        # Large vendor STEP imports dominate build time for some reference
        # assemblies.  Prefer a pre-generated .brep cache (25-45x faster
        # than STEP) when available; fall back to STEP and auto-generate
        # the cache for subsequent loads.
        part = _clone_cached_shape(_load_with_brep_cache(self.step_path))
        part.label = self.name
        return part


REPEAT_COMPACT_1806 = ExternalPart(
    name="repeat-compact-1806-gearmotor",
    step_path=REAL_PARTS_DIR
    / "repeat-drive-compact-1.snapshot.11"
    / "Repeat Compact 1806.STEP",
    source_kind="external-step",
    notes="Repeat Robotics Compact 1806 gearmotor reference STEP.",
    project="library",
)

AS5600_ENCODER = ExternalPart(
    name="as5600-magnetic-encoder-module",
    step_path=REAL_PARTS_DIR
    / "as5600-magnetic-encoder-module-1.snapshot.5"
    / "AS5600_magnetic_encoder.step",
    source_kind="external-step",
    notes="AS5600 magnetic encoder module reference STEP.",
    project="library",
)
AS5600_MOUNTING_HOLES = [
    (-8.0, -8.0, 1.775),
    (-8.0, 8.0, 1.775),
    (8.0, -8.0, 1.775),
    (8.0, 8.0, 1.775),
]

XIAO_ESP32S3_SENSE = ExternalPart(
    name="seeed-xiao-esp32s3-sense",
    step_path=REAL_PARTS_DIR
    / "seeed-studio-xiao-esp32s3-sense-1.snapshot.2"
    / "Seeed Studio XIAO-ESP32-S3-Sense.step",
    source_kind="external-step",
    notes=(
        "Seeed Studio XIAO ESP32-S3 Sense reference STEP. In this STEP, the "
        "camera module protrudes toward local +Y."
    ),
    project="library",
)

OV2640_21MM_160_CAMERA = ExternalPart(
    name="ov2640-21mm-160-camera",
    step_path=REAL_PARTS_DIR / "OV2640_21mm-160_camera.STEP",
    source_kind="external-step",
    notes=(
        "OV2640 160 degree camera reference STEP. The lens protrudes toward "
        "local +Y; the lens axis is centered at local X/Z zero."
    ),
    project="flat-disk-robot",
)

SO_ARM_101_ASSEMBLY = ExternalPart(
    name="so-arm-101-assembly",
    step_path=project_real_parts_dir("so101-cart")
    / "so-arm-101.snapshot"
    / "SO101_Assembly.step",
    source_kind="external-step",
    notes=(
        "TheRobotStudio SO-ARM100 SO-101 follower assembly STEP. In this STEP "
        "the base sits on Z=0, the arm columns extend toward +Z, and the "
        "rotation axis of the shoulder is parallel to local Z."
    ),
    project="so101-cart",
)

EXTERNAL_PARTS = {
    part.name: part
    for part in [
        REPEAT_COMPACT_1806,
        AS5600_ENCODER,
        XIAO_ESP32S3_SENSE,
        OV2640_21MM_160_CAMERA,
        SO_ARM_101_ASSEMBLY,
    ]
}


def load_external_part(name: str, color: str | None = None):
    part = EXTERNAL_PARTS[name].load()
    if color is not None:
        part.color = Color(color)
    return part
