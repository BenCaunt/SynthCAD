from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
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
