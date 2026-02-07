# Damascus Pattern Simulator 3D - Windows Installation Guide

## Quick Start (3 Easy Steps)

### Prerequisites
- **Python 3.8 or higher** must be installed
  - Download from: https://www.python.org/downloads/
  - ⚠️ **IMPORTANT:** Check "Add Python to PATH" during installation!

### Step 1: Install Dependencies
Double-click **`install_windows.bat`**

This will:
- ✅ Check if Python is installed
- ✅ Create a virtual environment
- ✅ Install all required packages (numpy, matplotlib, open3d, etc.)

The installation may take 5-10 minutes depending on your internet speed.

### Step 2: Run the Application
Double-click **`run_windows.bat`**

The Damascus Pattern Simulator 3D will launch!

---

## Detailed Information

### What Gets Installed?
The installer creates a virtual environment (`venv` folder) and installs:
- **numpy** - Numerical computing
- **scipy** - Scientific computing  
- **matplotlib** - 2D plotting and visualization
- **open3d** - 3D mesh processing and visualization
- **Pillow** - Image processing

### Troubleshooting

#### "Python is not installed or not in PATH!"
**Solution:** 
1. Download Python from https://www.python.org/downloads/
2. During installation, **check the box** "Add Python to PATH"
3. Restart your computer
4. Run `install_windows.bat` again

#### "Module not found" errors when running
**Solution:**
1. Delete the `venv` folder
2. Run `install_windows.bat` again
3. Try running `run_windows.bat`

#### Application won't start
**Solution:**
1. Open Command Prompt in the project folder
2. Run: `venv\Scripts\activate.bat`
3. Run: `python damascus_3d_gui.py`
4. Look for error messages and report them

### Manual Installation (Alternative)

If the batch files don't work, you can install manually:

```cmd
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate.bat

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python damascus_3d_gui.py
```

---

## System Requirements

### Minimum:
- Windows 10 or 11
- Python 3.8+
- 4 GB RAM
- 500 MB free disk space
- Graphics card with OpenGL support

### Recommended:
- Windows 11
- Python 3.10+
- 8 GB RAM
- 1 GB free disk space
- Dedicated graphics card

---

## Features

Once installed, you can:
- 📐 Create Damascus billets with custom dimensions and layer counts
- 🔨 Apply forging operations (cutting, twisting, stacking)
- 🎨 Visualize 3D patterns in real-time
- 📊 View cross-sections at any Z position
- 🔬 Reference steel properties (heat treatment, forging characteristics)
- ➕ Add custom steel data to the database
- 💾 Export 3D models (.obj, .stl) and images

---

## Uninstallation

To remove the Damascus Pattern Simulator:
1. Delete the entire project folder
2. (Optional) Uninstall Python if not needed for other projects

The application doesn't modify system files or registry.

---

## Support

For issues or questions:
- Email: devsupport@grayworkscrafts.com
- GitHub: https://github.com/gboyce1967/damascus-pattern-simulator

---

## License

Damascus Pattern Simulator 3D
Copyright © 2026 Gray Works Crafts

---

*Last updated: February 5, 2026*
