# VisPy Migration - Development Notes

## Date: 2026-02-05

## Problem Statement
Matplotlib's 3D axes have fundamental limitations with zoom functionality:
- Objects appear to grow beyond axis limits when zooming
- Both perspective and orthographic projections exhibit this issue
- Changing axis limits, camera distance (dist), or using set_box_aspect all fail
- This is a known matplotlib limitation (issues #110, #749, #25804, #18052, #19096)

## Solution: Migrate to VisPy
VisPy is an OpenGL-based visualization library that provides proper 3D rendering with correct zoom behavior.

## Research Findings
- **Reference Project**: [mesh-viewer](https://github.com/precise-simulation/mesh-viewer) - Shows VisPy embedded in Tkinter for STL/OBJ mesh viewing
- **Performance**: VisPy is fast and produces small binaries (~35MB vs matplotlib)
- **Integration**: Can embed VisPy canvas in Tkinter using parent widget parameter

## Installation
```bash
pip install vispy PyOpenGL
```

Dependencies added to requirements.txt:
- vispy>=0.14.0
- PyOpenGL>=3.1.0

## Architecture Plan

### New Module: vispy_3d_viewer.py
A dedicated module for VisPy-based 3D rendering:
- DamascusVispyViewer class
- Handles mesh rendering from Open3D meshes
- Provides camera controls (zoom, rotate, pan)
- Embeddable in Tkinter frame

### Key Features to Implement
1. **Mesh Rendering**: Convert Open3D triangle meshes to VisPy mesh visuals
2. **Camera System**: Use VisPy's Turntable or Arcball camera for intuitive controls
3. **Mouse Controls**:
   - Left drag: Rotate
   - Mouse wheel: Zoom
   - Right drag: Pan
4. **Build Plate Visualization**: Draw build plate boundary as reference
5. **Layer Colors**: Maintain alternating steel colors from current implementation

### Integration Points
Replace in damascus_3d_gui.py:
- Line ~421-439: Replace matplotlib Figure/Canvas with VisPy SceneCanvas
- Line ~1490-1603: Replace update_3d_view() to use VisPy rendering
- Line ~1658-1672: Remove custom zoom handler (VisPy handles it)

## VisPy Concepts
- **SceneCanvas**: Top-level widget, embeds in Tkinter
- **ViewBox**: Container providing pan/zoom/rotate
- **Mesh Visual**: Renders triangle meshes with vertices and faces
- **Camera**: Controls viewpoint (Turntable, Arcball, PanZoom, etc.)
- **Transform**: Handles scaling, rotation, translation

## Implementation Steps
1. ✓ Install VisPy and dependencies
2. Create vispy_3d_viewer.py module
3. Implement DamascusVispyViewer class
4. Integrate into damascus_3d_gui.py
5. Test zoom, rotation, pan controls
6. Verify build plate boundaries remain consistent

## Expected Benefits
- Proper zoom that maintains spatial relationships
- Better performance for complex meshes
- Hardware-accelerated rendering
- Professional-grade 3D interaction

## Fallback Plan
If VisPy integration proves difficult, alternative options:
- PyVista (VTK-based, more features but heavier)
- Plotly (browser-based, good interactivity)
- Accept matplotlib limitations and disable zoom

## Notes
- Keep matplotlib for 2D cross-section preview (it works well for 2D)
- VisPy uses OpenGL directly, requires graphics drivers
- Test on Gary's Ubuntu system to ensure OpenGL support
