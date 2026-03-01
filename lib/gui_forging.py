"""
GUI Forging Operations - Backward Compatibility Re-exports
============================================================

The forging operations have been modularized into individual files:
  - lib/forging_square.py  -> forge_to_square()
  - lib/forging_octagon.py -> forge_to_octagon()

This module re-exports them so existing imports continue to work:
    from lib.gui_forging import forge_to_square, forge_to_octagon
"""

from lib.forging_square import forge_to_square    # noqa: F401
from lib.forging_octagon import forge_to_octagon  # noqa: F401
