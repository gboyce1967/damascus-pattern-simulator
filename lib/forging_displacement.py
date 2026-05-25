"""
Forging Displacement Engine
===========================

Shared helpers for treating forging operations as displacement fields.

Each operation supplies a field function that maps the current vertex
positions to displaced positions.  The engine handles subdivision,
application, debug stats, metadata refresh, normal recomputation, and
operation history consistently.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Callable

import numpy as np
import open3d as o3d

from lib.forging_utils import compute_billet_frame, subdivide_if_needed
from lib.logging_config import logger


DEFAULT_OCTAGON_CHAMFER_PERCENT = 45.0
REGULAR_OCTAGON_CHAMFER_PERCENT = float(100.0 * (2.0 / (2.0 + np.sqrt(2.0))))
DEFAULT_OCTAGON_FLOW_STRENGTH = 0.62
DEFAULT_OCTAGON_CENTER_BULGE = 0.0


@dataclass
class DisplacementStats:
    """Summary of one displacement operation."""

    operation: str
    vertices_processed: int
    affected_vertices: int
    max_displacement: float
    mean_displacement: float
    max_axis_displacement: tuple[float, float, float]
    before_span: tuple[float, float, float]
    after_span: tuple[float, float, float]
    volume_ratio: float


def _frame_span_tuple(frame) -> tuple[float, float, float]:
    return (float(frame.span_x), float(frame.span_y), float(frame.span_z))


def _frame_volume(frame) -> float:
    return float(frame.span_x * frame.span_y * frame.span_z)


def _refresh_layer_metadata_from_mesh(layer) -> None:
    """Keep per-layer metadata aligned with live mesh vertices."""
    vertices = np.asarray(layer.mesh.vertices)
    if len(vertices) == 0:
        return

    layer.width = float(vertices[:, 0].max() - vertices[:, 0].min())
    layer.length = float(vertices[:, 1].max() - vertices[:, 1].min())
    layer.thickness = float(vertices[:, 2].max() - vertices[:, 2].min())
    layer.z_position = float(vertices[:, 2].min())


def refresh_billet_metadata_from_geometry(billet) -> None:
    """Update billet width/length and every layer's metadata from geometry."""
    frame = compute_billet_frame(billet)
    billet.width = float(frame.span_x)
    billet.length = float(frame.span_y)

    for layer in billet.layers:
        _refresh_layer_metadata_from_mesh(layer)


DisplacementField = Callable[[np.ndarray, object, int, object], np.ndarray]
MetadataUpdater = Callable[[object, object], None]


def apply_displacement_to_billet(
    billet,
    operation: str,
    field: DisplacementField,
    parameters: dict,
    *,
    subdivide: bool = True,
    min_vertices: int = 200,
    base_iterations: int = 3,
    extra_param: float = 0.0,
    metadata_updater: MetadataUpdater | None = None,
    debug: bool = True,
) -> DisplacementStats:
    """
    Apply a displacement field to every layer in a billet.

    Args:
        billet: Damascus3DBillet instance.
        operation: Operation name to record in histories.
        field: Callable returning displaced vertices for one layer.
        parameters: Operation parameters stored in debug/history records.
        subdivide: If True, densify coarse meshes before applying the field.
        min_vertices: Minimum layer vertex count before subdivision is skipped.
        base_iterations: Base midpoint subdivision iterations.
        extra_param: Magnitude hint for additional subdivision.
        metadata_updater: Optional hook for operation-specific metadata.
        debug: Enable detailed debug logging.
    """
    start_time = datetime.now()

    if subdivide:
        subdivide_if_needed(
            billet,
            min_vertices=min_vertices,
            base_iterations=base_iterations,
            extra_param=extra_param,
        )

    before_frame = compute_billet_frame(billet)
    before_volume = _frame_volume(before_frame)

    vertices_processed = 0
    affected_vertices = 0
    displacement_lengths: list[np.ndarray] = []
    max_axis = np.zeros(3, dtype=np.float64)

    for layer_idx, layer in enumerate(billet.layers):
        before_vertices = np.asarray(layer.mesh.vertices).copy()
        after_vertices = np.asarray(field(before_vertices.copy(), layer, layer_idx, before_frame), dtype=np.float64)

        if after_vertices.shape != before_vertices.shape:
            raise ValueError(
                f"{operation} displacement field returned shape {after_vertices.shape}, "
                f"expected {before_vertices.shape}"
            )

        delta = after_vertices - before_vertices
        lengths = np.linalg.norm(delta, axis=1)
        displacement_lengths.append(lengths)

        vertices_processed += len(before_vertices)
        affected_vertices += int(np.count_nonzero(lengths > 1e-9))
        if len(delta):
            max_axis = np.maximum(max_axis, np.abs(delta).max(axis=0))

        layer.mesh.vertices = o3d.utility.Vector3dVector(after_vertices)
        layer.mesh.compute_vertex_normals()
        _refresh_layer_metadata_from_mesh(layer)

        layer.deformation_history.append({
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'parameters': parameters,
            'vertices_processed': int(len(before_vertices)),
            'vertices_affected': int(np.count_nonzero(lengths > 1e-9)),
            'max_displacement': float(lengths.max()) if len(lengths) else 0.0,
        })

    if metadata_updater is not None:
        metadata_updater(billet, before_frame)
    else:
        refresh_billet_metadata_from_geometry(billet)

    after_frame = compute_billet_frame(billet)
    after_volume = _frame_volume(after_frame)
    all_lengths = np.concatenate(displacement_lengths) if displacement_lengths else np.array([], dtype=np.float64)
    elapsed = (datetime.now() - start_time).total_seconds()

    stats = DisplacementStats(
        operation=operation,
        vertices_processed=int(vertices_processed),
        affected_vertices=int(affected_vertices),
        max_displacement=float(all_lengths.max()) if len(all_lengths) else 0.0,
        mean_displacement=float(all_lengths.mean()) if len(all_lengths) else 0.0,
        max_axis_displacement=(float(max_axis[0]), float(max_axis[1]), float(max_axis[2])),
        before_span=_frame_span_tuple(before_frame),
        after_span=_frame_span_tuple(after_frame),
        volume_ratio=float(after_volume / before_volume) if before_volume > 1e-9 else 1.0,
    )

    if debug:
        logger.info(
            f"{operation}: processed={stats.vertices_processed}, affected={stats.affected_vertices}, "
            f"max_disp={stats.max_displacement:.4f}, mean_disp={stats.mean_displacement:.4f}, "
            f"volume_ratio={stats.volume_ratio:.4f}, elapsed={elapsed:.2f}s"
        )

    billet.operation_history.append({
        'operation': operation,
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': elapsed,
        'parameters': parameters,
        'displacement_stats': asdict(stats),
    })

    return stats


def octagon_width_at_z_array(z: np.ndarray, hw: float, hh: float, c: float) -> np.ndarray:
    """Vectorized octagon envelope half-width at height z."""
    z = np.asarray(z, dtype=np.float64)
    az = np.abs(z)
    z_transition = (1.0 - c) * hh
    widths = np.where(
        az <= z_transition,
        hw,
        hw * ((2.0 - c) - az / hh),
    )
    return np.clip(widths, 0.0, hw)


def apply_octagon_corner_flow(
    vertices: np.ndarray,
    *,
    hw: float,
    hh: float,
    c: float,
    strength: float = DEFAULT_OCTAGON_FLOW_STRENGTH,
    center_bulge: float = DEFAULT_OCTAGON_CENTER_BULGE,
    boundary_eps: float = 1e-7,
) -> np.ndarray:
    """
    Displace internal layer surfaces for square-to-octagon forging.

    The final octagon envelope is preserved.  Internal material is pulled
    toward the center only in the side/corner contact zones.  The central
    span of each layer is deliberately left flat so the result does not form
    a centerline chevron.
    """
    displaced = np.asarray(vertices, dtype=np.float64).copy()
    if len(displaced) == 0:
        return displaced

    x = displaced[:, 0]
    z = displaced[:, 2]

    original_width = octagon_width_at_z_array(z, hw, hh, c)
    on_outer_skin = np.abs(np.abs(x) - original_width) <= max(hw, hh) * boundary_eps
    on_global_top_bottom = np.abs(np.abs(z) - hh) <= max(hw, hh) * boundary_eps

    side_t = np.clip(np.abs(x) / max(hw, 1e-9), 0.0, 1.0)
    z_abs_t = np.clip(np.abs(z) / max(hh, 1e-9), 0.0, 1.0)
    z_sign = np.sign(z)
    # The flat middle of a forged octagon should remain flat.  Start material
    # flow at the same normalized X position where the octagon's flat side
    # transitions into its chamfer; this makes 5% chamfer deform only a tiny
    # edge band, while a regular-octagon chamfer deforms the outer side zones.
    flow_start = float(np.clip(1.0 - c, 0.0, 0.98))
    flow_width = max(1.0 - flow_start, 1e-9)
    side_zone_t = np.clip((side_t - flow_start) / flow_width, 0.0, 1.0)
    side_contact = side_zone_t * side_zone_t * (3.0 - 2.0 * side_zone_t)

    # Corner/side contact compresses layer heights toward the billet center.
    # Since side_contact is zero in the central band, the middle of every
    # layer stays horizontal rather than bending into a V at x=0.
    press_fade = np.sqrt(np.clip(1.0 - z_abs_t, 0.0, 1.0))
    inward_press = np.clip(strength, 0.0, 0.95) * side_contact * press_fade
    z_abs_new = z_abs_t * (1.0 - inward_press)
    z_abs_new = np.clip(z_abs_new, 0.0, 1.0)
    z_new = z_sign * hh * z_abs_new

    # The tooling fixes the global top and bottom flat faces.
    z_new[on_global_top_bottom] = z[on_global_top_bottom]

    max_x_new = octagon_width_at_z_array(z_new, hw, hh, c)
    x_new = x.copy()
    x_sign = np.sign(x_new)

    # Boundary vertices stay on the octagon skin; internal vertices are only
    # clipped if the z displacement would place them outside the envelope.
    needs_envelope_projection = on_outer_skin | (np.abs(x_new) > max_x_new)
    x_new[needs_envelope_projection] = x_sign[needs_envelope_projection] * max_x_new[needs_envelope_projection]

    displaced[:, 0] = x_new
    displaced[:, 2] = z_new
    return displaced


def count_degenerate_triangles(vertices: np.ndarray, triangles: np.ndarray, tolerance: float = 1e-9) -> int:
    """Return the number of triangles whose area is effectively zero."""
    if len(triangles) == 0:
        return 0
    a = vertices[triangles[:, 1]] - vertices[triangles[:, 0]]
    b = vertices[triangles[:, 2]] - vertices[triangles[:, 0]]
    area2 = np.linalg.norm(np.cross(a, b), axis=1)
    return int(np.count_nonzero(area2 < tolerance))
