"""
Damascus Pattern Simulator - Library Modules
=============================================

Reusable modules extracted from the monolithic scripts.
Each module is self-contained and can be imported independently.

Modules:
    logging_config       - Logger setup, RUNTIME_ROOT, LOGS_DIR
    api_instrumentation  - API call tracing / instrumentation
    damascus_layer       - DamascusLayer (single 3D mesh layer)
    damascus_billet      - Damascus3DBillet (full billet engine)
    vispy_viewer         - DamascusVispyViewer (OpenGL 3D viewer)
    tk_log_handler       - TkTextLogHandler (streams logs to Tkinter widget)
    gui_dialogs          - Standalone GUI dialog helpers (incl. center_dialog)
    gui_references       - Reference material viewer dialogs
    gui_export           - Export functions (3D model, cross-section, log)
    gui_forging          - Backward-compat re-exports for forging dialogs
    forging_wedge        - Wedge deformation (feather Damascus)
    forging_twist        - Twist deformation (ladder/twist Damascus)
    forging_compression  - Compression (hammering/pressing)
    forging_drill        - Drilling (raindrop Damascus)
    forging_square       - Forge to square bar (GUI dialog + physics)
    forging_octagon      - Forge to octagonal bar (GUI dialog + physics)
    demo_functions       - CLI demo runners
"""

# Core engine
from lib.logging_config import setup_logging, logger, RUNTIME_ROOT, LOGS_DIR
from lib.damascus_layer import DamascusLayer
from lib.damascus_billet import Damascus3DBillet

__all__ = [
    # Core engine
    'setup_logging', 'logger', 'RUNTIME_ROOT', 'LOGS_DIR',
    'DamascusLayer', 'Damascus3DBillet',
    # Submodules available via lib.<name>
    'api_instrumentation',
    'vispy_viewer',
    'tk_log_handler',
    'gui_dialogs',
    'gui_references',
    'gui_export',
    'gui_forging',
    'forging_wedge',
    'forging_twist',
    'forging_compression',
    'forging_drill',
    'forging_square',
    'forging_octagon',
    'demo_functions',
]
