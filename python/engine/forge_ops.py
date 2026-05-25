"""
Headless Forging Operations for the FastAPI Backend
====================================================

Thin wrappers around the modularized lib/ forging modules.
Each *_safe function is a headless (no GUI) entry point suitable
for the Electron/FastAPI backend.

All physics and mesh manipulation lives in the lib/forging_*.py modules.
"""

import io
import numpy as np
import open3d as o3d
from datetime import datetime
from PIL import Image

from lib.forging_wedge import apply_wedge_deformation
from lib.forging_twist import apply_twist
from lib.forging_compression import apply_compression
from lib.forging_drill import drill_hole
from lib.forging_utils import compute_billet_frame
from lib.forging_displacement import (
    DEFAULT_OCTAGON_CENTER_BULGE,
    DEFAULT_OCTAGON_CHAMFER_PERCENT,
    DEFAULT_OCTAGON_FLOW_STRENGTH,
    apply_displacement_to_billet,
    apply_octagon_corner_flow,
)
from lib.logging_config import logger


def apply_wedge_safe(billet, wedge_depth: float, wedge_angle: float, split_gap: float):
    """Apply wedge deformation (feather Damascus). Delegates to lib/forging_wedge.py."""
    apply_wedge_deformation(billet, wedge_depth=wedge_depth, wedge_angle=wedge_angle,
                            split_gap=split_gap, debug=False)


def apply_twist_safe(billet, angle_degrees: float):
    """Apply twist (length-axis). Delegates to lib/forging_twist.py."""
    apply_twist(billet, angle_degrees=float(angle_degrees), axis='y', debug=False)


def apply_compression_safe(billet, compression_factor: float):
    """Apply compression (hammering/pressing). Delegates to lib/forging_compression.py."""
    apply_compression(billet, compression_factor=float(compression_factor), debug=False)


def drill_hole_safe(billet, x_pos: float, z_pos: float, radius: float):
    """Drill a hole (raindrop Damascus). Delegates to lib/forging_drill.py."""
    drill_hole(billet, x_pos=float(x_pos), z_pos=float(z_pos),
               radius=float(radius), debug=False)


def forge_to_square_safe(billet, target_bar_size: float, num_heats: int):
    """
    Headless forge-to-square operation (volume conservation).

    Scales the billet cross-section to target_bar_size × target_bar_size
    while extending the length to conserve volume.  Scaling is done
    relative to the billet centroid so it works on billets that have
    already been deformed.
    """
    frame = compute_billet_frame(billet)
    original_volume = frame.span_x * frame.span_y * frame.span_z
    final_length = original_volume / (target_bar_size * target_bar_size)

    def square_press_field(vertices, layer, layer_idx, current_frame):
        displaced = vertices.copy()
        sx = target_bar_size / current_frame.span_x if current_frame.span_x > 1e-9 else 1.0
        sy = final_length / current_frame.span_y if current_frame.span_y > 1e-9 else 1.0
        sz = target_bar_size / current_frame.span_z if current_frame.span_z > 1e-9 else 1.0

        displaced[:, 0] = current_frame.center_x + (vertices[:, 0] - current_frame.center_x) * sx
        displaced[:, 1] = current_frame.center_y + (vertices[:, 1] - current_frame.center_y) * sy
        displaced[:, 2] = current_frame.center_z + (vertices[:, 2] - current_frame.center_z) * sz
        return displaced

    def square_metadata(b, before_frame):
        b.width = float(target_bar_size)
        b.length = float(final_length)

    apply_displacement_to_billet(
        billet,
        'forge_square',
        square_press_field,
        {
            'target_bar_size': target_bar_size,
            'num_heats': num_heats,
            'final_length': final_length,
        },
        extra_param=abs(target_bar_size - max(frame.span_x, frame.span_z)) * 30.0,
        metadata_updater=square_metadata,
        debug=False,
    )


def forge_to_octagon_safe(
    billet,
    target_bar_size: float,
    num_heats: int,
    chamfer_percent: float = DEFAULT_OCTAGON_CHAMFER_PERCENT,
    flow_strength: float = DEFAULT_OCTAGON_FLOW_STRENGTH,
    center_bulge: float = DEFAULT_OCTAGON_CENTER_BULGE,
):
    """
    Headless forge-to-octagon operation.

    Instead of subdividing a box and clipping corners, this builds each
    layer mesh from scratch as a structured octagonal prism with vertices
    at the exact chamfer transition coordinates. The die fixes the outside
    octagon envelope while a displacement field moves the internal material
    surfaces into the bowed pattern caused by 45-degree corner compression.
    """
    from lib.forging_octagon_mesh import build_octagon_layer_mesh

    frame = compute_billet_frame(billet)

    c = float(np.clip(chamfer_percent / 100.0, 0.01, 0.95))
    original_volume = frame.span_x * frame.span_y * frame.span_z
    # Octagon area for square side s with corner legs c·s/2:
    # A = s² − 4·(1/2·(c·s/2)²) = s²·(1 − c²/2)
    octagon_area = target_bar_size * target_bar_size * (1.0 - (c * c) / 2.0)
    final_length = original_volume / octagon_area

    hw = target_bar_size / 2.0
    hh = target_bar_size / 2.0   # square → octagon, so hw == hh

    logger.info(
        f"forge_to_octagon_safe: target={target_bar_size}mm, "
        f"heats={num_heats}, chamfer={c * 100.0:.1f}%, "
        f"final_length={final_length:.1f}mm"
    )

    # --- Rebuild every layer mesh as a structured octagonal prism ---
    # Scale layer Z positions to the target bar height
    total_height_old = frame.span_z
    sz = target_bar_size / total_height_old if total_height_old > 1e-9 else 1.0
    samples_x = 17

    for layer_idx, layer in enumerate(billet.layers):
        # Read actual Z bounds from the mesh vertices (not metadata,
        # which can be out of sync after prior operations).
        cur_verts = np.asarray(layer.mesh.vertices)
        actual_z_bot = float(cur_verts[:, 2].min())
        actual_z_top = float(cur_verts[:, 2].max())
        z_bot_rel = (actual_z_bot - frame.center_z) * sz
        z_top_rel = (actual_z_top - frame.center_z) * sz

        verts, tris = build_octagon_layer_mesh(
            hw=hw, hh=hh, c=c,
            z_bot=z_bot_rel, z_top=z_top_rel,
            y_min=frame.y_min, y_max=frame.y_min + final_length,
            segments_y=16,
            samples_x=samples_x,
        )
        verts = apply_octagon_corner_flow(
            verts,
            hw=hw,
            hh=hh,
            c=c,
            strength=float(flow_strength),
            center_bulge=float(center_bulge),
        )
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(verts)
        mesh.triangles = o3d.utility.Vector3iVector(tris)
        mesh.paint_uniform_color(layer.color)
        mesh.compute_vertex_normals()

        # --- Normal tuning: force chamfer-face normals to exact 45° ---
        # This helps exporters shade the chamfer as a single smooth plane
        # across independent layer meshes. The Electron renderer currently
        # recomputes normals, so geometry correctness is the main fix.
        z_trans_abs = (1.0 - c) * hh
        normals = np.asarray(mesh.vertex_normals)
        for vi, (vx, vy, vz) in enumerate(verts):
            col = vi % samples_x
            if (col == 0 or col == samples_x - 1) and abs(vz) > z_trans_abs + 1e-6:
                nx_dir = 0.7071 if vx > 0.0 else -0.7071
                nz_dir = 0.7071 if vz > 0.0 else -0.7071
                normals[vi] = [nx_dir, 0.0, nz_dir]
        mesh.vertex_normals = o3d.utility.Vector3dVector(normals)

        # Translate from centroid-relative to world coordinates
        verts[:, 0] += frame.center_x
        verts[:, 2] += frame.center_z
        # Y already set by build_octagon_layer_mesh (y_min..y_max)

        mesh.vertices = o3d.utility.Vector3dVector(verts)
        layer.width = float(target_bar_size)
        layer.length = float(final_length)
        layer.thickness = float(z_top_rel - z_bot_rel)
        layer.z_position = float(frame.center_z + z_bot_rel)
        layer.mesh = mesh
    billet.width = float(target_bar_size)
    billet.length = float(final_length)

    billet.operation_history.append({
        'operation': 'forge_octagon',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'target_bar_size': target_bar_size,
            'num_heats': num_heats,
            'chamfer_percent': c * 100.0,
            'flow_strength': float(flow_strength),
            'center_bulge': float(center_bulge),
            'final_length': final_length
        }
    })


def cross_section_png_safe(billet, y_slice: float, resolution: int) -> bytes:
    """
    Extract a cross-section and return PNG bytes.

    Note: The simulator's extract_cross_section z_slice parameter
    actually slices on Y coords (length axis).
    """
    img_array = billet.extract_cross_section(z_slice=float(y_slice),
                                             resolution=int(resolution), debug=False)
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()
