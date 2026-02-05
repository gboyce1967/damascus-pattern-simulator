# Damascus Pattern Simulator - Beta Release (3D Version)
**Version**: 2.0-beta  
**Release Date**: 2026-02-04  
**Status**: 🚧 **BETA - UNDER ACTIVE DEVELOPMENT** 🚧

---

## ⚠️ BETA SOFTWARE WARNING

**This is beta software and is still under active development.**

### What Works
✅ 3D mesh-based billet creation  
✅ Static build plate system with auto-resize  
✅ Forge to square bar (with volume conservation)  
✅ Forge to octagonal bar (with chamfering)  
✅ 3D visualization with camera controls  
✅ Cross-section preview  
✅ Export to .obj format  

### What's In Development
🚧 **Twist/Ladder Damascus** - Implemented but needs testing  
🚧 **Feather Damascus** - Wedge deformation needs refinement  
🚧 **Raindrop Damascus** - Drilling operation needs testing  
🚧 **Compression operations** - Not yet implemented  
🚧 **Undo/Redo system** - Planned, not yet implemented  

### Known Issues
⚠️ **No undo functionality** - Use "Reset Billet" to start over  
⚠️ **Some pattern operations untested** - May produce unexpected results  
⚠️ **Twist requires forging first** - Must forge to square/octagon before twisting  
⚠️ **Performance with large billets** - Billets with >100 layers may be slow  

**USE AT YOUR OWN RISK. This software may have bugs, crashes, or unexpected behavior.**

---

## 🎉 What's New in 3D Version

This is a **complete rewrite** of the Damascus Pattern Simulator using real 3D physics and mesh-based simulation. The old 2D pixel-based simulator has been deprecated in favor of this more accurate and powerful 3D engine.

### Recent Updates (2026-02-05)
- Added live debug console streaming in `damascus_3d_gui.py` via `TkTextLogHandler`
- Added API call instrumentation logs in `damascus_3d_simulator.py` (callable, source file, definition line)
- Added project folder organization for clarity: `Notes/`, `Research/`, `data/`, `Staging/`, `testing/`, `Installation_and_Launch/`
- Added Windows install/run support files (`Installation_and_Launch/install_windows.bat`, `run_windows.bat`, `Installation_and_Launch/INSTALL_WINDOWS.md`, `Installation_and_Launch/requirements.txt`)
- Updated Windows installer to enforce Python 3.12 for Open3D compatibility
- Consolidated beta documentation into the root `README.md` so release notes stay current

### Major Features

#### ✨ **3D Mesh-Based Physics Engine**
- True 3D geometry using Open3D library
- Real volume conservation during forging operations
- Accurate material deformation modeling
- Multiple heats simulation for realistic forging

#### 🎨 **Interactive 3D Visualization**
- Real-time 3D viewport with matplotlib
- Adjustable camera angles (elevation, azimuth)
- Mouse wheel zoom support
- Quick view presets (top, front, isometric)
- Cross-section preview at any Z height

#### 🏭 **Static Build Plate System** (NEW!)
- Configurable workspace dimensions (default 400×400mm)
- Visual build plate boundary reference
- Intelligent oversized billet warnings
- **Auto-resize feature**: One-click build plate adjustment
- Consistent viewport that doesn't change with billet size

#### 🔨 **Realistic Forging Operations** (TESTED & WORKING)
- **Forge to Square Bar**: Compress billet into square cross-section
- **Forge to Octagonal Bar**: Create 8-sided profile with chamfering
- Progressive multi-heat forging simulation
- Volume conservation validation
- Automatic length extension calculation

#### 📐 **Pattern Operations** (EXPERIMENTAL)
- **Feather Damascus**: Wedge deformation with material splitting (⚠️ IN DEVELOPMENT)
- **Twist/Ladder Damascus**: Torsional deformation around length axis (⚠️ NEEDS TESTING)
- **Raindrop Damascus**: Drill holes with material flow simulation (⚠️ NEEDS TESTING)
- Real-time cross-section preview showing pattern

---

## 🚀 Installation

### Requirements
- Python 3.8+
- Virtual environment (included)
- Linux/Ubuntu (tested on Ubuntu)

### Quick Install
```bash
cd ~/Projects/damascus-pattern-simulator
chmod +x install-DPS.sh
./install-DPS.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies (Open3D, matplotlib, PIL, numpy)
- Create desktop launcher
- Set up the application

### Manual Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install open3d matplotlib pillow numpy
```

---

## 🎮 Usage

### Launch the Application
```bash
./damascus_3d_gui.py
```

Or use the desktop launcher: `Damascus Pattern Simulator`

### Recommended Workflow (BETA)

**For best results, start with these tested features:**

1. **Create a Billet**
   - Set layer count (default: 30 layers - TESTED)
   - Set layer thickness (white/black: 0.8mm each)
   - Set billet dimensions (width × length, keep under 200mm for performance)
   - Click "Create New Billet"

2. **Configure Build Plate**
   - Adjust width/length in "Build Plate (Workspace)" section
   - Default: 400×400mm (WORKING)
   - Auto-resize will trigger if billet exceeds plate size (WORKING)

3. **Forge the Billet** ✅ **RECOMMENDED - FULLY TESTED**
   - Click "🔨 Forge to Square Bar" or "⬡ Forge to Octagon Bar"
   - Enter target bar size (try 15-25mm for good results)
   - Set number of heats (3-7 recommended)
   - Click "Forge"
   - Choose auto-resize if bar exceeds build plate

4. **Export Your Work**
   - 💾 Save 3D Model (.obj format) - WORKING
   - 🖼️ Save Cross-Section (PNG image) - WORKING
   - 📋 Save Operation Log (JSON) - WORKING

5. **Pattern Operations** ⚠️ **EXPERIMENTAL - USE WITH CAUTION**
   - These features are implemented but not fully tested
   - May produce unexpected results
   - Save your work before applying patterns
   - If something goes wrong, use "🔄 Reset Billet"

---

## 📊 Build Plate System ✅ (WORKING)

### What is the Build Plate?
The build plate represents your workspace - a fixed area where billets can be placed. This mimics real-world manufacturing where you have workspace constraints.

### Features
- **Static Reference Frame**: Viewport doesn't resize with every billet change ✅
- **Visual Boundary**: Dashed gray rectangle shows workspace limits ✅
- **Intelligent Warnings**: Alerts when billet or forged bar exceeds plate size ✅
- **Auto-Resize**: One-click adjustment to fit oversized billets ✅

### Auto-Resize Options
When a billet exceeds the build plate, you get three choices:
1. **📐 Auto-Resize Build Plate**: Automatically adjusts to 110% of needed size (squared for symmetry)
2. **✓ Continue Anyway**: Proceed with oversized billet (for visualization purposes)
3. **✗ Cancel**: Abort the operation

---

## 🔧 Technical Details

### Architecture
- **GUI**: Tkinter-based with matplotlib 3D viewport
- **3D Engine**: Open3D for mesh operations
- **Physics**: Volume-conserving transformations
- **Coordinate System**: X=width, Y=length, Z=height (layers stack in Z)

<img width="1205" height="678" alt="image" src="https://github.com/user-attachments/assets/ed4abee8-e27e-43d5-9894-22a34e7ee9e1" />


### Forging Physics (VERIFIED WORKING)
Real forging physics using volume conservation:
```
V = width × length × height = constant
```

For a square bar:
```
final_length = original_volume / (target_size²)
```

Example: 50×100×24mm billet → 20×20mm square = 300mm long bar (3× extension)

### File Structure
- `damascus_3d_gui.py` - Main GUI application (1,700+ lines)
- `damascus_3d_simulator.py` - 3D physics engine (1,400+ lines)
- `3D_DEVELOPMENT_NOTES.md` - Detailed development documentation
- `Research/` - Pattern research and deformation math references
- `data/` - Steel data files and lookup module
- `Staging/` - Prepared files for integration
- `testing/` - PoC/test scripts
- `Installation_and_Launch/` - Windows installation assets and packaging config
- **Old/Deprecated**: `damascus_simulator.py` - Old 2D version (DO NOT USE)

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
- First render may take a few seconds to initialize Open3D

### Stability
- **Generally stable** for billet creation and forging operations
- **May crash** during experimental pattern operations
- **Save your work frequently** using export functions
- Check debug logs (`damascus_3d_debug_*.log`) if crashes occur

---

## 📖 Documentation

### Included Documentation
- `3D_DEVELOPMENT_NOTES.md` - Complete technical documentation (1,100+ lines)
- `Research/FEATHER_PATTERN_PHYSICS.md` - Feather pattern deformation physics (IN DEVELOPMENT)
- `Research/FEATHER_PATTERN_NOTES.md` - Feather pattern deformation notes
- `Research/material-deformation-math.md` - Mathematical models for deformation
- `Installation_and_Launch/INSTALL_WINDOWS.md` - Windows installation and setup walkthrough

### Debug Logging
Debug logs are automatically created in the project directory:
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
The original 2D pixel-based simulator (`damascus_simulator.py`) is **DEPRECATED** and should **NOT BE USED**.

**Status**: Kept in repository for reference only  
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
2. Check debug logs: `damascus_3d_debug_*.log`
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
- **matplotlib**: 3D visualization
- **Damascus steel community**: Inspiration and reference patterns
- **Beta testers**: Thank you for your patience!

---

## 📞 Support & Help

For questions or issues:
1. **READ THIS README FIRST** - especially the "Known Issues" section
2. Check documentation in `Notes/3D_DEVELOPMENT_NOTES.md`
3. Review session notes in `Notes/` for recent changes
4. Check debug logs for error details (`damascus_3d_debug_*.log`)
5. Submit GitHub issue with:
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
- `Notes/3D_DEVELOPMENT_NOTES.md` - Technical background
- `Research/FEATHER_PATTERN_PHYSICS.md` - Pattern formation physics
- `Research/material-deformation-math.md` - Mathematical models

---

## 🚀 Getting Started (Quick Reference)

**For first-time users:**
1. Install using `./install-DPS.sh`
2. Launch: `./damascus_3d_gui.py`
3. Create a default billet (50×100mm, 30 layers)
4. Try forging to square bar (15mm, 5 heats)
5. Export the result (.obj file)
6. View in your favorite 3D viewer

**That's it!** You've created your first 3D Damascus billet with realistic forging physics!

---

**Enjoy creating Damascus patterns in 3D - and thank you for being a beta tester!** 🗡️✨

**Remember: This is beta software. Save often, expect bugs, and report issues!**

---

*Last Updated: 2026-02-05*  
*Version: 2.0-beta*  
*Status: Active Development*
