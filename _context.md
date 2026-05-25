# Damascus Pattern Simulator — Context
> **Version**: 2.3.0-beta | **Status**: Active Development | **Last updated**: 2026-05-10

## What It Is
3D Damascus steel pattern simulator for bladesmiths. Simulates layered steel billets through forging operations (square, octagon, twist, wedge) with volume conservation. Primary user: Gary's wife.

## Dual Frontend Architecture
1. **Legacy Tkinter GUI** (`damascus_3d_gui.py`) — VisPy OpenGL viewport, full feature set
2. **Electron + React UI** (new, Mar 2026) — Three.js WebGL, FastAPI Python backend, Tailwind CSS

## Key Paths
- Electron: `src/main/`, `src/renderer/src/`, `python/engine/`
- Legacy: `damascus_3d_gui.py`, `damascus_3d_simulator.py`, `vispy_3d_viewer.py`
- Shared lib modules via `python/vendor/` symlink shim

## Coordinate System
- Engine: X=width, Y=length, Z=height (layers stack in Z)
- Three.js: X=width, Y=height(up), Z=length — remap done in Viewport3D.tsx

## Recent Work
- May 3: Preferences dialog with metric/imperial unit switching
- Electron UI integrated, Tkinter GUI still available
- Forge to octagon with chamfering added

## Detailed Notes
- `.dev_notes.md` — Comprehensive architecture, variables, testing checklist
- `DEVNOTES_*.md` — Per-feature development logs
- `KNOWLEDGE_BASE.md` (parent dir) — Cross-project context (outdated Feb 2026)
