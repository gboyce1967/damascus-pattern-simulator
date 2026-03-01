"""
Forging Operation: Wedge Deformation (Feather Damascus)
========================================================

Applies wedge deformation to a Damascus billet to simulate feather Damascus.

PHYSICS SIMULATION:
------------------
Real-world process:
  1. Wedge is driven into center of billet from top
  2. Billet splits into two halves
  3. Material flows downward and outward (waterfall effect)
  4. Top layers displace more than bottom layers
  5. Wedge angle creates non-parallel edges

Usage:
    from lib.forging_wedge import apply_wedge_deformation
    apply_wedge_deformation(billet, wedge_depth=18.0)
"""

import numpy as np
import open3d as o3d
from datetime import datetime

from lib.logging_config import logger


def apply_wedge_deformation(billet, wedge_depth: float = 20.0, wedge_angle: float = 30.0,
                            split_gap: float = 5.0, debug: bool = True):
    """
    Apply wedge deformation to simulate feather Damascus.

    Args:
        billet: Damascus3DBillet instance to deform
        wedge_depth: How deep the wedge penetrates (mm)
        wedge_angle: Angle of wedge in degrees (from vertical)
        split_gap: Gap created at the split point (mm)
        debug: Enable detailed debug logging
    """
    logger.info("=" * 70)
    logger.info("WEDGE DEFORMATION OPERATION")
    logger.info(f"Parameters: depth={wedge_depth}mm, angle={wedge_angle}°, gap={split_gap}mm")
    logger.info("=" * 70)

    start_time = datetime.now()

    print(f"\nApplying wedge deformation:")
    print(f"  Depth: {wedge_depth}mm")
    print(f"  Angle: {wedge_angle}°")
    print(f"  Split gap: {split_gap}mm")
    print("This applies REAL 3D physics - each layer deforms based on its position!")

    center_x = 0.0
    wedge_angle_rad = np.deg2rad(wedge_angle)
    total_height = sum(l.thickness for l in billet.layers)

    logger.debug(f"Wedge center X: {center_x}")
    logger.debug(f"Wedge angle (radians): {wedge_angle_rad:.4f}")
    logger.debug(f"Total billet height: {total_height:.2f}mm")

    # Statistics tracking
    total_vertices_processed = 0
    displacement_stats = {
        'max_vertical': 0.0,
        'max_horizontal': 0.0,
        'mean_vertical': [],
        'mean_horizontal': []
    }

    for layer_idx, layer in enumerate(billet.layers):
        logger.debug(f"Processing layer #{layer_idx}/{len(billet.layers)}")

        vertices = np.asarray(layer.mesh.vertices).copy()
        original_vertices = vertices.copy()

        layer_position_normalized = layer.z_position / total_height

        logger.debug(f"  Layer position (normalized): {layer_position_normalized:.3f}")
        logger.debug(f"  Vertex count: {len(vertices)}")

        vertical_displacements = []
        horizontal_displacements = []

        for i, vertex in enumerate(vertices):
            x, y, z = vertex

            dist_from_center = abs(x - center_x)
            side = np.sign(x - center_x) if abs(x - center_x) > 0.001 else 1.0

            sigma = billet.width / 3.0
            intensity = np.exp(-(dist_from_center ** 2) / (2 * sigma ** 2))

            downward_displacement = -wedge_depth * intensity * layer_position_normalized
            horizontal_displacement = side * split_gap * intensity * layer_position_normalized
            horizontal_displacement += side * wedge_depth * np.tan(wedge_angle_rad) * intensity * layer_position_normalized

            vertices[i, 0] += horizontal_displacement
            vertices[i, 2] += downward_displacement

            vertical_displacements.append(abs(downward_displacement))
            horizontal_displacements.append(abs(horizontal_displacement))

            if debug and i % 10 == 0:
                logger.debug(f"    Vertex {i}: ({x:.2f}, {y:.2f}, {z:.2f}) -> "
                             f"({vertices[i, 0]:.2f}, {vertices[i, 1]:.2f}, {vertices[i, 2]:.2f}) | "
                             f"Δx={horizontal_displacement:.2f}, Δz={downward_displacement:.2f}")

        layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
        layer.mesh.compute_vertex_normals()

        deformation_record = {
            'operation': 'wedge',
            'timestamp': datetime.now().isoformat(),
            'parameters': {
                'wedge_depth': wedge_depth,
                'wedge_angle': wedge_angle,
                'split_gap': split_gap
            },
            'displacement_stats': {
                'vertical_max': max(vertical_displacements),
                'vertical_mean': np.mean(vertical_displacements),
                'horizontal_max': max(horizontal_displacements),
                'horizontal_mean': np.mean(horizontal_displacements)
            }
        }
        layer.deformation_history.append(deformation_record)

        displacement_stats['max_vertical'] = max(displacement_stats['max_vertical'], max(vertical_displacements))
        displacement_stats['max_horizontal'] = max(displacement_stats['max_horizontal'], max(horizontal_displacements))
        displacement_stats['mean_vertical'].append(np.mean(vertical_displacements))
        displacement_stats['mean_horizontal'].append(np.mean(horizontal_displacements))

        total_vertices_processed += len(vertices)

        logger.debug(f"  Layer #{layer_idx} deformation complete:")
        logger.debug(f"    Vertical: max={max(vertical_displacements):.2f}mm, mean={np.mean(vertical_displacements):.2f}mm")
        logger.debug(f"    Horizontal: max={max(horizontal_displacements):.2f}mm, mean={np.mean(horizontal_displacements):.2f}mm")

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"Wedge deformation complete in {elapsed:.2f}s")
    logger.info(f"  Processed {total_vertices_processed} vertices across {len(billet.layers)} layers")
    logger.info(f"  Max vertical displacement: {displacement_stats['max_vertical']:.2f}mm")
    logger.info(f"  Max horizontal displacement: {displacement_stats['max_horizontal']:.2f}mm")

    billet.operation_history.append({
        'operation': 'wedge_deformation',
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': elapsed,
        'parameters': {
            'wedge_depth': wedge_depth,
            'wedge_angle': wedge_angle,
            'split_gap': split_gap
        },
        'stats': displacement_stats
    })

    print("Deformation complete!")
