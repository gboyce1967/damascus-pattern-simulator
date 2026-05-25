"""
Forging Utilities — Shared Geometry Helpers
=============================================

Common routines used by every forging operation module:
  - Mesh subdivision (densify coarse box meshes before deformation)
  - Billet frame computation (actual bounds + centroid from live vertices)

Physics basis (from Research/material-deformation-math.md):
    Vertex displacement requires enough intermediate mesh points for the
    deformation field to produce visible, smooth results.  Open3D's initial
    box mesh has only 8 vertices, which is far too coarse for torsion,
    Gaussian wedge fields, or drill‐hole radial push.

Usage:
    from lib.forging_utils import subdivide_if_needed, compute_billet_frame
"""

import numpy as np
import open3d as o3d

from lib.logging_config import logger


# ---------------------------------------------------------------------------
# Mesh subdivision
# ---------------------------------------------------------------------------

_DEFAULT_MIN_VERTICES = 200


def subdivide_if_needed(billet, min_vertices: int = _DEFAULT_MIN_VERTICES,
                        base_iterations: int = 3, extra_param: float = 0.0):
    """
    Ensure every layer mesh has at least *min_vertices* vertices by applying
    Open3D midpoint subdivision.  Layers that are already dense enough are
    left untouched.

    Args:
        billet: Damascus3DBillet instance.
        min_vertices: Skip subdivision for layers already at or above this count.
        base_iterations: Minimum number of midpoint subdivision iterations.
        extra_param: An operation-magnitude value (e.g. twist degrees, wedge depth)
                     used to add 0-2 extra iterations for very large deformations.
    """
    extra_iterations = min(2, int(abs(extra_param) / 720)) if extra_param else 0
    iterations = base_iterations + extra_iterations

    for layer_idx, layer in enumerate(billet.layers):
        count_before = len(layer.mesh.vertices)
        if count_before >= min_vertices:
            logger.debug(
                f"subdivide_if_needed: layer #{layer_idx} already has "
                f"{count_before} vertices — skipping"
            )
            continue

        layer.mesh = layer.mesh.subdivide_midpoint(number_of_iterations=iterations)
        layer.mesh.paint_uniform_color(layer.color)
        layer.mesh.compute_vertex_normals()

        logger.debug(
            f"subdivide_if_needed: layer #{layer_idx}: "
            f"{count_before} → {len(layer.mesh.vertices)} vertices "
            f"({iterations} iterations)"
        )


# ---------------------------------------------------------------------------
# Billet frame (bounds + centroid) from live vertex data
# ---------------------------------------------------------------------------

class BilletFrame:
    """Lightweight container for actual billet geometry bounds."""
    __slots__ = (
        'x_min', 'x_max', 'y_min', 'y_max', 'z_min', 'z_max',
        'center_x', 'center_y', 'center_z',
        'span_x', 'span_y', 'span_z',
    )

    def __repr__(self):
        return (
            f"BilletFrame(center=({self.center_x:.3f}, {self.center_y:.3f}, "
            f"{self.center_z:.3f}), "
            f"span=({self.span_x:.3f}, {self.span_y:.3f}, {self.span_z:.3f}))"
        )


def compute_billet_frame(billet) -> BilletFrame:
    """
    Compute the axis-aligned bounding box and centroid of the billet from
    the actual vertex positions of every layer.  Works regardless of billet
    shape (square, octagonal, round, already deformed).

    Returns:
        BilletFrame with min/max/center/span for each axis.
    """
    if not billet.layers:
        raise ValueError("Cannot compute frame for a billet with no layers")

    all_verts = np.vstack(
        [np.asarray(layer.mesh.vertices) for layer in billet.layers]
    )

    f = BilletFrame()
    f.x_min = float(all_verts[:, 0].min())
    f.x_max = float(all_verts[:, 0].max())
    f.y_min = float(all_verts[:, 1].min())
    f.y_max = float(all_verts[:, 1].max())
    f.z_min = float(all_verts[:, 2].min())
    f.z_max = float(all_verts[:, 2].max())

    f.center_x = (f.x_min + f.x_max) / 2.0
    f.center_y = (f.y_min + f.y_max) / 2.0
    f.center_z = (f.z_min + f.z_max) / 2.0

    f.span_x = f.x_max - f.x_min
    f.span_y = f.y_max - f.y_min
    f.span_z = f.z_max - f.z_min

    logger.debug(f"compute_billet_frame: {f}")
    return f
