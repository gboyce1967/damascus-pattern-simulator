# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Damascus Pattern Simulator 3D
Builds a standalone Windows executable with all dependencies bundled.
"""
from pathlib import Path

block_cipher = None

SPEC_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SPEC_DIR.parent

# Data files to include
added_files = [
    (str(PROJECT_ROOT / 'data' / '__init__.py'), 'data'),
    (str(PROJECT_ROOT / 'data' / 'steel_database.py'), 'data'),
    (str(PROJECT_ROOT / 'data' / 'Hardening-tempering.txt'), 'data'),
    (str(PROJECT_ROOT / 'data' / 'steel-plasticity.txt'), 'data'),
    (str(PROJECT_ROOT / 'data' / 'steel-losses-during-forging.txt'), 'data'),
    (str(PROJECT_ROOT / 'Staging' / 'ProCut-hardening-tempering.txt'), 'Staging'),
    (str(PROJECT_ROOT / 'Staging' / 'ProCut-steel-plasticity.txt'), 'Staging'),
    (str(PROJECT_ROOT / 'Staging' / 'ProCut-steel-losses-during-forging.txt'), 'Staging'),
]

a = Analysis(
    [str(PROJECT_ROOT / 'damascus_3d_gui.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'data.steel_database',
        'matplotlib.backends.backend_tkagg',
        'PIL._tkinter_finder',
        'open3d',
        'numpy',
        'scipy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DamascusSimulator3D',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application, no console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon file path here if you create one
)
