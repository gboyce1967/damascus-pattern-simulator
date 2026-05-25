"""
Forging Operation: Twist Deformation (Ladder/Twist Damascus)
=============================================================

Applies torsional twist to a Damascus billet for ladder/twist patterns.

Physics basis (from Research/material-deformation-math.md):
    - Vertex displacement moves mesh vertices by a mathematical deformation map
    - Progressive rotation along the length axis simulates torsion
    - Rotation center comes from actual billet geometry, not assumptions about
      whether the billet is square, octagonal, round, or already deformed
    - Mesh subdivision adds enough vertices for the deformation to be visible
    - Twisting shortens the billet along its length axis and pushes the
      cross-section toward a rounder bar as twist density increases

Usage:
    from lib.forging_twist import apply_twist
    apply_twist(billet, angle_degrees=90.0, axis='y')
"""

import numpy as np

from lib.forging_displacement import apply_displacement_to_billet
from lib.forging_utils import compute_billet_frame
from lib.logging_config import logger

MM_PER_INCH = 25.4
STANDARD_TWISTS_PER_INCH = (3.0, 4.0)
TURKISH_TWISTS_PER_INCH = (5.0, 10.0)
MAX_TWIST_AXIAL_SHORTENING = 0.75
MAX_TWIST_ROUNDNESS = 1.0
TWIST_ROUNDING_START_SHORTENING = 0.06
TWIST_ROUNDING_FULL_SHORTENING = 0.45


def classify_twist_density(twists_per_inch: float) -> str:
    """Classify a twist density against common Damascus twist guidelines."""
    if twists_per_inch < STANDARD_TWISTS_PER_INCH[0]:
        return "below_standard"
    if twists_per_inch <= STANDARD_TWISTS_PER_INCH[1]:
        return "standard"
    if twists_per_inch < TURKISH_TWISTS_PER_INCH[0]:
        return "between_standard_and_turkish"
    if twists_per_inch <= TURKISH_TWISTS_PER_INCH[1]:
        return "turkish"
    return "above_turkish_guideline"

def _smoothstep(value: float) -> float:
    """Return a smooth 0..1 interpolation curve for visual material flow."""
    clamped = float(np.clip(value, 0.0, 1.0))
    return clamped * clamped * (3.0 - 2.0 * clamped)


def twist_material_flow_factors(total_twists: float, twists_per_inch: float) -> tuple[float, float, float]:
    """
    Return axial scale, axial shortening ratio, and roundness factor.

    The values are visual/heuristic forging approximations, not finite-element
    simulation. Round-bar flow is derived from compression: more twists per
    inch shorten the billet, and the cross-section rounds as that compression
    reaches standard and Turkish twist densities.
    """
    twist_count = abs(float(total_twists))
    density = abs(float(twists_per_inch))
    axial_shortening = float(np.clip(
        0.225 * density + 0.020 * (1.0 - np.exp(-twist_count / 10.0)),
        0.0,
        MAX_TWIST_AXIAL_SHORTENING,
    ))
    compression_progress = (
        (axial_shortening - TWIST_ROUNDING_START_SHORTENING)
        / max(TWIST_ROUNDING_FULL_SHORTENING - TWIST_ROUNDING_START_SHORTENING, 1e-9)
    )
    roundness_factor = _smoothstep(compression_progress) * MAX_TWIST_ROUNDNESS
    return 1.0 - axial_shortening, axial_shortening, roundness_factor


def _material_layers_before_twist(billet) -> list[dict]:
    """Capture pre-twist material intervals for fused render-surface sampling."""
    material_layers: list[dict] = []
    for layer_idx, layer in enumerate(billet.layers):
        vertices = np.asarray(layer.mesh.vertices)
        if len(vertices) == 0:
            continue
        material_layers.append({
            'layer_index': int(getattr(layer, 'layer_index', layer_idx)),
            'z_min': float(vertices[:, 2].min()),
            'z_max': float(vertices[:, 2].max()),
            'color': [float(layer.color[0]), float(layer.color[1]), float(layer.color[2])],
        })
    return material_layers


def apply_twist(billet, angle_degrees: float = 90.0, axis: str = 'y', debug: bool = True):
    """
    Apply torsional twist to the billet (for ladder/twist Damascus).

    The current implementation supports twisting around the billet length
    axis (engine Y). The twist is calculated from actual mesh bounds so it
    remains valid after forging to square, octagon, round, or other deformed
    cross-sections.

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

    if axis.lower() != 'y':
        logger.warning(f"Twist axis '{axis}' requested, but only length-axis ('y') twist is supported")
        axis = 'y'

    print(f"\nApplying twist deformation: {angle_degrees}° around {axis}-axis")

    angle_rad = np.deg2rad(angle_degrees)
    logger.debug(f"Twist angle (radians): {angle_rad:.4f}")

    frame = compute_billet_frame(billet)
    if frame.span_y < 1e-9:
        logger.warning("Twist skipped because current billet length is effectively zero")
        print("Twist skipped: billet length is effectively zero.")
        return
    material_layers = _material_layers_before_twist(billet)

    total_twists = float(angle_degrees) / 360.0
    billet_length_inches = frame.span_y / MM_PER_INCH
    twists_per_inch = total_twists / billet_length_inches if billet_length_inches > 1e-9 else 0.0
    guideline_band = classify_twist_density(twists_per_inch)
    axial_scale, axial_shortening, roundness_factor = twist_material_flow_factors(
        total_twists,
        twists_per_inch,
    )
    estimated_cross_section_area = max(frame.span_x * frame.span_z, 1e-9)
    target_round_radius = float(np.sqrt((estimated_cross_section_area / axial_scale) / np.pi))
    target_round_diameter = target_round_radius * 2.0

    logger.info(
        f"Twist density: {twists_per_inch:.2f} twists/in "
        f"({total_twists:.2f} total twists over {billet_length_inches:.2f} in) — {guideline_band}"
    )
    logger.info(
        f"Twist material flow: length_scale={axial_scale:.3f}, "
        f"roundness={roundness_factor:.3f}, target_round_diameter={target_round_diameter:.2f}mm"
    )

    def twist_field(vertices, layer, layer_idx, current_frame):
        normalized_position = (vertices[:, 1] - current_frame.y_min) / current_frame.span_y
        current_angles = angle_rad * normalized_position
        cos_angles = np.cos(current_angles)
        sin_angles = np.sin(current_angles)

        x_rel = vertices[:, 0] - current_frame.center_x
        z_rel = vertices[:, 2] - current_frame.center_z
        # Torsion alone mathematically preserves length and keeps flat sides.
        # Real hot twisting compacts the billet. The cross-section flow below
        # is driven by that compression: as axial shortening rises, the
        # rectangle/octagon section maps toward an area-preserving round bar.
        half_x = max(current_frame.span_x * 0.5, 1e-9)
        half_z = max(current_frame.span_z * 0.5, 1e-9)
        x_normalized = x_rel / half_x
        z_normalized = z_rel / half_z
        rectangular_radius = np.maximum(np.abs(x_normalized), np.abs(z_normalized))
        polar_angle = np.arctan2(z_normalized, x_normalized)

        x_round_target = np.cos(polar_angle) * target_round_radius * rectangular_radius
        z_round_target = np.sin(polar_angle) * target_round_radius * rectangular_radius
        x_round = x_rel + (x_round_target - x_rel) * roundness_factor
        z_round = z_rel + (z_round_target - z_rel) * roundness_factor

        displaced = vertices.copy()
        displaced[:, 0] = x_round * cos_angles - z_round * sin_angles + current_frame.center_x
        displaced[:, 1] = current_frame.center_y + (vertices[:, 1] - current_frame.center_y) * axial_scale
        displaced[:, 2] = x_round * sin_angles + z_round * cos_angles + current_frame.center_z

        if debug and len(vertices) > 0:
            logger.debug(
                f"  Layer #{layer_idx}: y-normalized range "
                f"{normalized_position.min():.3f} -> {normalized_position.max():.3f}, "
                f"angle range {np.rad2deg(current_angles.min()):.2f}° -> "
                f"{np.rad2deg(current_angles.max()):.2f}°, "
                f"length_scale={axial_scale:.3f}, roundness={roundness_factor:.3f}"
            )

        return displaced

    stats = apply_displacement_to_billet(
        billet,
        'twist',
        twist_field,
        {
            'angle_degrees': angle_degrees,
            'total_twists': total_twists,
            'billet_length_inches': billet_length_inches,
            'twists_per_inch': twists_per_inch,
            'guideline_band': guideline_band,
            'standard_twists_per_inch': STANDARD_TWISTS_PER_INCH,
            'turkish_twists_per_inch': TURKISH_TWISTS_PER_INCH,
            'axial_scale': axial_scale,
            'axial_shortening': axial_shortening,
            'roundness_factor': roundness_factor,
            'target_round_radius': target_round_radius,
            'source_span_x': frame.span_x,
            'source_span_z': frame.span_z,
            'axis': axis,
            'center_x': frame.center_x,
            'center_y': frame.center_y,
            'center_z': frame.center_z,
            'y_min': frame.y_min,
            'y_max': frame.y_max,
            'material_layers': material_layers,
        },
        extra_param=angle_degrees,
        debug=debug,
    )

    print(f"Twist complete! Processed {stats.vertices_processed} vertices.")