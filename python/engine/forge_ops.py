"""
Headless Forging Operations for the FastAPI Backend
====================================================

Thin wrappers around the modularized lib/ forging modules.
Each *_safe function is a headless (no GUI) entry point suitable
for the Electron/FastAPI backend.

All physics and mesh manipulation lives in the lib/forging_*.py modules.
"""

import io
from PIL import Image

from lib.forging_wedge import apply_wedge_deformation
from lib.forging_twist import apply_twist
from lib.forging_compression import apply_compression
from lib.forging_drill import drill_hole


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

    This is a headless version of the GUI forge_to_square dialog.
    The physics is identical to lib/forging_square.py but without
    the Tkinter dialog (no root window needed).
    """
    import numpy as np
    import open3d as o3d
    from datetime import datetime

    current_height = sum(l.thickness for l in billet.layers)
    original_volume = billet.width * billet.length * current_height
    original_width = float(billet.width)
    original_length = float(billet.length)
    original_height = float(current_height)
    final_length = original_volume / (target_bar_size * target_bar_size)

    original_vertices = [np.asarray(layer.mesh.vertices).copy() for layer in billet.layers]
    orig_th = [layer.thickness for layer in billet.layers]
    orig_z = [layer.z_position for layer in billet.layers]

    for heat_num in range(max(1, num_heats)):
        progress = (heat_num + 1) / max(1, num_heats)
        target_width = original_width + (target_bar_size - original_width) * progress
        target_height = original_height + (target_bar_size - original_height) * progress
        target_len = original_length + (final_length - original_length) * progress

        scale_x = target_width / original_width
        scale_y = target_len / original_length
        scale_z = target_height / original_height

        for layer_idx, layer in enumerate(billet.layers):
            v = original_vertices[layer_idx].copy()
            v[:, 0] *= scale_x
            v[:, 1] *= scale_y
            v[:, 2] *= scale_z
            layer.mesh.vertices = o3d.utility.Vector3dVector(v)
            layer.mesh.compute_vertex_normals()

        for layer_idx, layer in enumerate(billet.layers):
            layer.thickness = orig_th[layer_idx] * scale_z
            layer.z_position = orig_z[layer_idx] * scale_z

    billet.width = float(target_bar_size)
    billet.length = float(final_length)

    billet.operation_history.append({
        'operation': 'forge_square',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'target_bar_size': target_bar_size,
            'num_heats': num_heats,
            'final_length': final_length
        }
    })


def forge_to_octagon_safe(billet, target_bar_size: float, num_heats: int, chamfer_percent: float = 15.0):
    """
    Headless forge-to-octagon operation (volume conservation + corner chamfering).

    Physics extracted from lib/forging_octagon.py without Tkinter dialogs.
    Creates an octagonal cross-section by forging to square then chamfering corners.
    """
    import numpy as np
    import open3d as o3d
    from datetime import datetime

    chamfer_frac = chamfer_percent / 100.0
    current_height = sum(l.thickness for l in billet.layers)
    original_volume = billet.width * billet.length * current_height
    original_width = float(billet.width)
    original_length = float(billet.length)
    original_height = float(current_height)
    octagon_area = target_bar_size * target_bar_size * 0.95
    final_length = original_volume / octagon_area

    original_vertices = [np.asarray(layer.mesh.vertices).copy() for layer in billet.layers]
    orig_th = [layer.thickness for layer in billet.layers]
    orig_z = [layer.z_position for layer in billet.layers]

    for heat_num in range(max(1, num_heats)):
        progress = (heat_num + 1) / max(1, num_heats)
        target_width = original_width + (target_bar_size - original_width) * progress
        target_height = original_height + (target_bar_size - original_height) * progress
        target_len = original_length + (final_length - original_length) * progress

        scale_x = target_width / original_width
        scale_y = target_len / original_length
        scale_z = target_height / original_height
        current_chamfer = chamfer_frac * progress

        for layer_idx, layer in enumerate(billet.layers):
            v = original_vertices[layer_idx].copy()
            for i in range(len(v)):
                x_f = v[i, 0] * scale_x
                y_f = v[i, 1] * scale_y
                z_f = v[i, 2] * scale_z

                # Chamfer corners to create octagonal profile
                corner_threshold = target_width / 2 - (target_width * current_chamfer)
                if abs(x_f) > corner_threshold and abs(y_f) > corner_threshold:
                    chamfer_scale = 1.0 - current_chamfer
                    x_f *= chamfer_scale
                    y_f *= chamfer_scale

                v[i, 0] = x_f
                v[i, 1] = y_f
                v[i, 2] = z_f

            layer.mesh.vertices = o3d.utility.Vector3dVector(v)
            layer.mesh.compute_vertex_normals()

        for layer_idx, layer in enumerate(billet.layers):
            layer.thickness = orig_th[layer_idx] * scale_z
            layer.z_position = orig_z[layer_idx] * scale_z

    billet.width = float(target_bar_size)
    billet.length = float(final_length)

    billet.operation_history.append({
        'operation': 'forge_octagon',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'target_bar_size': target_bar_size,
            'num_heats': num_heats,
            'chamfer_percent': chamfer_percent,
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
