"""
Forging Operation: Drilling (Raindrop Damascus)
=================================================

Drills holes through a Damascus billet to create raindrop patterns.

Usage:
    from lib.forging_drill import drill_hole
    drill_hole(billet, x_pos=0.0, z_pos=0.0, radius=10.0)
"""

import numpy as np
import open3d as o3d
from datetime import datetime

from lib.logging_config import logger


def drill_hole(billet, x_pos: float = 0.0, z_pos: float = 0.0,
               radius: float = 10.0, debug: bool = True):
    """
    Drill a hole through the billet.

    Args:
        billet: Damascus3DBillet instance to deform
        x_pos: X position of hole center (mm)
        z_pos: Z position of hole center (mm)
        radius: Radius of the hole (mm)
        debug: Enable detailed debug logging
    """
    logger.info("=" * 70)
    logger.info("DRILLING OPERATION")
    logger.info(f"Parameters: position=({x_pos:.1f}, {z_pos:.1f}), radius={radius}mm")
    logger.info("=" * 70)

    start_time = datetime.now()

    print(f"\nDrilling hole at ({x_pos:.1f}, {z_pos:.1f}) with radius {radius:.1f}mm")

    total_vertices_affected = 0

    for layer_idx, layer in enumerate(billet.layers):
        logger.debug(f"Drilling through layer #{layer_idx}")

        vertices = np.asarray(layer.mesh.vertices).copy()
        vertices_affected_in_layer = 0

        for i, vertex in enumerate(vertices):
            x, y, z = vertex

            dx = x - x_pos
            dy = y - z_pos
            dist = np.sqrt(dx ** 2 + dy ** 2)

            if dist < radius * 2.0:
                vertices_affected_in_layer += 1

                if dist < radius:
                    push_factor = 1.5
                    logger.debug(f"  Vertex {i} INSIDE hole: dist={dist:.2f}mm, push={push_factor}")
                else:
                    influence = np.exp(-((dist - radius) ** 2) / (2 * radius ** 2))
                    push_factor = influence * 0.3

                if dist > 0.001:
                    direction_x = dx / dist
                    direction_y = dy / dist

                    displacement_x = direction_x * radius * push_factor
                    displacement_y = direction_y * radius * push_factor

                    vertices[i, 0] += displacement_x
                    vertices[i, 1] += displacement_y

        logger.debug(f"  Layer #{layer_idx}: {vertices_affected_in_layer} vertices affected")
        total_vertices_affected += vertices_affected_in_layer

        layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
        layer.mesh.compute_vertex_normals()

        layer.deformation_history.append({
            'operation': 'drill',
            'timestamp': datetime.now().isoformat(),
            'parameters': {'x_pos': x_pos, 'z_pos': z_pos, 'radius': radius},
            'vertices_affected': vertices_affected_in_layer
        })

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Drilling complete in {elapsed:.2f}s")
    logger.info(f"  Total vertices affected: {total_vertices_affected}")

    billet.operation_history.append({
        'operation': 'drill_hole',
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': elapsed,
        'parameters': {'x_pos': x_pos, 'z_pos': z_pos, 'radius': radius},
        'vertices_affected': total_vertices_affected
    })

    print("Drilling complete!")
