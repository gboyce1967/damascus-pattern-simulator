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

Physics basis (from Research/material-deformation-math.md):
  - Gaussian falloff: deformation = amplitude · e^(-distance²/width²)
  - Vertex displacement applied per-layer, intensity scaled by height position
  - Bounds and center computed from actual vertex data so the wedge
    hits the real centre of the billet regardless of prior deformations

Usage:
    from lib.forging_wedge import apply_wedge_deformation
    apply_wedge_deformation(billet, wedge_depth=18.0)
"""

import numpy as np

from lib.forging_displacement import apply_displacement_to_billet
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

    print(f"\nApplying wedge deformation:")
    print(f"  Depth: {wedge_depth}mm")
    print(f"  Angle: {wedge_angle}°")
    print(f"  Split gap: {split_gap}mm")

    wedge_angle_rad = np.deg2rad(wedge_angle)

    def wedge_field(vertices, layer, layer_idx, frame):
        sigma = frame.span_x / 3.0 if frame.span_x > 1e-9 else 1.0

        if frame.span_z > 1e-9:
            height_t = (vertices[:, 2] - frame.z_min) / frame.span_z
        else:
            height_t = np.ones(len(vertices), dtype=np.float64) * 0.5

        dx = vertices[:, 0] - frame.center_x
        dist = np.abs(dx)
        side = np.where(dx >= 0, 1.0, -1.0)
        intensity = np.exp(-(dist ** 2) / (2 * sigma ** 2))

        downward = -wedge_depth * intensity * height_t
        horizontal = side * (split_gap + wedge_depth * np.tan(wedge_angle_rad)) * intensity * height_t

        displaced = vertices.copy()
        displaced[:, 0] += horizontal
        displaced[:, 2] += downward

        if debug:
            logger.debug(
                f"  Layer #{layer_idx}: affected={int(np.count_nonzero(intensity > 1e-4))}, "
                f"max_down={float(np.abs(downward).max()) if len(downward) else 0.0:.3f}, "
                f"max_horizontal={float(np.abs(horizontal).max()) if len(horizontal) else 0.0:.3f}"
            )

        return displaced

    stats = apply_displacement_to_billet(
        billet,
        'wedge_deformation',
        wedge_field,
        {
            'wedge_depth': wedge_depth,
            'wedge_angle': wedge_angle,
            'split_gap': split_gap,
        },
        extra_param=wedge_depth * 20,
        debug=debug,
    )

    print(f"Wedge deformation complete! Processed {stats.vertices_processed} vertices.")