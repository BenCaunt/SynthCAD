from __future__ import annotations

from flat_disk_robot.robot import (
    make_flat_disk_robot,
    make_flat_disk_robot_chassis,
    make_flat_disk_robot_lid,
)
from flat_disk_robot.urdf import make_flat_disk_robot_urdf
from synthcad.registry import (
    BuildTarget,
    IntentionalInterference,
    UrdfTarget,
    ValidationPlan,
)


FLAT_DISK_SOURCE_REFS = (
    "projects/flat-disk-robot/real-parts/repeat-drive-compact-1.snapshot.11/Repeat Compact 1806.STEP",
    "projects/flat-disk-robot/real-parts/as5600-magnetic-encoder-module-1.snapshot.5/AS5600_magnetic_encoder.step",
    "projects/flat-disk-robot/real-parts/seeed-studio-xiao-esp32s3-sense-1.snapshot.2/Seeed Studio XIAO-ESP32-S3-Sense.step",
    "projects/flat-disk-robot/real-parts/OV2640_21mm-160_camera.STEP",
    "projects/flat-disk-robot/real-parts/TOF-sensor-drawing.webp",
    "projects/flat-disk-robot/real-parts/battery.png",
)

FLAT_DISK_DOCS = ("projects/flat-disk-robot/docs/flat-disk-robot-notes.md",)


BUILD_TARGETS = (
    BuildTarget(
        "flat-disk-robot-chassis",
        make_flat_disk_robot_chassis,
        "generated-printable-part",
        "flat_disk_robot.robot",
        True,
        "flat-disk-robot",
        "printable-candidate",
        source_refs=FLAT_DISK_SOURCE_REFS,
        docs=FLAT_DISK_DOCS,
        validation=ValidationPlan(interference_targets=("flat-disk-robot",)),
    ),
    BuildTarget(
        "flat-disk-robot-lid",
        make_flat_disk_robot_lid,
        "generated-printable-part",
        "flat_disk_robot.robot",
        True,
        "flat-disk-robot",
        "printable-candidate",
        docs=FLAT_DISK_DOCS,
        validation=ValidationPlan(interference_targets=("flat-disk-robot",)),
    ),
    BuildTarget(
        "flat-disk-robot",
        make_flat_disk_robot,
        "robot-reference-assembly",
        "flat_disk_robot.robot",
        False,
        "flat-disk-robot",
        "active",
        source_refs=FLAT_DISK_SOURCE_REFS,
        docs=FLAT_DISK_DOCS,
        intentional_interferences=(
            IntentionalInterference(
                "repeat-compact-1806-gearmotor",
                "TPU press-fit D-bore wheel",
                "The wheel/motor overlap is the modeled TPU press fit, not a hard interference.",
            ),
        ),
    ),
)

URDF_TARGETS = (
    UrdfTarget(
        name="flat-disk-robot",
        project="flat-disk-robot",
        factory=make_flat_disk_robot_urdf,
        docs=FLAT_DISK_DOCS,
    ),
)
