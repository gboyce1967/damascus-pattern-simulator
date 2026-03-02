import numpy as np
import open3d as o3d
from PIL import Image
import io

def apply_wedge_safe(billet, wedge_depth: float, wedge_angle: float, split_gap: float):
    billet.apply_wedge_deformation(wedge_depth=wedge_depth, wedge_angle=wedge_angle, split_gap=split_gap, debug=False)

def forge_to_square_safe(billet, target_bar_size: float, num_heats: int):
    # Ported from your Tk GUI forging logic (volume conservation approach) but headless. :contentReference[oaicite:3]{index=3}
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
        "operation": "forge_square",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "parameters": {"target_bar_size": target_bar_size, "num_heats": num_heats, "final_length": final_length}
    })

def apply_twist_safe(billet, angle_degrees: float):
    # Your simulator only rotates when axis == 'y', so we lock to that (length-axis twist). :contentReference[oaicite:4]{index=4}
    billet.apply_twist(angle_degrees=float(angle_degrees), axis='y', debug=False)

def cross_section_png_safe(billet, y_slice: float, resolution: int) -> bytes:
    # Your simulator's extract_cross_section parameter is named z_slice but it slices on Y coords (length).
    # So we pass y_slice into z_slice to match current implementation. :contentReference[oaicite:5]{index=5}
    img_array = billet.extract_cross_section(z_slice=float(y_slice), resolution=int(resolution), debug=False)
    img = Image.fromarray(img_array)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
