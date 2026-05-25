"""
Octagonal Prism Mesh Builder
==============================

Builds a structured layer mesh whose outer walls match the global octagon
envelope.  Each layer is a horizontal slice through the billet, clipped by
the octagonal profile.

Three layer zone types:
  Zone 1 — Centre:     |z| ≤ (1-c)·hh → pure rectangle, full width
  Zone 2 — Chamfer:    |z| > (1-c)·hh → trapezoid, width tapers with Z
  Zone 3 — Transition: layer straddles the (1-c)·hh boundary → extra
                        Z-level inserted at exactly (1-c)·hh

Usage:
    from lib.forging_octagon_mesh import build_octagon_layer_mesh
"""

import numpy as np

from lib.logging_config import logger


def get_octagon_width_at_z(z: float, hw: float, hh: float, c: float) -> float:
    """
    Maximum |x| at height z for the global octagon envelope.

    Chamfer line:  x/hw + |z|/hh = 2 - c
    Solving:       x = hw · (2 - c - |z|/hh)   clamped to [0, hw]
    """
    az = abs(z)
    z_transition = (1.0 - c) * hh
    if az <= z_transition:
        return hw                                          # flat side-wall zone
    elif az <= hh:
        return max(0.0, hw * ((2.0 - c) - az / hh))       # chamfer taper
    return 0.0


def build_octagon_layer_mesh(
    hw: float, hh: float, c: float,
    z_bot: float, z_top: float,
    y_min: float, y_max: float,
    segments_y: int = 16,
    samples_x: int = 9,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Build vertices and triangles for one layer of an octagonal bar.

    All coordinates are centroid-relative (centre of billet = origin).
    The layer is a horizontal slice clipped by the global octagon profile.
    If the layer straddles a chamfer transition boundary, an extra Z-level
    is inserted so the side walls have a vertex at the exact flat↔chamfer
    transition.

    Uses an anchored internal X grid plus dynamic outer boundary vertices.
    The internal columns stay vertically aligned from layer to layer while
    only the two outside columns move inward in the chamfer zones. This keeps
    each layer flat and avoids side grooves caused by resampling the entire row
    across a changing width.
    """

    # --- Determine Z-levels for this layer ---
    z_trans_pos = (1.0 - c) * hh
    z_trans_neg = -z_trans_pos

    z_levels = [z_bot]
    if z_bot < z_trans_neg < z_top:
        z_levels.append(z_trans_neg)
    if z_bot < z_trans_pos < z_top:
        z_levels.append(z_trans_pos)
    z_levels.append(z_top)
    z_levels = sorted(set(round(z, 10) for z in z_levels))
    n_z = len(z_levels)

    # --- Y slices ---
    y_coords = np.linspace(y_min, y_max, max(2, segments_y))
    n_y = len(y_coords)

    # --- Build vertices ---
    # Layout per Y-slice: [z_level_0 row (samples_x pts), z_level_1 row, ...]
    internal_count = max(0, samples_x - 2)
    internal_limit = max(0.0, (1.0 - c) * hw)
    if internal_count:
        # Keep internal columns fixed for every row. Exclude the flat-face
        # endpoints so top/bottom rows do not duplicate their boundary vertices.
        internal_x = np.linspace(
            -internal_limit,
            internal_limit,
            internal_count + 2,
            dtype=np.float64,
        )[1:-1]
    else:
        internal_x = np.empty(0, dtype=np.float64)
    stride = n_z * samples_x
    total_verts = n_y * stride

    verts = np.empty((total_verts, 3), dtype=np.float64)
    idx = 0
    for y in y_coords:
        for z_val in z_levels:
            max_x = get_octagon_width_at_z(z_val, hw, hh, c)
            row = np.concatenate(([-max_x], internal_x, [max_x]))
            for x in row:
                verts[idx] = [x, y, z_val]
                idx += 1

    # --- Build triangles (hollow shell) ---
    tris = []

    for g in range(n_y - 1):
        base_cur = g * stride
        base_nxt = (g + 1) * stride

        # 1. Bottom face (horizontal)
        off_bot = 0
        for col in range(samples_x - 1):
            i0 = base_cur + off_bot + col
            i1 = base_cur + off_bot + col + 1
            i2 = base_nxt + off_bot + col
            i3 = base_nxt + off_bot + col + 1
            # Normal pointing downward (-Z)
            tris.append([i0, i3, i1])
            tris.append([i0, i2, i3])

        # 2. Top face (horizontal)
        off_top = (n_z - 1) * samples_x
        for col in range(samples_x - 1):
            i0 = base_cur + off_top + col
            i1 = base_cur + off_top + col + 1
            i2 = base_nxt + off_top + col
            i3 = base_nxt + off_top + col + 1
            # Normal pointing upward (+Z)
            tris.append([i0, i1, i3])
            tris.append([i0, i3, i2])

        # 3. Side walls (stitch adjacent Z-levels on left & right boundaries)
        for zi in range(n_z - 1):
            off_lo = zi * samples_x
            off_hi = (zi + 1) * samples_x

            # Left wall (col = 0)
            bl_c = base_cur + off_lo
            tl_c = base_cur + off_hi
            bl_n = base_nxt + off_lo
            tl_n = base_nxt + off_hi
            # Normal pointing left (-X)
            tris.append([bl_c, tl_n, tl_c])
            tris.append([bl_c, bl_n, tl_n])

            # Right wall (col = samples_x - 1)
            br_c = base_cur + off_lo + samples_x - 1
            tr_c = base_cur + off_hi + samples_x - 1
            br_n = base_nxt + off_lo + samples_x - 1
            tr_n = base_nxt + off_hi + samples_x - 1
            # Normal pointing right (+X)
            tris.append([br_c, tr_c, tr_n])
            tris.append([br_c, tr_n, br_n])

    # 4. End caps (front at y_min, back at y_max)
    for g_cap in [0, n_y - 1]:
        base = g_cap * stride
        for zi in range(n_z - 1):
            off_lo = zi * samples_x
            off_hi = (zi + 1) * samples_x
            for col in range(samples_x - 1):
                b0 = base + off_lo + col
                b1 = base + off_lo + col + 1
                t0 = base + off_hi + col
                t1 = base + off_hi + col + 1
                if g_cap == 0:
                    # Front cap (normal pointing toward -Y)
                    tris.append([b0, t0, t1])
                    tris.append([b0, t1, b1])
                else:
                    # Back cap (normal pointing toward +Y)
                    tris.append([b0, b1, t1])
                    tris.append([b0, t1, t0])

    triangles = np.array(tris, dtype=np.int32)

    logger.debug(
        f"build_octagon_layer_mesh: {len(verts)} verts, {len(triangles)} tris "
        f"(n_x={samples_x}, n_z={n_z}, n_y={n_y}, "
        f"z_levels={[f'{z:.2f}' for z in z_levels]})"
    )

    return verts, triangles
