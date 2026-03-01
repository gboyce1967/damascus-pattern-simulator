"""
Forging Operation: Compression (Hammering/Pressing)
=====================================================

Compresses a Damascus billet vertically to simulate hammering or pressing.

Usage:
    from lib.forging_compression import apply_compression
    apply_compression(billet, compression_factor=0.8)
"""

import numpy as np
import open3d as o3d
from datetime import datetime

from lib.logging_config import logger


def apply_compression(billet, compression_factor: float = 0.8, debug: bool = True):
    """
    Compress the billet vertically (simulates hammering/pressing).

    Args:
        billet: Damascus3DBillet instance to deform
        compression_factor: Multiply height by this factor (< 1.0 compresses)
        debug: Enable detailed debug logging
    """
    logger.info("=" * 70)
    logger.info("COMPRESSION OPERATION")
    logger.info(f"Parameters: factor={compression_factor} ({compression_factor * 100:.1f}%)")
    logger.info("=" * 70)

    start_time = datetime.now()

    total_height_before = sum(l.thickness for l in billet.layers)
    total_height_after = total_height_before * compression_factor

    print(f"\nApplying compression: {compression_factor:.1%} of original height")
    logger.debug(f"Height before: {total_height_before:.2f}mm")
    logger.debug(f"Height after: {total_height_after:.2f}mm")
    logger.debug(f"Reduction: {total_height_before - total_height_after:.2f}mm")

    for layer_idx, layer in enumerate(billet.layers):
        logger.debug(f"Compressing layer #{layer_idx}")

        vertices = np.asarray(layer.mesh.vertices).copy()

        original_y_min = vertices[:, 2].min()
        original_y_max = vertices[:, 2].max()

        # Compress in Z direction (height)
        for i, vertex in enumerate(vertices):
            x, y, z = vertex
            vertices[i, 2] = z * compression_factor

        # Update layer properties
        layer.thickness *= compression_factor
        layer.z_position *= compression_factor

        new_y_min = vertices[:, 2].min()
        new_y_max = vertices[:, 2].max()

        logger.debug(f"  Layer #{layer_idx} Z bounds: [{original_y_min:.2f}, {original_y_max:.2f}] -> "
                     f"[{new_y_min:.2f}, {new_y_max:.2f}]")

        layer.mesh.vertices = o3d.utility.Vector3dVector(vertices)
        layer.mesh.compute_vertex_normals()

        layer.deformation_history.append({
            'operation': 'compression',
            'timestamp': datetime.now().isoformat(),
            'parameters': {'compression_factor': compression_factor},
            'height_change': {
                'before': original_y_max - original_y_min,
                'after': new_y_max - new_y_min
            }
        })

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Compression complete in {elapsed:.2f}s")
    logger.info(f"  Height: {total_height_before:.1f}mm → {total_height_after:.1f}mm")

    billet.operation_history.append({
        'operation': 'compression',
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': elapsed,
        'parameters': {'compression_factor': compression_factor},
        'height_change': {
            'before_mm': total_height_before,
            'after_mm': total_height_after
        }
    })

    print(f"Compression complete! Height: {total_height_before:.1f}mm → {total_height_after:.1f}mm")
