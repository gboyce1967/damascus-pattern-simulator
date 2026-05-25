# Forging Operation Modularization - Dev Notes

**Date:** 2026-03-01
**Branch:** refactor/modularize-functions

## Summary

This note records the original 2026-03-01 modularization, when 6 forging
operations were extracted from `damascus_billet.py` and `gui_forging.py` into
individual modules under `lib/`. Some of those original Tkinter GUI modules have
since been superseded by the Electron/FastAPI implementation described below.

## Current Status Update — 2026-05-25

The Tkinter square/octagon dialog path has been removed. The following files were
historical GUI-only modules and are no longer active project modules:

- `lib/gui_forging.py`
- `lib/forging_square.py`
- `lib/forging_octagon.py`

Square and octagon forging now run through `python/engine/forge_ops.py`:

- `forge_to_square_safe(billet, target_bar_size, num_heats)`
- `forge_to_octagon_safe(billet, target_bar_size, num_heats, chamfer_percent, ...)`

The active shared support modules for the displacement-first architecture are:

- `lib/forging_utils.py`
- `lib/forging_displacement.py`
- `lib/forging_octagon_mesh.py`

## Historical Modules Created During 2026-03-01 Modularization

| Module | Function | Extracted From |
|--------|----------|----------------|
| `lib/forging_wedge.py` | `apply_wedge_deformation(billet, ...)` | `damascus_billet.py` |
| `lib/forging_twist.py` | `apply_twist(billet, ...)` | `damascus_billet.py` |
| `lib/forging_compression.py` | `apply_compression(billet, ...)` | `damascus_billet.py` |
| `lib/forging_drill.py` | `drill_hole(billet, ...)` | `damascus_billet.py` |
| `lib/forging_square.py` | `forge_to_square(root, billet, ...)` | `gui_forging.py`; removed 2026-05-25 after Electron/FastAPI migration |
| `lib/forging_octagon.py` | `forge_to_octagon(root, billet, ...)` | `gui_forging.py`; removed 2026-05-25 after Electron/FastAPI migration |

## Modified Files

- **`lib/damascus_billet.py`** — Removed ~400 lines of inline forging code.
  Methods now delegate to imported module functions. Class API unchanged.
- **`lib/gui_forging.py`** — Historically replaced with a backward-compat
  re-export shim, then removed 2026-05-25 because no live code imported it.
- **`lib/gui_dialogs.py`** — Added `center_dialog()` helper (was `_center_dialog`
  in `gui_forging.py`). Also fixed `show_debug_console` signature mismatch.
- **`lib/__init__.py`** — Added 6 new module names to docstring and `__all__`.

## Bug Fix

Fixed a signature mismatch in `show_debug_console`:
- **Caller** (`damascus_3d_gui.py`) was passing 6 args (`root, logger, LOGS_DIR,
  window, text, handler`) and expecting a dict return.
- **Function** (`gui_dialogs.py`) only accepted 3 args and returned a tuple.
- **Fix:** Updated function to accept `(root, existing_window, existing_text,
  existing_handler)` and return a dict. Removed unnecessary args from caller.

## Historical Backward Compatibility

At the time of the 2026-03-01 modularization, existing callers worked without
changes:
- `damascus_3d_gui.py` — `billet.apply_twist()` etc. worked via wrappers before
  the Tkinter GUI was removed
- `lib/demo_functions.py` — same historical compatibility behavior
- `damascus_3d_simulator.py` — same historical compatibility behavior
- `from lib.gui_forging import forge_to_square` — historically worked via
  re-exports, but this path was removed 2026-05-25.

## Headless Forging Wrappers for Electron Backend (2026-03-02)

Added headless (no-GUI) wrappers in `python/engine/forge_ops.py` for the
Electron + FastAPI backend. These call the same physics as the `lib/` modules
but skip Tkinter dialogs:

- `apply_wedge_safe(billet, wedge_depth, wedge_angle, split_gap)`
- `apply_twist_safe(billet, angle_degrees)`
- `apply_compression_safe(billet, compression_factor)`
- `drill_hole_safe(billet, x_pos, z_pos, radius)`
- `forge_to_square_safe(billet, target_bar_size, num_heats)`
- `forge_to_octagon_safe(billet, target_bar_size, num_heats, chamfer_percent)` — NEW
- `cross_section_png_safe(billet, y_slice, resolution)`

All ops dispatched via `session.py:EngineSession.apply_operation(op, payload)`.

## Tkinter UI Removed (2026-03-02)

- Deleted `damascus_3d_gui.py` (Tkinter GUI entry point)
- `vispy_3d_viewer.py` already removed during merge
- Tkinter-specific square/octagon helper modules were preserved temporarily,
  then removed 2026-05-25 once the Electron/FastAPI path replaced them.
- Operational modules (forging physics, billet, layer, logging) are unchanged

## Testing

Historical import and functional operation checks:
- 6 modules imported successfully at the time of the 2026-03-01 modularization
- `gui_forging` re-exports worked historically, before removal
- Damascus3DBillet retains all methods
- All 4 billet operations execute and record to operation_history
- Electron backend: 7 headless forge_ops wrappers tested via FastAPI
