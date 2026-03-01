"""
Forging Operation: Twist Deformation (Ladder/Twist Damascus)
=============================================================

Applies torsional twist to a Damascus billet for ladder/twist patterns.

Usage:
    from lib.forging_twist import apply_twist
    apply_twist(billet, angle_degrees=90.0, axis='y')
"""

import numpy as np
import open3d as o3d
from datetime import datetime

from lib.logging_config import logger


def apply_twist(billet, angle_degrees: float = 90.0, axis: str = 'z', debug: bool = True):
    """
    Apply torsional twist to the billet (for ladder/twist Damascus).

    Args:
        billet: Damascus3DBillet instance to deform
        angle_degrees: Total rotation angle in degrees
        axis: Axis to twist around ('y' for length axis)
        debug: Enable detailed debug logging
    """
    logger.info("=" * 70)
    logger.info("TWIST DEFORMATION OPERATION")
    logger.info(f"Parameters: angle={angle_degrees}°, axis={axis}")
    logger.info("=" * 70)

    start_time = datetime.now()

    print(f"\nApplying twist deformation: {angle_degrees}° around {axis}-axis")

    angle_rad = np.deg2rad(angle_degrees)
    logger.debug(f"Twist angle (radians): {angle_rad:.4f}")

    total_vertices_processed = 0

    for layer_idx, layer in enumerate(billet.layers):
        logger.debug(f"Twisting layer #{layer_idx}")

        vertices = np.asarray(layer.mesh.vertices).copy()

        for i, vertex in enumerate(vertices):
            x, y, z = vertex

            normalized_position = (y + billet.length / 2) / billet.length
            current_angle = angle_rad * normalized_position

            if debug and i == 0:
                logger.debug(f"  Y position: {y:.2f}mm, normalized: {normalized_position:.3f}, "
                             f"rotation: {np.rad2deg(current_angle):.2f}°")

            if axis == 'y':
                x_center = 0
                z_center = layer.z_position + layer.thickness / 2

                x_rel = x - x_center
                z_rel = z - z_center

                x_new = x_rel * np.cos(current_angle) - z_rel * np.sin(current_angle)
                z_new = x_rel * np.sin(current_angle) + z_rel * np.cos(current_angle)

                vertices[i, 0] = x_new + x_center
                vertices[i, 2] = z_new + z_center

        layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
        layer.mesh.compute_vertex_normals()

        layer.deformation_history.append({
            'operation': 'twist',
            'timestamp': datetime.now().isoformat(),
            'parameters': {'angle_degrees': angle_degrees, 'axis': axis}
        })

        total_vertices_processed += len(vertices)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Twist complete in {elapsed:.2f}s - processed {total_vertices_processed} vertices")

    billet.operation_history.append({
        'operation': 'twist',
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': elapsed,
        'parameters': {'angle_degrees': angle_degrees, 'axis': axis}
    })

    print("Twist complete!")
