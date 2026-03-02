# Damascus Pattern Simulator
**Version**: 2.3.0-beta  
**Release Date**: 2026-03-02  
**Status**: 🚧 **BETA - UNDER ACTIVE DEVELOPMENT** 🚧

---

## ⚠️ BETA SOFTWARE WARNING

**This is beta software and is still under active development.**

### What Works
✅ Electron + React desktop application  
✅ Three.js WebGL 3D billet viewport with OrbitControls  
✅ FastAPI Python backend (auto-spawned by Electron)  
✅ 3D mesh-based billet creation  
✅ Build plate grid (auto-resizes when billet exceeds it)  
✅ Forge to square bar (with volume conservation)  
✅ Forge to octagonal bar (with chamfering)  
✅ Twist operation (full twist count slider)  
✅ Feather / wedge split  
✅ Cross-section preview  
✅ Engine log streaming  
✅ Collapsible sidebar operation panels  

### What's In Development
🚧 **Compression operations** - Backend ready, UI controls not yet added  
🚧 **Raindrop Damascus (drill)** - Backend ready, UI controls not yet added  
🚧 **Export dialog** - Backend supports OBJ/STL/PLY, native save dialog TBD  
🚧 **Undo/Redo system** - Planned  
🚧 **Steel reference database viewer** - Needs Electron UI  

### Known Issues
⚠️ **No undo functionality** - Restart session to start over  
⚠️ **Some pattern operations need testing** - May produce unexpected results  
⚠️ **Performance with large billets** - Billets with >100 layers may be slow  

---

## 🎉 What's New

### 2026-03-02 — Electron UI & Integration
- **New Electron + React + Tailwind frontend** replacing the legacy Tkinter GUI
- **Three.js WebGL viewport** with proper axis mapping (billet lies flat on build plate)
- **FastAPI Python backend** spawned by Electron, serving all forging operations
- **Collapsible sidebar** with Feather, Forge to Square, Forge to Octagon, Twist, Export
- **Twist slider** uses whole-number full twists (0–30) instead of raw degrees
- **Build plate grid** is the fixed reference frame; auto-resizes only when billet outgrows it
- **Headless forging ops** extracted into `python/engine/forge_ops.py` for all operations
- **Tkinter UI removed** — all `lib/` modules preserved with migration notes
- **Viewport resize** fills window on maximize (flex layout + ResizeObserver)

### 2026-03-01 — Modularization
- Broke monolithic scripts into reusable modules in `lib/`
  - 12 new modules covering: logging, API instrumentation, layer/billet classes, GUI dialogs, reference panels, export functions, forging operations, and demo patterns
  - All modules independently importable for scripting and automation
- Extracted 6 forging operations into individual `lib/forging_*.py` modules

### Previous Updates (2026-02-07)
- Added API call instrumentation and live debug logging
- Added project folder organization: `Research/`, `data/`, `Staging/`, `testing/`, `Installation_and_Launch/`
- Added Windows install/run support files
- Debug logs write to `logs/damascus_3d_debug_*.log`

### Major Features

#### ✨ **3D Mesh-Based Physics Engine**
- True 3D geometry using Open3D library
- Real volume conservation during forging operations
- Accurate material deformation modeling
- Multiple heats simulation for realistic forging

#### 🎨 **Interactive 3D Visualization**
- Three.js WebGL viewport with OrbitControls (rotate/pan/zoom)
- Vertex-level axis remapping (engine → scene coordinates)
- Billet origin at (0,0,0) on the build plate
- Build plate grid auto-resizes when billet outgrows it

#### 🔨 **Forging Operations**
- **Forge to Square Bar**: Volume-conserving progressive forging
- **Forge to Octagonal Bar**: Chamfered 8-sided profile
- **Twist**: Full-twist count slider (0–30 twists)
- **Feather / Wedge Split**: Depth, angle, split gap controls
- Cross-section preview with adjustable slice position

---

## 🚀 Installation

### Requirements
- **Node.js** 18+ and **npm**
- **Python** 3.8+ with virtual environment
- **Open3D**, **FastAPI**, **uvicorn**, **Pillow** (Python packages)

### Setup
```bash
# Clone and enter the project
git clone <repo-url> ~/Projects/damascus-pattern-simulator
cd ~/Projects/damascus-pattern-simulator

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install open3d fastapi uvicorn pillow numpy

# Symlink for Electron to find Python
ln -sf venv .venv

# Node dependencies
npm install
```

---

## 🎮 Usage

### Launch (Development)
```bash
npm run dev
```

This starts:
1. Vite dev server for the React renderer
2. Electron main process
3. FastAPI Python backend (auto-spawned by Electron)

### Workflow

1. **Billet auto-creates** on launch (50×100mm, 30 layers)
2. **Forge** using sidebar controls (Square Bar, Octagonal Bar)
3. **Twist** using the full-twist slider
4. **Feather** — expand the collapsed Wedge Split section
5. **Cross-section** — adjust slice position and resolution
6. **Export** — OBJ/STL/PLY via the Export panel

---

## 📊 Build Plate System

The build plate (grid) is the **fixed reference frame** in the 3D viewport. The billet sits on it at origin (0,0,0). The grid auto-resizes only when a forging operation produces a billet that exceeds its current size (1.5× padding).

---

## 🔧 Technical Details

### Architecture
- **Frontend**: Electron + React + Tailwind CSS + Three.js
- **Backend**: FastAPI Python server (spawned by Electron)
- **3D Engine**: Open3D for mesh operations
- **Physics**: Volume-conserving transformations
- **Coordinate System**:
  - Engine: X=width, Y=length, Z=height (layers stack in Z)
  - Scene: X=width, Y=height(up), Z=length (remapped at vertex level)

### File Structure
- `src/main/` — Electron main process (spawns Python backend)
- `src/renderer/src/` — React UI components:
  - `App.tsx` — Root layout (3-column grid)
  - `components/Sidebar.tsx` — Collapsible operation panels
  - `components/Viewport3D.tsx` — Three.js WebGL viewport
  - `components/CrossSection.tsx` — Cross-section preview
  - `components/Timeline.tsx` — Operation timeline + engine logs
- `src/preload/` — Electron preload bridge (IPC → FastAPI)
- `python/engine/` — FastAPI backend:
  - `server.py` — API endpoints
  - `session.py` — Session manager + operation dispatch
  - `forge_ops.py` — Headless forging wrappers
  - `serialize.py` — Open3D mesh → JSON serialization
- `python/vendor/` — Shim importing from `lib/`
- `lib/` — Reusable module library (12+ modules):
  - `damascus_billet.py` — Core 3D engine (`Damascus3DBillet`)
  - `damascus_layer.py` — `DamascusLayer` class
  - `forging_*.py` — Individual forging operation physics
  - `logging_config.py` — Logger setup
  - `gui_*.py`, `tk_log_handler.py`, `vispy_viewer.py` — Legacy Tkinter modules (annotated with migration notes)
- `damascus_3d_simulator.py` — CLI entry point / re-export shim
- `data/` — Steel database and reference files
- `Research/` — Pattern research and deformation math
- `logs/` — Runtime debug logs

---

## 🐛 Known Issues & Limitations

### Critical Issues
⚠️ **NO UNDO FUNCTIONALITY** - Once an operation is applied, you cannot undo it. Use "Reset Billet" to start over.  
⚠️ **PATTERN OPERATIONS UNTESTED** - Twist, Feather, and Raindrop patterns are implemented but not fully tested.  
⚠️ **MUST FORGE BEFORE TWIST** - Twist operation requires forging to square or octagon first (validation enforced).  

### Known Limitations
1. **Z-axis not validated**: Only X/Y dimensions checked against build plate
2. **Single billet only**: Can't place multiple billets on build plate
3. **No animation**: Operations apply instantly (no gradual visualization)
4. **Limited undo**: Only "Reset Billet" available (loses all work)

### Performance Notes
- Large billets (>100 layers) may render slowly
- Forging with many heats (>10) takes longer but produces smoother results
- Cross-section extraction is fast (<0.1s typically)
- First render may take a few seconds to initialize Open3D/VisPy

### Stability
- **Generally stable** for billet creation and forging operations
- **May crash** during experimental pattern operations
- **Save your work frequently** using export functions
- Check debug logs (`logs/damascus_3d_debug_*.log`) if crashes occur

---

## 📖 Documentation

### Included Documentation
- `3D_DEVELOPMENT_NOTES.md` - Complete technical documentation (1,100+ lines)
- `Research/FEATHER_PATTERN_PHYSICS.md` - Feather pattern deformation physics (IN DEVELOPMENT)
- `Research/FEATHER_PATTERN_NOTES.md` - Feather pattern deformation notes
- `Research/material-deformation-math.md` - Mathematical models for deformation
- `Installation_and_Launch/INSTALL_WINDOWS.md` - Windows installation and setup walkthrough

### Debug Logging
Debug logs are automatically created by the simulator:
- Format: `damascus_3d_debug_YYYYMMDD_HHMMSS.log`
- Includes: Operation details, vertex transformations, validation checks, performance metrics
- **IMPORTANT**: Check these logs if you encounter issues

---

## 🎯 Development Roadmap

### Phase 1: Core Functionality (CURRENT - 80% COMPLETE)
- [x] 3D mesh-based billet creation
- [x] Static build plate system
- [x] Forge to square bar (TESTED)
- [x] Forge to octagonal bar (TESTED)
- [x] 3D visualization
- [x] Export to .obj format
- [ ] Test all pattern operations
- [ ] Implement undo/redo system

### Phase 2: Pattern Refinement (UPCOMING)
- [ ] Test and debug twist operation
- [ ] Refine feather/wedge deformation
- [ ] Test raindrop drilling
- [ ] Add compression operations
- [ ] Pattern presets library

### Phase 3: Advanced Features (PLANNED)
- [ ] Z-axis build plate validation
- [ ] Preset build plate sizes
- [ ] Build plate surface visualization
- [ ] Multiple billets on plate
- [ ] Animation system
- [ ] Material presets

### Phase 4: Polish (FUTURE)
- [ ] Performance optimization
- [ ] Better error handling
- [ ] User documentation
- [ ] Tutorial mode
- [ ] Pattern gallery

---

## ⚠️ Deprecation Notice

### Old 2D Simulator
The original 2D pixel-based simulator approach is **DEPRECATED** and should **NOT BE USED**.

**Status**: Legacy approach retained in project history only  
**Maintenance**: None - no bug fixes or updates  
**Recommended**: Use 3D version (`damascus_3d_gui.py`) instead  

**Why deprecated?**
- Limited to 2D cross-sections (no true 3D geometry)
- Pixel-based rendering (not scalable)
- No realistic physics modeling
- Limited pattern types

---

## 🤝 Contributing & Feedback

This is a personal project, but feedback is appreciated!

### Reporting Bugs 🐛
1. **Check if it's a known issue** (see section above)
2. Check debug logs: `logs/damascus_3d_debug_*.log`
3. Note the exact steps to reproduce
4. Include screenshots if applicable
5. Report via GitHub issues with tag `[BETA-BUG]`

### Feature Requests 💡
1. Check the roadmap first
2. Submit via GitHub issues with tag `[FEATURE-REQUEST]`
3. Describe the use case and expected behavior

### Beta Testing 🧪
Beta testers wanted! If you're willing to test experimental features:
1. Try pattern operations (twist, feather, raindrop)
2. Report what works and what doesn't
3. Share any interesting patterns you create
4. Tag feedback with `[BETA-TESTING]`

---

## 📜 License

[Your license here]

---

## 🙏 Acknowledgments

- **Open3D**: 3D mesh processing library
- **VisPy**: OpenGL 3D viewport rendering in Tkinter
- **matplotlib**: optional plotting utilities
- **Damascus steel community**: Inspiration and reference patterns
- **Beta testers**: Thank you for your patience!

---

## 📞 Support & Help

For questions or issues:
1. **READ THIS README FIRST** - especially the "Known Issues" section
2. Check documentation in `3D_DEVELOPMENT_NOTES.md`
3. Check debug logs for error details (`logs/damascus_3d_debug_*.log`)
4. Submit GitHub issue with:
   - `[BETA]` tag
   - Clear description
   - Steps to reproduce
   - Debug log excerpt (if applicable)

### Expected Response Time
This is a personal project developed in spare time. Response times may vary:
- Bug reports: 1-7 days
- Feature requests: Evaluated for roadmap
- Beta testing feedback: Appreciated anytime!

---

## 🎓 Learning Resources

New to Damascus steel patterns? Check out:
- `3D_DEVELOPMENT_NOTES.md` - Technical background
- `Research/FEATHER_PATTERN_PHYSICS.md` - Pattern formation physics
- `Research/material-deformation-math.md` - Mathematical models

---

## 🚀 Getting Started (Quick Reference)

**For first-time users:**
1. Install dependencies with `Installation_and_Launch/install_windows.bat` (Windows) or manual venv + `Installation_and_Launch/requirements.txt` (Linux/macOS)
2. Launch with `run_windows.bat` (Windows) or `python damascus_3d_gui.py`
3. Create a default billet (50×100mm, 30 layers)
4. Try forging to square bar (15mm, 5 heats)
5. Export the result (.obj file)
6. View in your favorite 3D viewer

**That's it!** You've created your first 3D Damascus billet with realistic forging physics!

---

**Enjoy creating Damascus patterns in 3D - and thank you for being a beta tester!** 🗡️✨

**Remember: This is beta software. Save often, expect bugs, and report issues!**

---

*Last Updated: 2026-03-02*  
*Version: 2.3.0-beta*  
*Status: Active Development*
