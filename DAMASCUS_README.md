# Damascus Steel Pattern Simulator

A comprehensive tool for simulating Damascus steel patterns with various transformations and effects on Linux.

## Overview

This application allows bladesmiths, metalworkers, and enthusiasts to visualize and experiment with Damascus steel patterns before forging. Create custom layer stacks, apply transformations like twisting and grinding, and export high-quality patterns for reference.

**Inspired by Thor II by Christian Schnura**

## Features

### Pattern Generation
- **Simple Layers**: Basic alternating white/black layer patterns
- **Checkerboard**: Grid-based pattern for unique Damascus effects
- **Random Pattern**: Pseudo-random layering for organic looks
- **W Pattern**: Chevron/zigzag layers forming "W" shapes  
- **C Pattern**: Curved/arced layers simulating bent billets
- **Custom Layers**: Build your own complex layer stacks

### Custom Layer Builder
- Add individual layers with specific colors (white/black) and thicknesses
- Edit existing layers by double-clicking
- Quick buttons to add 5, 10, or 20 alternating layers
- Reorder layers (move up/down)
- Remove layers or clear all
- **Save/Load**: Store custom layer stacks as JSON files for reuse
- **Apply to Patterns**: Use your custom layers with W and C patterns

### Real-Time Transformations
- **Twist**: Simulate twisting the billet (0-10 scale)
- **Grind Depth**: Visualize pattern at different grinding depths (0-100%)
- **Mosaic Stacking**: Create tiled arrangements (1x1, 2x2, 3x3)

### Layer Thickness Control
- Adjust white and black layer thickness independently
- Switch between metric (mm) and imperial (inches)
- Range: 0.1mm to 5.0mm (0.004" to 0.197")
- Real-time pattern updates

### Export & Print
- **Export formats**: PNG, JPEG, PDF (300 DPI)
- **Native print dialog**: Standard Linux print interface with full options

## Requirements

### Required
- Python 3.6+
- PIL/Pillow
- NumPy
- Tkinter (usually included with Python)

### Optional
- GTK 3.0 and PyGObject (for native print dialog)

## Installation

### Quick Install (Recommended)

**For Debian/Ubuntu/Mint:**
```bash
chmod +x install-debian.sh
./install-debian.sh
```

**For Fedora/RHEL/CentOS:**
```bash
chmod +x install-redhat.sh
./install-redhat.sh
```

The installer will:
- Check and install Python 3 if needed
- Install all required dependencies automatically
- Install optional GTK libraries for native print dialog
- Make the application executable
- Create a desktop entry in your applications menu

### Manual Installation

If you prefer to install manually:

**Debian/Ubuntu:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-tk python3-pil python3-numpy python3-gi gir1.2-gtk-3.0
pip3 install --user pillow numpy
chmod +x damascus_simulator.py
```

**Fedora/RHEL:**
```bash
sudo dnf install python3 python3-pip python3-tkinter python3-pillow python3-numpy python3-gobject gtk3
pip3 install --user pillow numpy
chmod +x damascus_simulator.py
```

## Usage

```bash
chmod +x damascus_simulator.py
./damascus_simulator.py
```

Or:

```bash
python3 damascus_simulator.py
```

## Quick Start

1. Run the application
2. Choose a preset pattern or create custom layers
3. Adjust twist, grind depth, and layer thickness
4. Export or print your pattern

## Publishing to GitHub

1. Create a new repository on GitHub: https://github.com/new
2. Name it "damascus-pattern-simulator"
3. Run these commands in your terminal:

```bash
cd /home/gary
git init
git add damascus_simulator.py DAMASCUS_README.md
git add install-debian.sh install-redhat.sh uninstall-debian.sh uninstall-redhat.sh
git commit -m "Initial commit: Damascus Pattern Simulator v1.0 with installers"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/damascus-pattern-simulator.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Optional: Add a .gitignore file

```bash
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
*.log
.DS_Store
EOF

git add .gitignore
git commit -m "Add .gitignore"
git push
```

## Code Structure

The code is well-commented and organized into two main classes:

### `DamascusSimulator` Class
- Main application window and UI setup
- Pattern generation (simple, W, C, checkerboard, random, custom)
- Transformation effects (twist, grind, mosaic)
- File operations (load, export, print)
- Layer color calculation for custom stacks

### `CustomLayerDialog` Class
- Custom layer stack builder dialog
- Layer management (add, edit, remove, reorder)
- Quick add buttons (5, 10, 20 alternating layers)
- Save/load layer stacks to JSON files
- Apply custom stacks to W and C patterns

### Key Methods

**Pattern Creation:**
- `create_simple_layers()` - Alternating white/black layers
- `create_w_pattern()` - Chevron/W-shaped layers
- `create_c_pattern()` - Curved/arced layers
- `create_custom_layers()` - User-defined layer stacks

**Transformations:**
- `apply_twist()` - Radial twist effect
- `apply_grind()` - Depth simulation via vertical shift
- `apply_mosaic()` - Tiled pattern arrangement

**Utilities:**
- `get_layer_color_at_position()` - Calculate color for custom layer stacks
- `mm_to_pixels()` / `inches_to_mm()` - Unit conversions
- `print_pattern()` - GTK native print dialog integration

## File Formats

### Layer Stack JSON
Custom layer stacks are saved in JSON format:
```json
[
  {"color": "white", "thickness": 1.5},
  {"color": "black", "thickness": 1.0},
  {"color": "white", "thickness": 2.0}
]
```

### Export Formats
- **PNG**: Lossless, best for digital use
- **JPEG**: Compressed, smaller file size
- **PDF**: 300 DPI, best for printing

## Uninstallation

To remove the Damascus Pattern Simulator:

**Debian/Ubuntu:**
```bash
./uninstall-debian.sh
```

**Fedora/RHEL:**
```bash
./uninstall-redhat.sh
```

This will remove:
- Desktop application entry
- User-installed Python packages (pillow, numpy)
- The main application file remains for manual deletion if desired

## Troubleshooting

**Print dialog doesn't appear:**
- Install GTK: `sudo apt install python3-gi gir1.2-gtk-3.0`

**Pattern looks pixelated:**
- Normal at high twist values
- Export resolution (300 DPI) is higher than display

**Custom layers not visible:**
- Ensure layer thicknesses are > 0.1mm
- Check that layers were added to the list

**Installer fails:**
- Make sure scripts are executable: `chmod +x install-*.sh`
- Check you're using the correct installer for your distribution

## Credits

- **Inspired by**: Thor II by Christian Schnura
- **Author**: Gary
- **Version**: 1.0
- **Date**: January 2026

## License

Open source - free to use, modify, and distribute.

---

Enjoy creating beautiful Damascus patterns!
