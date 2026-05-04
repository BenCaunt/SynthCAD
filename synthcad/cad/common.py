from __future__ import annotations

from math import atan2, cos, degrees, hypot, radians, sin
from pathlib import Path
from time import perf_counter

from build123d import (
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Circle,
    Color,
    Compound,
    Cylinder,
    Line,
    Location,
    Locations,
    Mode,
    Plane,
    Rectangle,
    RectangleRounded,
    Text,
    add,
    export_gltf,
    export_step,
    export_stl,
    extrude,
    import_step,
    import_stl,
    make_face,
)


PCB_THICKNESS = 1.6
COPPER_THICKNESS = 0.08
SILK_THICKNESS = 0.035

PCB_GREEN = "#0a6b3d"
COPPER_GOLD = "#c89f2d"
SOLDER_MASK = "#093b24"
SILK_WHITE = "#f4f0df"
BLACK = "#111111"
SILVER = "#b9b9b9"
OFF_WHITE = "#e7dfc8"
BLUE = "#1d5f99"
PRINTED_FRAME = "#6d7378"
TPU_BLACK = "#181818"
BATTERY_BLACK = "#18191c"
BATTERY_LABEL = "#d9d2bd"
RADAR_PURPLE = "#51408f"

# GLB is a review artifact for the web viewer and PR pages, not the exact CAD
# interchange format. A slightly coarser tessellation keeps large reference
# assemblies practical to export while retaining viewer fidelity.
GLB_LINEAR_DEFLECTION_MM = 0.05
GLB_ANGULAR_DEFLECTION_RAD = 0.2


def tag(shape, label: str, color: str):
    shape.label = label
    shape.color = Color(color)
    return shape


def box(
    label: str,
    x: float,
    y: float,
    z: float,
    length: float,
    width: float,
    height: float,
    color: str,
    rotation: float = 0,
):
    return tag(
        Location((x, y, z)) * Box(length, width, height, rotation=(0, 0, rotation)),
        label,
        color,
    )


def trace_between(
    label: str,
    start: tuple[float, float],
    end: tuple[float, float],
    width: float = 0.18,
    height: float = COPPER_THICKNESS,
    color: str = COPPER_GOLD,
):
    sx, sy = start
    ex, ey = end
    length = hypot(ex - sx, ey - sy)
    angle = degrees(atan2(ey - sy, ex - sx))
    return box(
        label,
        (sx + ex) / 2,
        (sy + ey) / 2,
        PCB_THICKNESS + height / 2,
        length,
        width,
        height,
        color,
        angle,
    )


def annulus(label: str, x: float, y: float, inner_radius: float, outer_radius: float):
    with BuildPart() as ring:
        with BuildSketch(Plane.XY):
            Circle(outer_radius)
            Circle(inner_radius, mode=Mode.SUBTRACT)
        extrude(amount=COPPER_THICKNESS)
    return tag(
        Location((x, y, PCB_THICKNESS + 0.01)) * ring.part,
        label,
        COPPER_GOLD,
    )


def text_label(
    label: str,
    text: str,
    x: float,
    y: float,
    size: float,
    color: str = SILK_WHITE,
    rotation: float = 0,
):
    with BuildPart() as lettering:
        with BuildSketch(Plane.XY):
            Text(text, size, rotation=rotation)
        extrude(amount=SILK_THICKNESS)
    return tag(
        Location((x, y, PCB_THICKNESS + COPPER_THICKNESS + 0.02)) * lettering.part,
        label,
        color,
    )


def rotate_xy(x: float, y: float, angle_degrees: float) -> tuple[float, float]:
    angle = radians(angle_degrees)
    return (x * cos(angle) - y * sin(angle), x * sin(angle) + y * cos(angle))


def circle_point(
    center: tuple[float, float],
    radius: float,
    angle_degrees: float,
) -> tuple[float, float]:
    angle = radians(angle_degrees)
    return (center[0] + radius * cos(angle), center[1] + radius * sin(angle))


def qfn_package(
    label: str,
    x: float,
    y: float,
    body_size: float,
    rotation: float,
    pins_per_side: int = 5,
):
    children = [
        box(
            f"{label} body",
            x,
            y,
            PCB_THICKNESS + 0.36,
            body_size,
            body_size,
            0.72,
            BLACK,
            rotation,
        )
    ]
    pitch = body_size / (pins_per_side + 1)
    pin_length = 0.78
    pin_width = 0.18
    z = PCB_THICKNESS + COPPER_THICKNESS + 0.04

    for index in range(pins_per_side):
        offset = -body_size / 2 + pitch * (index + 1)
        pin_specs = [
            (offset, body_size / 2 + pin_length / 2, pin_width, pin_length),
            (offset, -body_size / 2 - pin_length / 2, pin_width, pin_length),
            (body_size / 2 + pin_length / 2, offset, pin_length, pin_width),
            (-body_size / 2 - pin_length / 2, offset, pin_length, pin_width),
        ]
        for pin_number, (px, py, length, width) in enumerate(pin_specs):
            rx, ry = rotate_xy(px, py, rotation)
            children.append(
                box(
                    f"{label} pin {index + 1}-{pin_number + 1}",
                    x + rx,
                    y + ry,
                    z,
                    length,
                    width,
                    0.1,
                    SILVER,
                    rotation,
                )
            )

    return children


def rounded_board(
    label: str,
    length: float,
    width: float,
    radius: float,
    holes: list[tuple[float, float, float]] | None = None,
):
    with BuildPart() as board:
        with BuildSketch(Plane.XY):
            RectangleRounded(length, width, radius)
        extrude(amount=PCB_THICKNESS)

        for x, y, radius in holes or []:
            with Locations((x, y, PCB_THICKNESS / 2)):
                Cylinder(radius, PCB_THICKNESS * 3, mode=Mode.SUBTRACT)

    return tag(board.part, label, PCB_GREEN)


def export_model_with_timings(
    model,
    path_base: Path,
    formats: tuple[str, ...] = ("step", "stl", "glb"),
) -> tuple[list[Path], dict[str, float]]:
    written: list[Path] = []
    timings: dict[str, float] = {}
    path_base.parent.mkdir(parents=True, exist_ok=True)
    exporters = {
        "step": lambda path: export_step(model, path),
        "stl": lambda path: export_stl(model, path),
        "glb": lambda path: export_gltf(
            model,
            path,
            binary=True,
            linear_deflection=GLB_LINEAR_DEFLECTION_MM,
            angular_deflection=GLB_ANGULAR_DEFLECTION_RAD,
        ),
    }
    for suffix in formats:
        if suffix not in exporters:
            supported = ", ".join(sorted(exporters))
            raise ValueError(
                f"Unsupported export format {suffix!r}. Supported formats: {supported}"
            )
        path = path_base.with_suffix(f".{suffix}")
        start = perf_counter()
        exporters[suffix](path)
        timings[suffix] = perf_counter() - start
        written.append(path)
    return written, timings


def export_model(model, path_base: Path, formats: tuple[str, ...] = ("step", "stl", "glb")) -> list[Path]:
    written, _timings = export_model_with_timings(model, path_base, formats)
    return written


def load_cad(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".step", ".stp"}:
        return import_step(path)
    if suffix == ".stl":
        return import_stl(path)
    raise ValueError(f"Unsupported CAD import format: {path}")
