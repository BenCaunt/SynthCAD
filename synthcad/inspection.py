from __future__ import annotations

from dataclasses import asdict, dataclass
from html import escape
from itertools import combinations
from math import sqrt
from pathlib import Path
from typing import Any

from build123d import ExportSVG, LineType, Vector


DEFAULT_MIN_INTERFERENCE_VOLUME_MM3 = 0.01


@dataclass(frozen=True)
class ProjectionView:
    name: str
    direction: tuple[float, float, float]
    up: tuple[float, float, float] = (0.0, 0.0, 1.0)


PROJECTION_VIEWS = {
    "isometric": ProjectionView("isometric", (1.0, -1.0, 0.75)),
    "left-isometric": ProjectionView("left-isometric", (-1.0, -1.0, 0.75)),
    "right-isometric": ProjectionView("right-isometric", (1.0, 1.0, 0.75)),
    "rear-isometric": ProjectionView("rear-isometric", (-1.0, 1.0, 0.75)),
}


@dataclass(frozen=True)
class Interference:
    first: str
    second: str
    volume_mm3: float
    first_bbox_mm: dict[str, Any]
    second_bbox_mm: dict[str, Any]


@dataclass(frozen=True)
class InterferenceError:
    first: str
    second: str
    error: str


@dataclass(frozen=True)
class InterferenceReport:
    child_count: int
    solid_child_count: int
    candidate_pair_count: int
    tested_pair_count: int
    min_volume_mm3: float
    interferences: list[Interference]
    errors: list[InterferenceError]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InterferenceSolid:
    interference: Interference
    shape: Any


def _vector_tuple(vector: Vector, precision: int = 4) -> tuple[float, float, float]:
    return tuple(round(float(component), precision) for component in vector)


def _shape_label(shape: Any, index: int) -> str:
    label = getattr(shape, "label", "")
    return label or f"child-{index:03d}"


def _bounding_box_summary_from_bbox(bbox: Any) -> dict[str, Any]:
    return {
        "min": _vector_tuple(bbox.min),
        "max": _vector_tuple(bbox.max),
        "center": _vector_tuple(bbox.center()),
        "size": _vector_tuple(bbox.size),
        "diagonal": round(float(bbox.diagonal), 4),
    }


def bounding_box_summary(shape: Any) -> dict[str, Any]:
    return _bounding_box_summary_from_bbox(shape.bounding_box())


def _dot(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> float:
    return sum(a * b for a, b in zip(first, second, strict=True))


def _cross(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
) -> tuple[float, float, float]:
    ax, ay, az = first
    bx, by, bz = second
    return (
        ay * bz - az * by,
        az * bx - ax * bz,
        ax * by - ay * bx,
    )


def _normalized(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = sqrt(sum(component**2 for component in vector))
    if length < 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(component / length for component in vector)


def _camera_basis(view: ProjectionView) -> tuple[
    tuple[float, float, float],
    tuple[float, float, float],
    tuple[float, float, float],
]:
    direction = _normalized(view.direction)
    up_hint = _normalized(view.up)
    right = _normalized(_cross(up_hint, direction))
    screen_up = _normalized(_cross(direction, right))
    return right, screen_up, direction


def _bbox_corners(bbox: Any) -> list[tuple[float, float, float]]:
    xs = (float(bbox.min.X), float(bbox.max.X))
    ys = (float(bbox.min.Y), float(bbox.max.Y))
    zs = (float(bbox.min.Z), float(bbox.max.Z))
    return [(x, y, z) for x in xs for y in ys for z in zs]


def _project_point(
    point: tuple[float, float, float],
    right: tuple[float, float, float],
    screen_up: tuple[float, float, float],
    direction: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        _dot(point, right),
        -_dot(point, screen_up),
        _dot(point, direction),
    )


def _convex_hull(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    unique = sorted(set(points))
    if len(unique) <= 1:
        return unique

    def cross_z(origin, first, second) -> float:
        return (
            (first[0] - origin[0]) * (second[1] - origin[1])
            - (first[1] - origin[1]) * (second[0] - origin[0])
        )

    lower: list[tuple[float, float]] = []
    for point in unique:
        while len(lower) >= 2 and cross_z(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)

    upper: list[tuple[float, float]] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross_z(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)

    return lower[:-1] + upper[:-1]


def _shape_color_hex(shape: Any, fallback: str = "#94a3b8") -> str:
    color = getattr(shape, "color", None)
    if color is None:
        return fallback

    try:
        components = tuple(float(component) for component in color)
    except (TypeError, ValueError):
        return fallback

    if len(components) < 3:
        return fallback

    channels = [max(0.0, min(component, 1.0)) for component in components[:3]]
    return "#" + "".join(f"{round(component * 255):02x}" for component in channels)


def _svg_polygon_points(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.2f},{y:.2f}" for x, y in points)


def render_quick_detail_svg(
    model: Any,
    output_path: str | Path,
    view_name: str = "isometric",
    *,
    max_legend_items: int = 48,
) -> Path:
    """Write a fast colored direct-child bbox overview SVG.

    This complements exact hidden-line projections for planning assemblies. It
    favors legibility over geometric fidelity by drawing colored child bounding
    boxes, numbered markers, and a legend.
    """

    if view_name not in PROJECTION_VIEWS:
        valid = ", ".join(sorted(PROJECTION_VIEWS))
        raise ValueError(f"Unknown projection view '{view_name}'. Valid views: {valid}")

    children = tuple(getattr(model, "children", ()) or ())
    if not children:
        children = (model,)

    right, screen_up, direction = _camera_basis(PROJECTION_VIEWS[view_name])
    records: list[dict[str, Any]] = []
    all_points: list[tuple[float, float]] = []

    for index, child in enumerate(children, start=1):
        bbox = child.bounding_box()
        corners = _bbox_corners(bbox)
        projected = [
            _project_point(corner, right, screen_up, direction)
            for corner in corners
        ]
        hull = _convex_hull([(x, y) for x, y, _depth in projected])
        center = _project_point(
            _vector_tuple(bbox.center(), precision=8),
            right,
            screen_up,
            direction,
        )
        all_points.extend(hull)
        all_points.append((center[0], center[1]))
        records.append(
            {
                "index": index,
                "label": _shape_label(child, index),
                "bbox": _bounding_box_summary_from_bbox(bbox),
                "color": _shape_color_hex(child),
                "hull": hull,
                "center": center,
                "depth": sum(depth for _x, _y, depth in projected) / len(projected),
                "shape_type": type(child).__name__,
            }
        )

    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)

    plot_width = 760.0
    plot_height = 620.0
    margin = 32.0
    legend_width = 430.0
    legend_rows = min(len(records), max_legend_items)
    width = plot_width + legend_width + margin * 3
    height = max(plot_height + margin * 2, 120.0 + legend_rows * 20.0)
    scale = min((plot_width - margin * 2) / span_x, (plot_height - margin * 2) / span_y)
    offset_x = margin + (plot_width - span_x * scale) / 2
    offset_y = margin + (plot_height - span_y * scale) / 2

    def screen(point: tuple[float, float]) -> tuple[float, float]:
        return (
            offset_x + (point[0] - min_x) * scale,
            offset_y + (point[1] - min_y) * scale,
        )

    summary = bounding_box_summary(model)
    svg: list[str] = [
        "<?xml version='1.0' encoding='utf-8'?>",
        (
            f'<svg width="{width:.0f}" height="{height:.0f}" '
            f'viewBox="0 0 {width:.0f} {height:.0f}" '
            'xmlns="http://www.w3.org/2000/svg">'
        ),
        "<style>",
        "text { font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }",
        ".title { font-size: 18px; font-weight: 700; fill: #0f172a; }",
        ".meta { font-size: 12px; fill: #475569; }",
        ".legend { font-size: 11px; fill: #1f2937; }",
        ".marker { font-size: 9px; font-weight: 700; fill: #0f172a; text-anchor: middle; dominant-baseline: central; }",
        "</style>",
        '<rect x="0" y="0" width="100%" height="100%" fill="#f8fafc" />',
        (
            f'<text class="title" x="{margin:.0f}" y="26">'
            f"{escape(str(getattr(model, 'label', '') or 'model'))} detail render</text>"
        ),
        (
            f'<text class="meta" x="{margin:.0f}" y="46">'
            f"{len(records)} direct children | bbox "
            f"{summary['size'][0]:.1f} x {summary['size'][1]:.1f} x "
            f"{summary['size'][2]:.1f} mm | view {escape(view_name)}</text>"
        ),
        (
            f'<rect x="{margin:.0f}" y="64" width="{plot_width:.0f}" height="{plot_height:.0f}" '
            'rx="8" fill="#ffffff" stroke="#cbd5e1" />'
        ),
    ]

    for record in sorted(records, key=lambda item: item["depth"]):
        hull = [screen(point) for point in record["hull"]]
        if len(hull) < 3:
            continue
        if record["shape_type"] in {"Cylinder", "Sphere"}:
            xs = [point[0] for point in hull]
            ys = [point[1] for point in hull]
            cx = (min(xs) + max(xs)) / 2
            cy = (min(ys) + max(ys)) / 2
            rx = max((max(xs) - min(xs)) / 2, 3.0)
            ry = max((max(ys) - min(ys)) / 2, 3.0)
            svg.append(
                f'<ellipse cx="{cx:.2f}" cy="{cy:.2f}" rx="{rx:.2f}" ry="{ry:.2f}" '
                f'fill="{record["color"]}" fill-opacity="0.52" stroke="#0f172a" '
                'stroke-opacity="0.46" stroke-width="1" />'
            )
            continue
        svg.append(
            f'<polygon points="{_svg_polygon_points(hull)}" fill="{record["color"]}" '
            'fill-opacity="0.52" stroke="#0f172a" stroke-opacity="0.46" stroke-width="1" />'
        )

    for record in records:
        cx, cy = screen((record["center"][0], record["center"][1]))
        svg.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="8" fill="#ffffff" '
            'fill-opacity="0.88" stroke="#0f172a" stroke-opacity="0.45" />'
        )
        svg.append(
            f'<text class="marker" x="{cx:.2f}" y="{cy:.2f}">{record["index"]}</text>'
        )

    legend_x = margin * 2 + plot_width
    svg.extend(
        [
            (
                f'<rect x="{legend_x:.0f}" y="64" width="{legend_width:.0f}" '
                f'height="{height - 96:.0f}" rx="8" fill="#ffffff" stroke="#cbd5e1" />'
            ),
            f'<text class="title" x="{legend_x + 16:.0f}" y="92">Direct children</text>',
        ]
    )

    for row, record in enumerate(records[:max_legend_items]):
        y = 116 + row * 20
        size = record["bbox"]["size"]
        label = escape(record["label"])
        svg.append(
            f'<rect x="{legend_x + 16:.0f}" y="{y - 10:.0f}" width="12" height="12" '
            f'fill="{record["color"]}" stroke="#0f172a" stroke-opacity="0.35" />'
        )
        svg.append(
            f'<text class="legend" x="{legend_x + 36:.0f}" y="{y:.0f}">'
            f'{record["index"]:02d}. {label} ({size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} mm)</text>'
        )

    hidden_count = len(records) - max_legend_items
    if hidden_count > 0:
        y = 116 + max_legend_items * 20
        svg.append(
            f'<text class="meta" x="{legend_x + 16:.0f}" y="{y:.0f}">'
            f"... {hidden_count} more children omitted from legend</text>"
        )

    svg.append("</svg>")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(svg) + "\n", encoding="utf-8")
    return output


def model_summary(name: str, kind: str, model: Any) -> dict[str, Any]:
    children = tuple(getattr(model, "children", ()) or ())
    return {
        "name": name,
        "kind": kind,
        "label": getattr(model, "label", "") or name,
        "bbox_mm": bounding_box_summary(model),
        "child_count": len(children),
        "solid_count": len(model.solids()),
        "volume_mm3": round(float(getattr(model, "volume", 0.0)), 4),
    }


def _projection_camera(
    model: Any,
    view_name: str,
) -> tuple[ProjectionView, Vector, Vector]:
    if view_name not in PROJECTION_VIEWS:
        valid = ", ".join(sorted(PROJECTION_VIEWS))
        raise ValueError(f"Unknown projection view '{view_name}'. Valid views: {valid}")

    view = PROJECTION_VIEWS[view_name]
    bbox = model.bounding_box()
    center = bbox.center()
    direction = Vector(*view.direction).normalized()
    distance = max(float(bbox.diagonal), 1.0) * 3.0
    camera_origin = Vector(
        center.X + direction.X * distance,
        center.Y + direction.Y * distance,
        center.Z + direction.Z * distance,
    )
    return view, camera_origin, center


def _project_to_viewport(
    shape: Any,
    view: ProjectionView,
    camera_origin: Vector,
    look_at: Vector,
):
    return shape.project_to_viewport(
        tuple(camera_origin),
        viewport_up=view.up,
        look_at=tuple(look_at),
    )


def render_projection_svg(
    model: Any,
    output_path: str | Path,
    view_name: str = "isometric",
    *,
    include_hidden: bool = True,
    margin_mm: float = 4.0,
    line_weight_mm: float = 0.12,
) -> Path:
    """Write an orthographic hidden-line SVG projection for a build123d model."""

    view, camera_origin, look_at = _projection_camera(model, view_name)
    visible_edges, hidden_edges = _project_to_viewport(
        model,
        view,
        camera_origin,
        look_at,
    )

    exporter = ExportSVG(margin=margin_mm, line_weight=line_weight_mm)
    if include_hidden and len(hidden_edges) > 0:
        exporter.add_layer(
            "hidden",
            line_color=(150, 150, 150),
            line_weight=line_weight_mm * 0.7,
            line_type=LineType.HIDDEN,
        )
        exporter.add_shape(hidden_edges, layer="hidden")

    exporter.add_layer(
        "visible",
        line_color=(20, 20, 20),
        line_weight=line_weight_mm,
        line_type=LineType.CONTINUOUS,
    )
    exporter.add_shape(visible_edges, layer="visible")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output))
    return output


def render_interference_projection_svg(
    model: Any,
    interference_solids: list[InterferenceSolid],
    output_path: str | Path,
    view_name: str = "isometric",
    *,
    include_hidden: bool = True,
    margin_mm: float = 4.0,
    line_weight_mm: float = 0.12,
    interference_line_weight_mm: float = 0.42,
) -> Path:
    """Write an SVG projection with interference volumes highlighted in red."""

    view, camera_origin, look_at = _projection_camera(model, view_name)
    visible_edges, hidden_edges = _project_to_viewport(
        model,
        view,
        camera_origin,
        look_at,
    )

    exporter = ExportSVG(margin=margin_mm, line_weight=line_weight_mm)
    if include_hidden and len(hidden_edges) > 0:
        exporter.add_layer(
            "assembly-hidden",
            line_color=(185, 185, 185),
            line_weight=line_weight_mm * 0.7,
            line_type=LineType.HIDDEN,
        )
        exporter.add_shape(hidden_edges, layer="assembly-hidden")

    exporter.add_layer(
        "assembly-visible",
        line_color=(80, 80, 80),
        line_weight=line_weight_mm,
        line_type=LineType.CONTINUOUS,
    )
    exporter.add_shape(visible_edges, layer="assembly-visible")

    interference_edges = []
    for interference_solid in interference_solids:
        red_visible, red_hidden = _project_to_viewport(
            interference_solid.shape,
            view,
            camera_origin,
            look_at,
        )
        interference_edges.extend(red_visible)
        interference_edges.extend(red_hidden)

    if interference_edges:
        exporter.add_layer(
            "interference",
            line_color=(220, 0, 0),
            line_weight=interference_line_weight_mm,
            line_type=LineType.CONTINUOUS,
        )
        exporter.add_shape(interference_edges, layer="interference")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output))
    return output


def render_highlighted_projection_svg(
    model: Any,
    highlighted_shapes: list[Any] | tuple[Any, ...],
    output_path: str | Path,
    view_name: str = "isometric",
    *,
    include_hidden: bool = True,
    margin_mm: float = 4.0,
    line_weight_mm: float = 0.12,
    highlight_line_weight_mm: float = 0.3,
    highlight_color: tuple[int, int, int] = (29, 95, 153),
) -> Path:
    """Write an assembly projection with selected shapes emphasized in blue."""

    view, camera_origin, look_at = _projection_camera(model, view_name)
    visible_edges, hidden_edges = _project_to_viewport(
        model,
        view,
        camera_origin,
        look_at,
    )

    exporter = ExportSVG(margin=margin_mm, line_weight=line_weight_mm)
    if include_hidden and len(hidden_edges) > 0:
        exporter.add_layer(
            "assembly-hidden",
            line_color=(190, 190, 190),
            line_weight=line_weight_mm * 0.7,
            line_type=LineType.HIDDEN,
        )
        exporter.add_shape(hidden_edges, layer="assembly-hidden")

    exporter.add_layer(
        "assembly-visible",
        line_color=(90, 90, 90),
        line_weight=line_weight_mm,
        line_type=LineType.CONTINUOUS,
    )
    exporter.add_shape(visible_edges, layer="assembly-visible")

    highlight_visible_edges = []
    highlight_hidden_edges = []
    for shape in highlighted_shapes:
        shape_visible, shape_hidden = _project_to_viewport(
            shape,
            view,
            camera_origin,
            look_at,
        )
        highlight_visible_edges.extend(shape_visible)
        highlight_hidden_edges.extend(shape_hidden)

    if include_hidden and highlight_hidden_edges:
        exporter.add_layer(
            "highlight-hidden",
            line_color=highlight_color,
            line_weight=highlight_line_weight_mm * 0.8,
            line_type=LineType.HIDDEN,
        )
        exporter.add_shape(highlight_hidden_edges, layer="highlight-hidden")

    if highlight_visible_edges:
        exporter.add_layer(
            "highlight-visible",
            line_color=highlight_color,
            line_weight=highlight_line_weight_mm,
            line_type=LineType.CONTINUOUS,
        )
        exporter.add_shape(highlight_visible_edges, layer="highlight-visible")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    exporter.write(str(output))
    return output


def _bbox_overlaps(first_box: Any, second_box: Any, tolerance: float = 1e-6) -> bool:
    return (
        first_box.min.X <= second_box.max.X + tolerance
        and first_box.max.X + tolerance >= second_box.min.X
        and first_box.min.Y <= second_box.max.Y + tolerance
        and first_box.max.Y + tolerance >= second_box.min.Y
        and first_box.min.Z <= second_box.max.Z + tolerance
        and first_box.max.Z + tolerance >= second_box.min.Z
    )


def _has_solid_volume(shape: Any) -> bool:
    try:
        return len(shape.solids()) > 0
    except Exception:
        return False


def find_interferences(
    model: Any,
    *,
    min_volume_mm3: float = DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
    bbox_tolerance_mm: float = 1e-6,
) -> InterferenceReport:
    """Find volumetric overlaps among the direct children of a model."""

    report, _solids = collect_interference_solids(
        model,
        min_volume_mm3=min_volume_mm3,
        bbox_tolerance_mm=bbox_tolerance_mm,
    )
    return report


def collect_interference_solids(
    model: Any,
    *,
    min_volume_mm3: float = DEFAULT_MIN_INTERFERENCE_VOLUME_MM3,
    bbox_tolerance_mm: float = 1e-6,
) -> tuple[InterferenceReport, list[InterferenceSolid]]:
    """Find volumetric overlaps and keep the overlap solids for visualization."""

    children = list(getattr(model, "children", ()) or ())
    solid_children = []
    for index, child in enumerate(children, start=1):
        if not _has_solid_volume(child):
            continue
        solid_children.append(
            {
                "index": index,
                "shape": child,
                "label": _shape_label(child, index),
                "bbox": child.bounding_box(),
            }
        )

    interferences: list[Interference] = []
    interference_solids: list[InterferenceSolid] = []
    errors: list[InterferenceError] = []
    candidate_pair_count = 0
    tested_pair_count = 0

    for first, second in combinations(solid_children, 2):
        if not _bbox_overlaps(first["bbox"], second["bbox"], bbox_tolerance_mm):
            continue

        first_label = first["label"]
        second_label = second["label"]
        candidate_pair_count += 1

        try:
            common = first["shape"].intersect(second["shape"])
            tested_pair_count += 1
            volume = (
                abs(float(getattr(common, "volume", 0.0)))
                if common is not None
                else 0.0
            )
        except Exception as exc:
            errors.append(
                InterferenceError(
                    first=first_label,
                    second=second_label,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
            continue

        if volume >= min_volume_mm3:
            interference = Interference(
                first=first_label,
                second=second_label,
                volume_mm3=round(volume, 6),
                first_bbox_mm=_bounding_box_summary_from_bbox(first["bbox"]),
                second_bbox_mm=_bounding_box_summary_from_bbox(second["bbox"]),
            )
            interferences.append(interference)
            interference_solids.append(
                InterferenceSolid(interference=interference, shape=common)
            )

    ranked = sorted(
        zip(interferences, interference_solids, strict=True),
        key=lambda pair: pair[0].volume_mm3,
        reverse=True,
    )
    interferences = [interference for interference, _solid in ranked]
    interference_solids = [solid for _interference, solid in ranked]

    return (
        InterferenceReport(
            child_count=len(children),
            solid_child_count=len(solid_children),
            candidate_pair_count=candidate_pair_count,
            tested_pair_count=tested_pair_count,
            min_volume_mm3=min_volume_mm3,
            interferences=interferences,
            errors=errors,
        ),
        interference_solids,
    )
