"""
Demo Pattern Functions for Damascus Pattern Simulator
======================================================

Standalone demo functions that showcase different Damascus steel patterns.
Each function creates a billet, applies operations, and visualizes the result.

Usage:
    from lib.demo_functions import demo_feather_pattern, demo_twist_pattern, demo_raindrop_pattern
"""

import matplotlib.pyplot as plt

from lib.logging_config import logger
from lib.damascus_billet import Damascus3DBillet


def demo_feather_pattern():
    """
    Demo: Feather Damascus using wedge deformation.

    PROCESS:
    -------
    1. Create billet with 30 alternating layers
    2. Apply wedge split (creates two waterfalls)
    3. Extract cross-section to view pattern

    EXPECTED RESULT:
    ---------------
    Feather/waterfall pattern with central vein
    """
    logger.info("=" * 70)
    logger.info("STARTING FEATHER DAMASCUS DEMO")
    logger.info("=" * 70)

    print("\n" + "=" * 70)
    print("  DEMO 1: FEATHER DAMASCUS (Wedge Split)")
    print("=" * 70)

    billet = Damascus3DBillet(width=50.0, length=100.0)
    billet.create_simple_layers(num_layers=30, white_thickness=0.8, black_thickness=0.8)

    print("\nStep 1: Original billet")
    billet.visualize("Feather Damascus - Step 1: Original Billet")

    print("\nStep 2: Wedge split")
    billet.apply_wedge_deformation(wedge_depth=18.0, wedge_angle=35.0, split_gap=6.0, debug=True)
    billet.visualize("Feather Damascus - Step 2: After Wedge Split")

    print("\nStep 3: Extract cross-section to see the pattern")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)

    # Display the cross-section
    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Feather Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()

    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="feather_pattern.png", resolution=1600)
    billet.save_operation_log("feather_operations.json")

    logger.info("Feather Damascus demo complete")
    return billet


def demo_twist_pattern():
    """
    Demo: Ladder/Twist Damascus.

    PROCESS:
    -------
    1. Create billet with 24 layers
    2. Apply 180° twist along length
    3. Compress to consolidate
    4. Extract cross-section to view ladder pattern
    """
    logger.info("=" * 70)
    logger.info("STARTING TWIST DAMASCUS DEMO")
    logger.info("=" * 70)

    print("\n" + "=" * 70)
    print("  DEMO 2: LADDER/TWIST DAMASCUS")
    print("=" * 70)

    billet = Damascus3DBillet(width=40.0, length=120.0)
    billet.create_simple_layers(num_layers=24, white_thickness=1.0, black_thickness=1.0)

    print("\nStep 1: Original billet")
    billet.visualize("Twist Damascus - Step 1: Original Billet")

    print("\nStep 2: Apply twist")
    billet.apply_twist(angle_degrees=180.0, axis='y', debug=True)
    billet.visualize("Twist Damascus - Step 2: After 180° Twist")

    print("\nStep 3: Compress to consolidate")
    billet.apply_compression(compression_factor=0.7, debug=True)
    billet.visualize("Twist Damascus - Step 3: After Compression")

    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)

    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Ladder Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()

    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="twist_pattern.png", resolution=1600)
    billet.save_operation_log("twist_operations.json")

    logger.info("Twist Damascus demo complete")
    return billet


def demo_raindrop_pattern():
    """
    Demo: Raindrop Damascus using drilling.

    PROCESS:
    -------
    1. Create billet with 25 layers
    2. Drill grid of holes (3x3 pattern)
    3. Compress to close holes and create raindrops
    4. Extract cross-section
    """
    logger.info("=" * 70)
    logger.info("STARTING RAINDROP DAMASCUS DEMO")
    logger.info("=" * 70)

    print("\n" + "=" * 70)
    print("  DEMO 3: RAINDROP DAMASCUS (Drilling)")
    print("=" * 70)

    billet = Damascus3DBillet(width=60.0, length=80.0)
    billet.create_simple_layers(num_layers=25, white_thickness=0.8, black_thickness=0.8)

    print("\nStep 1: Original billet")
    billet.visualize("Raindrop Damascus - Step 1: Original Billet")

    print("\nStep 2: Drill holes in pattern")
    # Create a grid of holes (3x3)
    hole_positions = [
        (-15, -20), (0, -20), (15, -20),
        (-15, 0), (0, 0), (15, 0),
        (-15, 20), (0, 20), (15, 20)
    ]

    logger.info(f"Drilling {len(hole_positions)} holes in grid pattern")
    for hole_idx, (x_pos, z_pos) in enumerate(hole_positions):
        logger.debug(f"  Hole {hole_idx + 1}/{len(hole_positions)}: ({x_pos}, {z_pos})")
        billet.drill_hole(x_pos=x_pos, z_pos=z_pos, radius=6.0, debug=(hole_idx == 0))

    billet.visualize("Raindrop Damascus - Step 2: After Drilling Holes")

    print("\nStep 3: Compress to close holes and create raindrops")
    billet.apply_compression(compression_factor=0.5, debug=True)
    billet.visualize("Raindrop Damascus - Step 3: After Compression")

    print("\nStep 4: Extract cross-section")
    cross_section = billet.extract_cross_section(z_slice=0.0, resolution=800, debug=True)

    plt.figure(figsize=(12, 8))
    plt.imshow(cross_section, cmap='gray', vmin=0, vmax=255)
    plt.title('Raindrop Damascus - Cross-Section View', fontsize=14, fontweight='bold')
    plt.xlabel('Width', fontsize=10)
    plt.ylabel('Height (layers)', fontsize=10)
    plt.tight_layout()
    plt.show()

    # Save outputs
    billet.save_cross_section_image(z_slice=0.0, output_path="raindrop_pattern.png", resolution=1600)
    billet.save_operation_log("raindrop_operations.json")

    logger.info("Raindrop Damascus demo complete")
    return billet
