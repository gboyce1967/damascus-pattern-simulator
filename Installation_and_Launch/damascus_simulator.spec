# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Damascus Pattern Simulator 3D
Builds a standalone Windows executable with all dependencies bundled.
"""

block_cipher = None

# Data files to include
added_files = [
    ('steel_database.py', '.'),
    ('Hardening-tempering.txt', '.'),
    ('steel-plasticity.txt', '.'),
    ('steel-losses-during-forging.txt', '.'),
    ('ProCut-hardening-tempering.txt', '.'),
    ('ProCut-steel-plasticity.txt', '.'),
    ('ProCut-steel-losses-during-forging.txt', '.'),
]

a = Analysis(
    ['damascus_3d_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
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
