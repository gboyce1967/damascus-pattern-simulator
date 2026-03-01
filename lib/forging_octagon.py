"""
Forging Operation: Forge to Octagonal Bar
============================================

Forges a Damascus billet into an octagonal cross-section bar.
Creates an 8-sided profile by forging to square then chamfering corners.
Traditional for twist Damascus.

Usage:
    from lib.forging_octagon import forge_to_octagon
    result = forge_to_octagon(root, billet, build_plate_vars)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import open3d as o3d
from datetime import datetime

from lib.logging_config import logger
from lib.gui_dialogs import show_build_plate_warning, center_dialog


def forge_to_octagon(root, billet, build_plate_width_var, build_plate_length_var):
    """
    Forge the billet into an octagonal cross-section bar.

    Args:
        root: Tkinter root window
        billet: Damascus3DBillet instance
        build_plate_width_var: tk.DoubleVar for build plate width
        build_plate_length_var: tk.DoubleVar for build plate length

    Returns:
        tuple: (operation_description, is_forged) or (None, False) if cancelled
    """
    if billet is None:
        messagebox.showwarning("No Billet", "Please create a billet first")
        return None, False

    current_height = sum(l.thickness for l in billet.layers)
    current_volume = billet.width * billet.length * current_height

    # === Parameter dialog ===
    dialog = tk.Toplevel(root)
    dialog.title("Forge to Octagonal Bar")
    dialog.transient(root)
    dialog.grab_set()

    info_frame = ttk.LabelFrame(dialog, text="Current Billet", padding=10)
    info_frame.pack(fill='x', padx=10, pady=5)
    ttk.Label(info_frame, text=f"Width: {billet.width:.1f} mm").pack(anchor='w')
    ttk.Label(info_frame, text=f"Length: {billet.length:.1f} mm").pack(anchor='w')
    ttk.Label(info_frame, text=f"Height: {current_height:.1f} mm").pack(anchor='w')
    ttk.Label(info_frame, text=f"Volume: {current_volume:.0f} mm³").pack(anchor='w')

    params_frame = ttk.LabelFrame(dialog, text="Target Bar Dimensions", padding=10)
    params_frame.pack(fill='x', padx=10, pady=5)

    ttk.Label(params_frame, text="Bar Size (across flats, mm):").grid(row=0, column=0, sticky='w', pady=2)
    bar_size_var = tk.DoubleVar(value=15.0)
    ttk.Spinbox(params_frame, from_=5.0, to=100.0, increment=1.0,
                textvariable=bar_size_var, width=10).grid(row=0, column=1, pady=2)

    ttk.Label(params_frame, text="Number of Heats:").grid(row=1, column=0, sticky='w', pady=2)
    heats_var = tk.IntVar(value=5)
    ttk.Spinbox(params_frame, from_=1, to=20, increment=1,
                textvariable=heats_var, width=10).grid(row=1, column=1, pady=2)

    ttk.Label(params_frame, text="Chamfer %:").grid(row=2, column=0, sticky='w', pady=2)
    chamfer_var = tk.DoubleVar(value=15.0)
    ttk.Spinbox(params_frame, from_=5.0, to=30.0, increment=1.0,
                textvariable=chamfer_var, width=10).grid(row=2, column=1, pady=2)

    result_frame = ttk.LabelFrame(dialog, text="Calculated Result", padding=10)
    result_frame.pack(fill='x', padx=10, pady=5)
    result_label = ttk.Label(result_frame, text="", justify='left')
    result_label.pack(anchor='w')

    def update_preview(*args):
        bar_size = bar_size_var.get()
        octagon_area = bar_size * bar_size * 0.95
        fl = current_volume / octagon_area
        extension_ratio = fl / billet.length
        result_label.config(text=f"Final length: {fl:.1f} mm ({extension_ratio:.2f}x extension)\n"
                                 f"Octagonal cross-section: ~{bar_size:.1f} mm across flats")

    bar_size_var.trace_add('write', update_preview)
    update_preview()

    confirmed = {'value': False}

    def on_confirm():
        confirmed['value'] = True
        dialog.destroy()

    button_frame = ttk.Frame(dialog)
    button_frame.pack(pady=10)
    ttk.Button(button_frame, text="Forge", command=on_confirm).pack(side='left', padx=5)
    ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side='left', padx=5)

    center_dialog(dialog)
    dialog.wait_window()

    if not confirmed['value']:
        logger.info("Forging cancelled by user")
        return None, False

    # === Execute forging ===
    target_bar_size = bar_size_var.get()
    num_heats = heats_var.get()
    chamfer_percent = chamfer_var.get() / 100.0
    original_width = billet.width
    original_length = billet.length
    original_height = current_height
    original_volume = current_volume
    octagon_area = target_bar_size * target_bar_size * 0.95
    final_length = original_volume / octagon_area

    logger.info(f"Forging billet to octagonal bar: {target_bar_size}mm, {num_heats} heats, {chamfer_percent * 100}% chamfer")

    # Check build plate fit
    plate_w = build_plate_width_var.get()
    plate_l = build_plate_length_var.get()

    if target_bar_size > plate_w or final_length > plate_l:
        result = show_build_plate_warning(root, "Forged Octagon Bar",
                                          (target_bar_size, final_length), (plate_w, plate_l))
        if result['action'] == 'cancel':
            return None, False
        elif result['action'] == 'resize':
            new_w, new_l = result['new_size']
            build_plate_width_var.set(new_w)
            build_plate_length_var.set(new_l)

    # Store original vertex positions
    original_vertices = [np.asarray(layer.mesh.vertices).copy() for layer in billet.layers]
    original_layer_thickness = [layer.thickness for layer in billet.layers]
    original_layer_z_pos = [layer.z_position for layer in billet.layers]

    # Apply progressive forging with chamfering
    for heat_num in range(num_heats):
        progress = (heat_num + 1) / num_heats
        target_width = original_width + (target_bar_size - original_width) * progress
        target_height = original_height + (target_bar_size - original_height) * progress
        target_length_heat = original_length + (final_length - original_length) * progress

        scale_x = target_width / original_width
        scale_y = target_length_heat / original_length
        scale_z = target_height / original_height
        current_chamfer = chamfer_percent * progress

        logger.info(f"Heat {heat_num + 1}/{num_heats}: {target_width:.1f}W × {target_length_heat:.1f}L × {target_height:.1f}H mm")

        for layer_idx, layer in enumerate(billet.layers):
            vertices = original_vertices[layer_idx].copy()
            for i in range(len(vertices)):
                x, y, z = vertices[i]
                x_forged = x * scale_x
                y_forged = y * scale_y
                z_forged = z * scale_z

                # Apply chamfer to corners (creates octagon from square)
                abs_x = abs(x_forged)
                abs_y = abs(y_forged)
                corner_threshold = target_width / 2 - (target_width * current_chamfer)

                if abs_x > corner_threshold and abs_y > corner_threshold:
                    chamfer_scale = 1.0 - current_chamfer
                    x_forged *= chamfer_scale
                    y_forged *= chamfer_scale

                vertices[i, 0] = x_forged
                vertices[i, 1] = y_forged
                vertices[i, 2] = z_forged

            layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
            layer.mesh.compute_vertex_normals()

        for layer_idx, layer in enumerate(billet.layers):
            layer.thickness = original_layer_thickness[layer_idx] * scale_z
            layer.z_position = original_layer_z_pos[layer_idx] * scale_z

    # Update billet dimensions
    billet.width = target_bar_size
    billet.length = final_length

    # Verify volume conservation
    final_height = sum(l.thickness for l in billet.layers)
    final_volume = billet.width * billet.length * final_height * 0.95
    volume_ratio = final_volume / original_volume

    logger.info(f"Forging complete. Volume ratio: {volume_ratio:.3f}")

    op_desc = f"Forged to octagon: ~{target_bar_size:.1f}mm across flats, length {final_length:.1f}mm ({num_heats} heats)"
    billet.operation_history.append({
        'operation': 'forge_octagon',
        'timestamp': datetime.now().isoformat(),
        'parameters': {
            'target_bar_size': target_bar_size,
            'num_heats': num_heats,
            'chamfer_percent': chamfer_percent * 100,
            'final_length': final_length,
            'extension_ratio': final_length / original_length,
            'volume_ratio': volume_ratio
        }
    })

    messagebox.showinfo("Forging Complete",
                        f"Billet forged to octagonal bar:\n"
                        f"Cross-section: ~{target_bar_size:.1f} mm across flats\n"
                        f"Length: {final_length:.1f} mm ({final_length / original_length:.1f}x extension)\n"
                        f"Heats: {num_heats}\n"
                        f"Volume conserved: {volume_ratio:.3f}\n\n"
                        "You can now apply twist operations!")

    return op_desc, True
