from __future__ import annotations

from synthcad.external_parts import ExternalPart
from synthcad.paths import project_real_parts_dir


REAL_PARTS_DIR = project_real_parts_dir("flat-disk-robot")

REPEAT_COMPACT_1806 = ExternalPart(
    name="repeat-compact-1806-gearmotor",
    step_path=REAL_PARTS_DIR
    / "repeat-drive-compact-1.snapshot.11"
    / "Repeat Compact 1806.STEP",
    source_kind="external-step",
    notes="Repeat Robotics Compact 1806 gearmotor reference STEP.",
    project="flat-disk-robot",
)

AS5600_ENCODER = ExternalPart(
    name="as5600-magnetic-encoder-module",
    step_path=REAL_PARTS_DIR
    / "as5600-magnetic-encoder-module-1.snapshot.5"
    / "AS5600_magnetic_encoder.step",
    source_kind="external-step",
    notes="AS5600 magnetic encoder module reference STEP.",
    project="flat-disk-robot",
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
    project="flat-disk-robot",
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

EXTERNAL_PARTS = {
    part.name: part
    for part in [
        REPEAT_COMPACT_1806,
        AS5600_ENCODER,
        XIAO_ESP32S3_SENSE,
        OV2640_21MM_160_CAMERA,
    ]
}
