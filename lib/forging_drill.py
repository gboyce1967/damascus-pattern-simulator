"""
Forging Operation: Drilling (Raindrop Damascus)
=================================================

Drills holes through a Damascus billet to create raindrop patterns.

The drill goes along the Y axis (length), so the hole cross-section lives
in the X-Z plane. Vertices inside the hole radius are pushed radially
outward in X-Z; vertices in the influence zone receive a Gaussian falloff.

Usage:
    from lib.forging_drill import drill_hole
    drill_hole(billet, x_pos=0.0, z_pos=0.0, radius=10.0)
"""

import numpy as np

from lib.forging_displacement import apply_displacement_to_billet
from lib.logging_config import logger


def drill_hole(billet, x_pos: float = 0.0, z_pos: float = 0.0,
               radius: float = 10.0, debug: bool = True):
    """
    Drill a hole through the billet.

    The hole axis is the Y (length) direction. Displacement is applied
    radially in the X-Z cross-section plane.

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

    print(f"\nDrilling hole at ({x_pos:.1f}, {z_pos:.1f}) with radius {radius:.1f}mm")

    def drill_field(vertices, layer, layer_idx, frame):
        dx = vertices[:, 0] - x_pos
        dz = vertices[:, 2] - z_pos
        dist = np.sqrt(dx ** 2 + dz ** 2)

        mask = dist < radius * 2.0
        displaced = vertices.copy()

        if mask.any():
            d = dist[mask]
            vx = dx[mask]
            vz = dz[mask]

            push = np.where(
                d < radius,
                1.5,
                np.exp(-((d - radius) ** 2) / (2 * radius ** 2)) * 0.3
            )

            safe_dist = np.where(d > 0.001, d, 1.0)
            dir_x = np.where(d > 0.001, vx / safe_dist, 0.0)
            dir_z = np.where(d > 0.001, vz / safe_dist, 0.0)

            displaced[mask, 0] += dir_x * radius * push
            displaced[mask, 2] += dir_z * radius * push

        if debug:
            logger.debug(f"  Layer #{layer_idx}: {int(mask.sum())} vertices affected")

        return displaced

    stats = apply_displacement_to_billet(
        billet,
        'drill_hole',
        drill_field,
        {
            'x_pos': x_pos,
            'z_pos': z_pos,
            'radius': radius,
        },
        extra_param=radius * 30,
        debug=debug,
    )

    print(f"Drilling complete! {stats.affected_vertices} vertices affected.")