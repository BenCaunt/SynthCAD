from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element, ElementTree, SubElement

from synthcad.cad.common import export_model
from synthcad.paths import GENERATED_DIR


MM_TO_M = 0.001
DEFAULT_MESH_SCALE = (MM_TO_M, MM_TO_M, MM_TO_M)


@dataclass(frozen=True)
class MeshAsset:
    name: str
    model: Any
    filename: str | None = None
    scale: tuple[float, float, float] = DEFAULT_MESH_SCALE

    @property
    def stem(self) -> str:
        candidate = self.filename or self.name
        return sanitize_filename_stem(candidate)

    @property
    def relative_path(self) -> str:
        return f"meshes/{self.stem}.stl"


@dataclass(frozen=True)
class InertialSpec:
    mass_kg: float
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    ixx: float = 0.0
    ixy: float = 0.0
    ixz: float = 0.0
    iyy: float = 0.0
    iyz: float = 0.0
    izz: float = 0.0


@dataclass(frozen=True)
class VisualSpec:
    mesh: MeshAsset
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    material_name: str | None = None
    rgba: tuple[float, float, float, float] | None = None


@dataclass(frozen=True)
class CollisionSpec:
    mesh: MeshAsset
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class LinkSpec:
    name: str
    inertial: InertialSpec | None = None
    visual: VisualSpec | None = None
    collision: CollisionSpec | None = None


@dataclass(frozen=True)
class JointLimit:
    effort: float
    velocity: float
    lower: float | None = None
    upper: float | None = None


@dataclass(frozen=True)
class JointDynamics:
    damping: float | None = None
    friction: float | None = None


@dataclass(frozen=True)
class JointSpec:
    name: str
    joint_type: str
    parent: str
    child: str
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    axis: tuple[float, float, float] | None = None
    limit: JointLimit | None = None
    dynamics: JointDynamics | None = None


@dataclass(frozen=True)
class RobotDescription:
    name: str
    project: str
    links: tuple[LinkSpec, ...]
    joints: tuple[JointSpec, ...]
    artifact_name: str | None = None
    notes: tuple[str, ...] = ()

    @property
    def output_stem(self) -> str:
        return sanitize_artifact_name(self.artifact_name or self.name)

    def output_dir(self, generated_dir: str | Path = GENERATED_DIR) -> Path:
        return Path(generated_dir) / self.project / "urdf" / self.output_stem


def sanitize_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "item"


def sanitize_filename_stem(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", value.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("._-")
    return normalized or "asset"


def sanitize_artifact_name(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("._-")
    return normalized or "robot"


def hex_to_rgba(color: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    value = color.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Expected 6-digit hex color, got {color!r}")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
        alpha,
    )


def bbox_center_mm(shape: Any) -> tuple[float, float, float]:
    center = shape.bounding_box().center()
    return tuple(float(value) for value in center)


def bbox_size_mm(shape: Any) -> tuple[float, float, float]:
    size = shape.bounding_box().size
    return tuple(float(value) for value in size)


def box_inertia_kgm2(
    mass_kg: float,
    size_mm: tuple[float, float, float],
) -> tuple[float, float, float]:
    x_m, y_m, z_m = (float(value) * MM_TO_M for value in size_mm)
    ixx = mass_kg * (y_m**2 + z_m**2) / 12.0
    iyy = mass_kg * (x_m**2 + z_m**2) / 12.0
    izz = mass_kg * (x_m**2 + y_m**2) / 12.0
    return ixx, iyy, izz


def cylinder_inertia_kgm2(
    mass_kg: float,
    radius_mm: float,
    length_mm: float,
    axis: str = "z",
) -> tuple[float, float, float]:
    radius_m = float(radius_mm) * MM_TO_M
    length_m = float(length_mm) * MM_TO_M
    axial = 0.5 * mass_kg * radius_m**2
    transverse = mass_kg * (3.0 * radius_m**2 + length_m**2) / 12.0

    axis_name = axis.lower()
    if axis_name == "x":
        return axial, transverse, transverse
    if axis_name == "y":
        return transverse, axial, transverse
    if axis_name == "z":
        return transverse, transverse, axial
    raise ValueError(f"Unsupported cylinder axis {axis!r}; expected x, y, or z")


def inertial_from_bbox(shape: Any, mass_kg: float) -> InertialSpec:
    center_mm = bbox_center_mm(shape)
    size_mm = bbox_size_mm(shape)
    ixx, iyy, izz = box_inertia_kgm2(mass_kg, size_mm)
    return InertialSpec(
        mass_kg=mass_kg,
        xyz_mm=center_mm,
        ixx=ixx,
        iyy=iyy,
        izz=izz,
    )


def inertial_from_box(
    *,
    mass_kg: float,
    size_mm: tuple[float, float, float],
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> InertialSpec:
    ixx, iyy, izz = box_inertia_kgm2(mass_kg, size_mm)
    return InertialSpec(
        mass_kg=mass_kg,
        xyz_mm=xyz_mm,
        rpy_deg=rpy_deg,
        ixx=ixx,
        iyy=iyy,
        izz=izz,
    )


def inertial_from_cylinder(
    *,
    mass_kg: float,
    radius_mm: float,
    length_mm: float,
    axis: str = "z",
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> InertialSpec:
    ixx, iyy, izz = cylinder_inertia_kgm2(mass_kg, radius_mm, length_mm, axis=axis)
    return InertialSpec(
        mass_kg=mass_kg,
        xyz_mm=xyz_mm,
        rpy_deg=rpy_deg,
        ixx=ixx,
        iyy=iyy,
        izz=izz,
    )


def fixed_joint(
    name: str,
    parent: str,
    child: str,
    xyz_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
    rpy_deg: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> JointSpec:
    return JointSpec(
        name=name,
        joint_type="fixed",
        parent=parent,
        child=child,
        xyz_mm=xyz_mm,
        rpy_deg=rpy_deg,
    )


def _format_float(value: float) -> str:
    text = f"{value:.9f}".rstrip("0").rstrip(".")
    return text if text and text != "-0" else "0"


def _meters_string(values_mm: tuple[float, float, float]) -> str:
    return " ".join(_format_float(float(value) * MM_TO_M) for value in values_mm)


def _radians_string(values_deg: tuple[float, float, float]) -> str:
    return " ".join(_format_float(math.radians(float(value))) for value in values_deg)


def _axis_string(axis: tuple[float, float, float]) -> str:
    return " ".join(_format_float(float(value)) for value in axis)


def _scale_string(scale: tuple[float, float, float]) -> str:
    return " ".join(_format_float(float(value)) for value in scale)


def _rgba_string(rgba: tuple[float, float, float, float]) -> str:
    return " ".join(_format_float(float(value)) for value in rgba)


def _add_origin(parent: Element, xyz_mm: tuple[float, float, float], rpy_deg: tuple[float, float, float]) -> None:
    SubElement(
        parent,
        "origin",
        {
            "xyz": _meters_string(xyz_mm),
            "rpy": _radians_string(rpy_deg),
        },
    )


def _add_mesh_geometry(parent: Element, spec: VisualSpec | CollisionSpec) -> None:
    geometry = SubElement(parent, "geometry")
    SubElement(
        geometry,
        "mesh",
        {
            "filename": spec.mesh.relative_path,
            "scale": _scale_string(spec.mesh.scale),
        },
    )


def _write_link(parent: Element, link: LinkSpec) -> None:
    link_element = SubElement(parent, "link", {"name": link.name})

    if link.inertial is not None:
        inertial = SubElement(link_element, "inertial")
        _add_origin(inertial, link.inertial.xyz_mm, link.inertial.rpy_deg)
        SubElement(inertial, "mass", {"value": _format_float(link.inertial.mass_kg)})
        SubElement(
            inertial,
            "inertia",
            {
                "ixx": _format_float(link.inertial.ixx),
                "ixy": _format_float(link.inertial.ixy),
                "ixz": _format_float(link.inertial.ixz),
                "iyy": _format_float(link.inertial.iyy),
                "iyz": _format_float(link.inertial.iyz),
                "izz": _format_float(link.inertial.izz),
            },
        )

    if link.visual is not None:
        visual = SubElement(link_element, "visual")
        _add_origin(visual, link.visual.xyz_mm, link.visual.rpy_deg)
        _add_mesh_geometry(visual, link.visual)
        if link.visual.rgba is not None:
            material_name = link.visual.material_name or f"{link.name}_material"
            material = SubElement(visual, "material", {"name": material_name})
            SubElement(material, "color", {"rgba": _rgba_string(link.visual.rgba)})

    if link.collision is not None:
        collision = SubElement(link_element, "collision")
        _add_origin(collision, link.collision.xyz_mm, link.collision.rpy_deg)
        _add_mesh_geometry(collision, link.collision)


def _write_joint(parent: Element, joint: JointSpec) -> None:
    joint_element = SubElement(
        parent,
        "joint",
        {
            "name": joint.name,
            "type": joint.joint_type,
        },
    )
    _add_origin(joint_element, joint.xyz_mm, joint.rpy_deg)
    SubElement(joint_element, "parent", {"link": joint.parent})
    SubElement(joint_element, "child", {"link": joint.child})

    if joint.axis is not None and joint.joint_type not in {"fixed", "floating"}:
        SubElement(joint_element, "axis", {"xyz": _axis_string(joint.axis)})

    if joint.limit is not None:
        attributes = {
            "effort": _format_float(joint.limit.effort),
            "velocity": _format_float(joint.limit.velocity),
        }
        if joint.limit.lower is not None:
            attributes["lower"] = _format_float(joint.limit.lower)
        if joint.limit.upper is not None:
            attributes["upper"] = _format_float(joint.limit.upper)
        SubElement(joint_element, "limit", attributes)

    if joint.dynamics is not None:
        attributes: dict[str, str] = {}
        if joint.dynamics.damping is not None:
            attributes["damping"] = _format_float(joint.dynamics.damping)
        if joint.dynamics.friction is not None:
            attributes["friction"] = _format_float(joint.dynamics.friction)
        if attributes:
            SubElement(joint_element, "dynamics", attributes)


def _collect_assets(robot: RobotDescription) -> dict[str, MeshAsset]:
    assets: dict[str, MeshAsset] = {}
    for link in robot.links:
        for spec in (link.visual, link.collision):
            if spec is None:
                continue
            key = spec.mesh.stem
            assets.setdefault(key, spec.mesh)
    return assets


def _validate_robot_description(robot: RobotDescription) -> None:
    link_names = [link.name for link in robot.links]
    duplicate_links = sorted({name for name in link_names if link_names.count(name) > 1})
    if duplicate_links:
        raise ValueError(f"Duplicate URDF link names: {', '.join(duplicate_links)}")

    joint_names = [joint.name for joint in robot.joints]
    duplicate_joints = sorted({name for name in joint_names if joint_names.count(name) > 1})
    if duplicate_joints:
        raise ValueError(f"Duplicate URDF joint names: {', '.join(duplicate_joints)}")

    known_links = set(link_names)
    parent_count: dict[str, int] = {name: 0 for name in link_names}
    for joint in robot.joints:
        if joint.parent not in known_links:
            raise ValueError(f"Joint {joint.name!r} references unknown parent link {joint.parent!r}")
        if joint.child not in known_links:
            raise ValueError(f"Joint {joint.name!r} references unknown child link {joint.child!r}")
        parent_count[joint.child] += 1
        if parent_count[joint.child] > 1:
            raise ValueError(f"Link {joint.child!r} has more than one parent joint")

    roots = [name for name, count in parent_count.items() if count == 0]
    if len(roots) != 1:
        raise ValueError(
            "URDF must have exactly one root link; found "
            f"{len(roots)} roots: {', '.join(sorted(roots))}"
        )


def export_urdf_package(
    robot: RobotDescription,
    output_dir: str | Path = GENERATED_DIR,
) -> list[Path]:
    _validate_robot_description(robot)

    package_dir = robot.output_dir(output_dir)
    mesh_dir = package_dir / "meshes"
    mesh_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    asset_records: list[dict[str, str]] = []
    for asset in _collect_assets(robot).values():
        [mesh_path] = export_model(asset.model, mesh_dir / asset.stem, formats=("stl",))
        written.append(mesh_path)
        asset_records.append(
            {
                "name": asset.name,
                "path": str(mesh_path),
                "relative_path": asset.relative_path,
            }
        )

    robot_element = Element("robot", {"name": robot.name})
    for link in robot.links:
        _write_link(robot_element, link)
    for joint in robot.joints:
        _write_joint(robot_element, joint)

    urdf_path = package_dir / f"{robot.output_stem}.urdf"
    tree = ElementTree(robot_element)
    ET.indent(tree, space="  ")
    tree.write(urdf_path, encoding="utf-8", xml_declaration=True)
    written.append(urdf_path)

    manifest_path = package_dir / "urdf-manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "robot_name": robot.name,
                "project": robot.project,
                "artifact_name": robot.output_stem,
                "package_dir": str(package_dir),
                "urdf": str(urdf_path),
                "meshes": asset_records,
                "links": [link.name for link in robot.links],
                "joints": [joint.name for joint in robot.joints],
                "notes": list(robot.notes),
            },
            indent=2,
        )
        + "\n"
    )
    written.append(manifest_path)
    return written
