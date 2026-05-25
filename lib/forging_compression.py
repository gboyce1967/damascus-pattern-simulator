"""
Forging Operation: Compression (Hammering/Pressing)
=====================================================

Compresses a Damascus billet vertically to simulate hammering or pressing.

Usage:
    from lib.forging_compression import apply_compression
    apply_compression(billet, compression_factor=0.8)
"""

import numpy as np

from lib.logging_config import logger
from lib.forging_displacement import apply_displacement_to_billet


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

    compression_factor = float(np.clip(compression_factor, 0.05, 10.0))

    print(f"\nApplying compression: {compression_factor:.1%} of original height")

    lateral_flow = float(np.sqrt(1.0 / compression_factor))

    def compression_field(vertices, layer, layer_idx, frame):
        displaced = vertices.copy()
        displaced[:, 0] = frame.center_x + (vertices[:, 0] - frame.center_x) * lateral_flow
        displaced[:, 1] = frame.center_y + (vertices[:, 1] - frame.center_y) * lateral_flow
        displaced[:, 2] = frame.center_z + (vertices[:, 2] - frame.center_z) * compression_factor
        return displaced

    stats = apply_displacement_to_billet(
        billet,
        'compression',
        compression_field,
        {
            'compression_factor': compression_factor,
            'lateral_flow_factor': lateral_flow,
        },
        extra_param=abs(1.0 - compression_factor) * 720.0,
        debug=debug,
    )

    print(
        f"Compression complete! Height: {stats.before_span[2]:.1f}mm → "
        f"{stats.after_span[2]:.1f}mm; width/length expanded by {lateral_flow:.3f}x."
    )
