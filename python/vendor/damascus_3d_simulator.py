#!/usr/bin/env python3
"""
3D Damascus Billet Simulator - Production Version
==================================================

BREAKTHROUGH APPROACH:
---------------------
This simulator uses REAL 3D mesh layers with REAL physics-based deformation,
not 2D pixel manipulation. This is fundamentally how Damascus forging actually works.

KEY INSIGHT FROM DEBUGGING SESSION:
-----------------------------------
The previous 2D approach failed because:
  - Horizontal layers in a 2D pixel array have no physical "ends" to pull together
  - You can't simulate 3D material flow by warping pixels
  - The wedge split creates actual 3D geometry changes that pixels cannot represent

NEW APPROACH:
------------
  - Each Damascus layer is a 3D triangular mesh (thin rectangular solid)
  - Deformations modify actual 3D vertex positions
  - Physics includes: wedge splitting, twisting, compression, drilling
  - Can view from ANY angle in 3D space
  - Extract 2D cross-sections to see traditional Damascus patterns

ARCHITECTURE:
-------------
  DamascusLayer: Single layer (3D mesh + metadata)          -> lib/damascus_layer.py
  Damascus3DBillet: Stack of layers + deformation operations -> lib/damascus_billet.py
  Logging: Comprehensive debug logging to file + console     -> lib/logging_config.py
  Visualization: Matplotlib 3D (Wayland-compatible)
  Demo Functions: Feather, Twist, Raindrop demos             -> lib/demo_functions.py

Author: Damascus Pattern Simulator Team
Date: 2026-02-02
Version: 2.0 (3D Mesh-Based) — Modularized
"""

# ---------------------------------------------------------------------------
# Backward-compatible re-exports
# ---------------------------------------------------------------------------
# All classes, functions and constants that used to live in this file are now
# in the lib/ package.  Existing code that does:
#     from damascus_3d_simulator import Damascus3DBillet, DamascusLayer, logger
# will continue to work unchanged.
# ---------------------------------------------------------------------------

import sys

from lib.logging_config import (          # noqa: F401
    setup_logging,
    logger,
    RUNTIME_ROOT,
    LOGS_DIR,
)

from lib.api_instrumentation import (     # noqa: F401
    _resolve_source_location,
    _api_call_wrapper,
    install_api_call_logging as _install_api_call_logging,
)

from lib.damascus_layer import DamascusLayer    # noqa: F401
from lib.damascus_billet import Damascus3DBillet  # noqa: F401

from lib.demo_functions import (          # noqa: F401
    demo_feather_pattern,
    demo_twist_pattern,
    demo_raindrop_pattern,
)


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    """
    Main program: Interactive demo selector.

    FLOW:
    ----
    1. Display menu of available demos
    2. User selects pattern type
    3. Run demo with full visualization
    4. Save debug logs and outputs
    5. Repeat or exit
    """
    logger.info("=" * 70)
    logger.info("MAIN PROGRAM STARTED")
    logger.info("=" * 70)

    print("=" * 70)
    print("  DAMASCUS 3D BILLET SIMULATOR - PROOF OF CONCEPT")
    print("=" * 70)
    print("\nThis is a BREAKTHROUGH approach to Damascus pattern simulation!")
    print("\nInstead of manipulating 2D pixels, we create REAL 3D layers and")
    print("apply REAL physical deformations. This is how Damascus actually works!")
    print("=" * 70)

    while True:
        print("\n" + "=" * 70)
        print("AVAILABLE DEMOS:")
        print("=" * 70)
        print("1. Feather Damascus (wedge split + waterfall)")
        print("2. Ladder/Twist Damascus (torsional twist)")
        print("3. Raindrop Damascus (drilling + compression)")
        print("4. Exit")
        print("=" * 70)

        choice = input("\nSelect demo (1-4): ").strip()
        logger.info(f"User selected option: {choice}")

        if choice == '1':
            demo_feather_pattern()
        elif choice == '2':
            demo_twist_pattern()
        elif choice == '3':
            demo_raindrop_pattern()
        elif choice == '4':
            print("\n" + "=" * 70)
            print("  PROOF OF CONCEPT COMPLETE!")
            print("=" * 70)
            print("\nNext steps:")
            print("  - Refine mesh resolution for smoother deformations")
            print("  - Implement as-rigid-as-possible deformation")
            print("  - Add material property-based physics")
            print("  - Improve cross-section extraction algorithm")
            print("  - Build full interactive UI")
            print("  - Add animation timeline system")
            print("=" * 70)
            logger.info("User exited program")
            logger.info("=" * 70)
            logger.info("PROGRAM TERMINATED")
            logger.info("=" * 70)
            break
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")
            logger.warning(f"Invalid menu choice: {choice}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception("FATAL ERROR in main program:")
        print(f"\nFATAL ERROR: {e}")
        print("Check the debug log file for details.")
        sys.exit(1)
