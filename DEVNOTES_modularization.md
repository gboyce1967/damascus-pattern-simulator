# Development Notes: Modularization Refactoring

**Branch:** `refactor/modularize-functions`
**Date:** 2026-03-01
**Author:** Gary + Oz (AI assistant)

## Summary

Refactored the Damascus Pattern Simulator from monolithic scripts into a modular
`lib/` package. Each function/class now lives in its own module, making the code
reusable for future scripts and easier to maintain.

## Before (monolithic)

| File | Lines | Description |
|------|-------|-------------|
| damascus_3d_simulator.py | ~1524 | Everything: logging, layer, billet, demos, main |
| damascus_3d_gui.py | ~2608 | Entire GUI with all dialogs, forging, export |
| vispy_3d_viewer.py | ~368 | VisPy 3D viewer class |

## After (modular)

### lib/ modules (new)

| Module | Contents |
|--------|----------|
| `__init__.py` | Package init, core exports |
| `logging_config.py` | `setup_logging()`, `logger`, `RUNTIME_ROOT`, `LOGS_DIR` |
| `api_instrumentation.py` | API call wrapping/tracing for debugging |
| `damascus_layer.py` | `DamascusLayer` class (single 3D mesh layer) |
| `damascus_billet.py` | `Damascus3DBillet` class (full simulation engine, ~798 lines) |
| `vispy_viewer.py` | `DamascusVispyViewer` class (OpenGL 3D viewer) |
| `tk_log_handler.py` | `TkTextLogHandler` (streams logs to Tkinter widget) |
| `gui_dialogs.py` | Debug console, billet stats, about, quick start, build plate warning |
| `gui_references.py` | Heat treatment guide, steel properties, custom steel dialog, forging/plasticity refs |
| `gui_export.py` | `export_3d_model()`, `export_cross_section()`, `export_operation_log()` |
| `gui_forging.py` | `forge_to_square()`, `forge_to_octagon()` with physics and dialogs |
| `demo_functions.py` | `demo_feather_pattern()`, `demo_twist_pattern()`, `demo_raindrop_pattern()` |

### Root-level scripts (slimmed down)

| File | Role |
|------|------|
| `damascus_3d_simulator.py` | Thin entry point + backward-compatible re-exports from lib |
| `damascus_3d_gui.py` | GUI layout + thin method wrappers delegating to lib |
| `vispy_3d_viewer.py` | Re-export wrapper for `lib.vispy_viewer.DamascusVispyViewer` |

## Design Decisions

1. **Standalone functions (not mixins):** GUI helpers accept required state as
   parameters rather than being mixed into the GUI class. This maximizes
   reusability — any future script can call `forge_to_square(root, billet, ...)`.

2. **Backward-compatible imports:** Existing code like
   `from damascus_3d_simulator import Damascus3DBillet` still works unchanged.

3. **Consolidated `show_build_plate_warning()`:** Three duplicate build-plate
   warning dialogs were unified into one reusable function in `gui_dialogs.py`.

4. **Lazy imports for steel database:** `gui_references.py` imports the steel
   database at function call time to avoid circular dependencies.

5. **Module-level API instrumentation:** `damascus_billet.py` calls
   `install_api_call_logging()` at import time, same as the original.

## Files Unchanged

- `data/steel_database.py` — steel database (untouched)
- `data/__init__.py` — data package init (untouched)
- `data/*.txt` — reference data files (untouched)

## Syntax Verification

All 15 Python files pass `python -m py_compile` with zero errors.
