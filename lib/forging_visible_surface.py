"""
Fused Billet Visible Surface Helpers
====================================

The simulator still keeps per-layer meshes as a compatibility representation
for existing forging operations.  A forge-welded billet, however, should render
as one continuous body with an internal material field.  This module generates
visible render surfaces by sampling that material field instead of exposing
every internal layer interface as physical geometry.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Any

import numpy as np

from lib.forging_utils import compute_billet_frame

MM_PER_INCH = 25.4


@dataclass(frozen=True)
class MaterialInterval:
    """Original material interval used to color sampled render surfaces."""

    z_min: float
    z_max: float
    color: tuple[float, float, float]
    layer_index: int


def _latest_history_entry(billet) -> dict[str, Any] | None:
    if not billet.operation_history:
        return None
    latest = billet.operation_history[-1]
    return latest if isinstance(latest, dict) else None


def _latest_twist_parameters(billet) -> dict[str, Any] | None:
    latest = _latest_history_entry(billet)
    if not latest or latest.get("operation") != "twist":
        return None
    parameters = latest.get("parameters")
    return parameters if isinstance(parameters, dict) else None


def _material_intervals_from_parameters(parameters: dict[str, Any]) -> list[MaterialInterval]:
    raw_layers = parameters.get("material_layers")
    if not isinstance(raw_layers, list):
        return []

    intervals: list[MaterialInterval] = []
    for raw_layer in raw_layers:
        if not isinstance(raw_layer, dict):
            continue
        color = raw_layer.get("color")
        if not isinstance(color, (list, tuple)) or len(color) != 3:
            continue
        intervals.append(
            MaterialInterval(
                z_min=float(raw_layer["z_min"]),
                z_max=float(raw_layer["z_max"]),
                color=(float(color[0]), float(color[1]), float(color[2])),
                layer_index=int(raw_layer.get("layer_index", len(intervals))),
            )
        )

    intervals.sort(key=lambda interval: (interval.z_min, interval.z_max, interval.layer_index))
    return intervals


def _material_index_for_z(z_value: float, intervals: list[MaterialInterval]) -> int:
    if not intervals:
        return 0

    tolerance = 1e-7
    for index, interval in enumerate(intervals):
        if interval.z_min - tolerance <= z_value <= interval.z_max + tolerance:
            return index

    centers = np.array(
        [(interval.z_min + interval.z_max) * 0.5 for interval in intervals],
        dtype=np.float64,
    )
    return int(np.argmin(np.abs(centers - z_value)))


def _source_boundary_point(
    perimeter_angle: float,
    half_x: float,
    half_z: float,
    target_round_radius: float,
    roundness_factor: float,
    radial_fraction: float = 1.0,
) -> tuple[float, float, float, float]:
    """
    Return pre-twist and flowed X/Z coordinates for a source rectangle ray.

    The point is parameterized in the original square/rectangular cross-section.
    `radial_fraction=1` is the exterior perimeter; lower values are used for
    end caps.  The flow calculation mirrors `lib.forging_twist.apply_twist`.
    """
    cos_phi = float(np.cos(perimeter_angle))
    sin_phi = float(np.sin(perimeter_angle))
    square_scale = 1.0 / max(abs(cos_phi), abs(sin_phi), 1e-9)

    x_source = half_x * cos_phi * square_scale * radial_fraction
    z_source = half_z * sin_phi * square_scale * radial_fraction
    rectangular_radius = radial_fraction

    x_round_target = cos_phi * target_round_radius * rectangular_radius
    z_round_target = sin_phi * target_round_radius * rectangular_radius
    x_flowed = x_source + (x_round_target - x_source) * roundness_factor
    z_flowed = z_source + (z_round_target - z_source) * roundness_factor
    return x_source, z_source, x_flowed, z_flowed


def _flow_source_rect_point(
    x_source: float,
    z_source: float,
    half_x: float,
    half_z: float,
    target_round_radius: float,
    roundness_factor: float,
) -> tuple[float, float]:
    """Map a source X/Z point through the same round-bar flow as Twist."""
    x_normalized = x_source / max(half_x, 1e-9)
    z_normalized = z_source / max(half_z, 1e-9)
    rectangular_radius = max(abs(x_normalized), abs(z_normalized))
    polar_angle = float(np.arctan2(z_normalized, x_normalized))

    x_round_target = np.cos(polar_angle) * target_round_radius * rectangular_radius
    z_round_target = np.sin(polar_angle) * target_round_radius * rectangular_radius
    x_flowed = x_source + (x_round_target - x_source) * roundness_factor
    z_flowed = z_source + (z_round_target - z_source) * roundness_factor
    return float(x_flowed), float(z_flowed)


def _cap_spiral_turns(parameters: dict[str, Any]) -> float:
    """
    Return a readable end-grain spiral intensity from the finished twist density.

    The end cap is a cross-section view of the material field.  Using total
    twist count directly would alias badly on long bars; finished twist density
    captures how tight the hot-twisted material became while keeping the layer
    lines readable.
    """
    total_twists = float(parameters.get("total_twists", 0.0))
    if abs(total_twists) < 1e-9:
        return 0.0

    y_min = float(parameters["y_min"])
    y_max = float(parameters["y_max"])
    source_length_mm = max(y_max - y_min, 1e-9)
    axial_scale = max(float(parameters.get("axial_scale", 1.0)), 1e-9)
    finished_length_inches = (source_length_mm * axial_scale) / MM_PER_INCH
    finished_density = abs(total_twists) / max(finished_length_inches, 1e-9)
    return float(np.sign(total_twists) * min(finished_density, 12.0))


def _spiral_material_z(
    x_source: float,
    z_source: float,
    half_x: float,
    half_z: float,
    center_z: float,
    spiral_turns: float,
) -> float:
    """
    Sample the original flat layer field after a smooth end-grain spiral warp.

    Conceptually this takes the original horizontal layer lines and applies a
    radius-dependent twist, producing continuous spiral-bent stripes instead of
    polar wedge/checker artifacts.
    """
    x_normalized = x_source / max(half_x, 1e-9)
    z_normalized = z_source / max(half_z, 1e-9)
    radius = min(max(abs(x_normalized), abs(z_normalized)), 1.0)
    if radius < 1e-9 or abs(spiral_turns) < 1e-9:
        return center_z + z_normalized * half_z

    source_angle = float(np.arctan2(z_normalized, x_normalized))
    disk_x = float(np.cos(source_angle) * radius)
    disk_z = float(np.sin(source_angle) * radius)
    spiral_angle = 2.0 * np.pi * spiral_turns * radius
    material_z_normalized = -disk_x * np.sin(spiral_angle) + disk_z * np.cos(spiral_angle)
    return float(center_z + material_z_normalized * half_z)


def _twist_forward_sample(
    *,
    source_y: float,
    x_flowed: float,
    z_flowed: float,
    center_x: float,
    center_y: float,
    center_z: float,
    y_min: float,
    span_y: float,
    angle_rad: float,
    axial_scale: float,
) -> tuple[float, float, float]:
    normalized_position = (source_y - y_min) / max(span_y, 1e-9)
    current_angle = angle_rad * normalized_position
    cos_angle = float(np.cos(current_angle))
    sin_angle = float(np.sin(current_angle))

    x = x_flowed * cos_angle - z_flowed * sin_angle + center_x
    y = center_y + (source_y - center_y) * axial_scale
    z = x_flowed * sin_angle + z_flowed * cos_angle + center_z
    return x, y, z


def _append_grid_side(
    vertices: list[tuple[float, float, float]],
    material_z_values: list[float],
    triangles: list[tuple[int, int, int]],
    *,
    parameters: dict[str, Any],
    circumference_segments: int,
    length_segments: int,
) -> None:
    y_min = float(parameters["y_min"])
    y_max = float(parameters["y_max"])
    span_y = max(y_max - y_min, 1e-9)
    center_y = float(parameters.get("center_y", (y_min + y_max) * 0.5))
    center_x = float(parameters["center_x"])
    center_z = float(parameters["center_z"])
    half_x = max(float(parameters["source_span_x"]) * 0.5, 1e-9)
    half_z = max(float(parameters["source_span_z"]) * 0.5, 1e-9)
    axial_scale = float(parameters["axial_scale"])
    roundness_factor = float(parameters["roundness_factor"])
    target_round_radius = float(parameters["target_round_radius"])
    angle_rad = np.deg2rad(float(parameters["angle_degrees"]))

    start_index = len(vertices)
    for y_index in range(length_segments + 1):
        source_y = y_min + span_y * (y_index / length_segments)
        for circum_index in range(circumference_segments):
            perimeter_angle = 2.0 * np.pi * (circum_index / circumference_segments)
            _, z_source, x_flowed, z_flowed = _source_boundary_point(
                perimeter_angle,
                half_x,
                half_z,
                target_round_radius,
                roundness_factor,
            )
            vertices.append(
                _twist_forward_sample(
                    source_y=source_y,
                    x_flowed=x_flowed,
                    z_flowed=z_flowed,
                    center_x=center_x,
                    center_y=center_y,
                    center_z=center_z,
                    y_min=y_min,
                    span_y=span_y,
                    angle_rad=angle_rad,
                    axial_scale=axial_scale,
                )
            )
            material_z_values.append(center_z + z_source)

    for y_index in range(length_segments):
        row = start_index + y_index * circumference_segments
        next_row = row + circumference_segments
        for circum_index in range(circumference_segments):
            a = row + circum_index
            b = row + ((circum_index + 1) % circumference_segments)
            c = next_row + circum_index
            d = next_row + ((circum_index + 1) % circumference_segments)
            triangles.append((a, c, b))
            triangles.append((b, c, d))


def _append_end_cap(
    vertices: list[tuple[float, float, float]],
    material_z_values: list[float],
    triangles: list[tuple[int, int, int]],
    *,
    parameters: dict[str, Any],
    source_y: float,
    circumference_segments: int,
    radial_segments: int,
    reverse_winding: bool,
) -> None:
    y_min = float(parameters["y_min"])
    y_max = float(parameters["y_max"])
    span_y = max(y_max - y_min, 1e-9)
    center_y = float(parameters.get("center_y", (y_min + y_max) * 0.5))
    center_x = float(parameters["center_x"])
    center_z = float(parameters["center_z"])
    half_x = max(float(parameters["source_span_x"]) * 0.5, 1e-9)
    half_z = max(float(parameters["source_span_z"]) * 0.5, 1e-9)
    axial_scale = float(parameters["axial_scale"])
    roundness_factor = float(parameters["roundness_factor"])
    target_round_radius = float(parameters["target_round_radius"])
    angle_rad = np.deg2rad(float(parameters["angle_degrees"]))
    spiral_turns = _cap_spiral_turns(parameters)
    if reverse_winding:
        spiral_turns *= -1.0
    grid_segments = int(max(
        circumference_segments,
        radial_segments * 8,
        ceil(abs(spiral_turns) * 16.0),
        32,
    ))

    start_index = len(vertices)
    for z_index in range(grid_segments + 1):
        z_source = -half_z + (2.0 * half_z) * (z_index / grid_segments)
        for x_index in range(grid_segments + 1):
            x_source = -half_x + (2.0 * half_x) * (x_index / grid_segments)
            x_flowed, z_flowed = _flow_source_rect_point(
                x_source,
                z_source,
                half_x,
                half_z,
                target_round_radius,
                roundness_factor,
            )
            vertices.append(
                _twist_forward_sample(
                    source_y=source_y,
                    x_flowed=x_flowed,
                    z_flowed=z_flowed,
                    center_x=center_x,
                    center_y=center_y,
                    center_z=center_z,
                    y_min=y_min,
                    span_y=span_y,
                    angle_rad=angle_rad,
                    axial_scale=axial_scale,
                )
            )
            material_z_values.append(
                _spiral_material_z(
                    x_source,
                    z_source,
                    half_x,
                    half_z,
                    center_z,
                    spiral_turns,
                )
            )

    row_stride = grid_segments + 1
    for z_index in range(grid_segments):
        for x_index in range(grid_segments):
            a = start_index + z_index * row_stride + x_index
            b = a + 1
            c = a + row_stride
            d = c + 1
            if reverse_winding:
                triangles.append((a, b, c))
                triangles.append((b, d, c))
            else:
                triangles.append((a, c, b))
                triangles.append((b, c, d))


def _split_triangles_by_material(
    vertices: np.ndarray,
    material_z_values: np.ndarray,
    triangles: np.ndarray,
    intervals: list[MaterialInterval],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[float, float, float], dict[str, Any]] = {}

    for triangle in triangles:
        material_z = float(material_z_values[triangle].mean())
        interval = intervals[_material_index_for_z(material_z, intervals)]
        group = grouped.setdefault(
            interval.color,
            {
                "color": [float(interval.color[0]), float(interval.color[1]), float(interval.color[2])],
                "vertices": [],
                "triangles": [],
                "_index_map": {},
            },
        )
        index_map = group["_index_map"]
        local_triangle: list[int] = []
        for vertex_index in triangle:
            key = int(vertex_index)
            local_index = index_map.get(key)
            if local_index is None:
                local_index = len(group["vertices"]) // 3
                index_map[key] = local_index
                group["vertices"].extend(vertices[key].astype(float).tolist())
            local_triangle.append(local_index)
        group["triangles"].extend(local_triangle)

    output: list[dict[str, Any]] = []
    for group in grouped.values():
        group.pop("_index_map", None)
        output.append(group)
    output.sort(key=lambda item: tuple(item["color"]))
    return output


def can_build_twist_visible_surface(billet) -> bool:
    parameters = _latest_twist_parameters(billet)
    if not parameters:
        return False
    intervals = _material_intervals_from_parameters(parameters)
    required = (
        "angle_degrees",
        "axial_scale",
        "roundness_factor",
        "target_round_radius",
        "source_span_x",
        "source_span_z",
        "center_x",
        "center_y",
        "center_z",
        "y_min",
        "y_max",
    )
    return bool(intervals) and all(key in parameters for key in required)


def build_twist_visible_surface_layers(
    billet,
    *,
    circumference_segments: int = 96,
    length_segments: int | None = None,
    radial_segments: int = 12,
) -> list[dict[str, Any]]:
    """
    Build a continuous, material-colored render surface for the latest Twist.

    Returns a list shaped like the existing layer serialization payload:
    each entry has `color`, flattened `vertices`, and flattened `triangles`.
    The entries are render-material groups, not separate physical layers.
    """
    parameters = _latest_twist_parameters(billet)
    if not parameters:
        raise ValueError("latest billet operation is not a twist")

    intervals = _material_intervals_from_parameters(parameters)
    if not intervals:
        raise ValueError("twist operation did not record material layer intervals")

    total_twists = abs(float(parameters.get("total_twists", 1.0)))
    if length_segments is None:
        length_segments = int(np.clip(ceil(total_twists * 18.0), 96, 1200))

    circumference_segments = int(max(circumference_segments, 16))
    length_segments = int(max(length_segments, 2))
    radial_segments = int(max(radial_segments, 2))

    vertices: list[tuple[float, float, float]] = []
    material_z_values: list[float] = []
    triangles: list[tuple[int, int, int]] = []

    _append_grid_side(
        vertices,
        material_z_values,
        triangles,
        parameters=parameters,
        circumference_segments=circumference_segments,
        length_segments=length_segments,
    )
    _append_end_cap(
        vertices,
        material_z_values,
        triangles,
        parameters=parameters,
        source_y=float(parameters["y_min"]),
        circumference_segments=circumference_segments,
        radial_segments=radial_segments,
        reverse_winding=True,
    )
    _append_end_cap(
        vertices,
        material_z_values,
        triangles,
        parameters=parameters,
        source_y=float(parameters["y_max"]),
        circumference_segments=circumference_segments,
        radial_segments=radial_segments,
        reverse_winding=False,
    )

    vertices_array = np.asarray(vertices, dtype=np.float64)
    material_z_array = np.asarray(material_z_values, dtype=np.float64)
    triangles_array = np.asarray(triangles, dtype=np.int64)
    return _split_triangles_by_material(vertices_array, material_z_array, triangles_array, intervals)


def build_visible_surface_layers(billet) -> list[dict[str, Any]] | None:
    """Return fused render layers for operations that support material fields."""
    if can_build_twist_visible_surface(billet):
        return build_twist_visible_surface_layers(billet)
    return None


def summarize_visible_surface_layers(layers: list[dict[str, Any]]) -> dict[str, int]:
    """Return simple health metrics for a serialized visible-surface payload."""
    vertex_count = 0
    triangle_count = 0
    material_count = 0
    for layer in layers:
        vertices = layer.get("vertices", [])
        triangles = layer.get("triangles", [])
        if len(vertices) > 0 and len(triangles) > 0:
            material_count += 1
        vertex_count += len(vertices) // 3
        triangle_count += len(triangles) // 3

    return {
        "render_mesh_count": len(layers),
        "render_material_count": material_count,
        "render_vertex_count": vertex_count,
        "render_triangle_count": triangle_count,
    }


def current_frame_dimensions(billet) -> dict[str, float]:
    """Return actual current fused-body dimensions for API payloads."""
    frame = compute_billet_frame(billet)
    return {
        "width_mm": float(frame.span_x),
        "length_mm": float(frame.span_y),
        "height_mm": float(frame.span_z),
    }
