@echo off
setlocal EnableDelayedExpansion
REM ============================================================
REM Damascus Pattern Simulator 3D - Windows Installer
REM ============================================================
REM This script installs all required Python dependencies
REM for running the Damascus Pattern Simulator on Windows.
REM
REM Requirements: Python 3.12.x
REM ============================================================

echo.
echo ============================================================
echo  Damascus Pattern Simulator 3D - Windows Installer
echo ============================================================
echo.

REM Resolve absolute paths
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
set "REQUIREMENTS_FILE=%SCRIPT_DIR%requirements.txt"

REM Always run installation from the project root
cd /d "%PROJECT_ROOT%"

set "PYTHON_CMD="

REM Prefer exact Python 3.12 via Python Launcher to avoid 3.13 for Open3D
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_CMD=py -3.12"
)

REM Fallback: allow python.exe only if it is exactly 3.12
if "%PYTHON_CMD%"=="" (
    python --version >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_CMD=python"
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [ERROR] Python 3.12 is required. Open3D does not support Python 3.13 for this project.
    echo.
    echo Install Python 3.12 from:
    echo https://www.python.org/downloads/
    echo.
    echo Recommended option during install: "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('%PYTHON_CMD% --version 2^>^&1') do set PYVER=%%i
echo Detected Python version: %PYVER%
echo.

%PYTHON_CMD% -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
if errorlevel 1 (
    echo [ERROR] Python 3.12 is required. Detected: %PYVER%
    echo.
    pause
    exit /b 1
)

echo [OK] Using Python 3.12
echo.

REM Create virtual environment (optional but recommended)
echo Creating virtual environment...
if exist venv (
    if not exist venv\Scripts\python.exe (
        set "ERROR_MSG=Existing venv is missing venv\\Scripts\\python.exe"
        goto :fail
    )
    venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)"
    if errorlevel 1 (
        set "ERROR_MSG=Existing venv is not Python 3.12. Delete the venv folder and run this installer again."
        goto :fail
    )
    echo [SKIP] Virtual environment already exists and is Python 3.12
) else (
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        set "ERROR_MSG=Failed to create virtual environment."
        goto :fail
    )
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
if not exist venv\Scripts\activate.bat (
    set "ERROR_MSG=Virtual environment activation script not found: venv\\Scripts\\activate.bat"
    goto :fail
)
call venv\Scripts\activate.bat
if errorlevel 1 (
    set "ERROR_MSG=Failed to activate virtual environment."
    goto :fail
)
echo.

REM Upgrade package tooling first
echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    set "ERROR_MSG=Failed to upgrade pip/setuptools/wheel."
    goto :fail
)
echo.

REM Install dependencies
echo ============================================================
echo  Installing Required Dependencies
echo ============================================================
echo.
echo This may take several minutes...
echo.

REM Install from Installation_and_Launch\requirements.txt if it exists
if exist "%REQUIREMENTS_FILE%" (
    echo Installing from %REQUIREMENTS_FILE%...
    pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 (
        set "ERROR_MSG=Failed to install dependencies from %REQUIREMENTS_FILE%."
        goto :fail
    )
) else (
    echo [WARN] %REQUIREMENTS_FILE% not found. Installing core dependencies directly...
    pip install numpy scipy matplotlib Pillow open3d
    if errorlevel 1 (
        set "ERROR_MSG=Failed to install core dependencies."
        goto :fail
    )
)

REM Needed to build executable from damascus_simulator.spec
echo Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    set "ERROR_MSG=Failed to install PyInstaller."
    goto :fail
)

REM Sanity check imports so setup fails early if something is missing
echo Verifying installed modules...
python -c "import numpy, scipy, matplotlib, PIL, open3d; import tkinter; print('All required modules imported successfully.')"
if errorlevel 1 (
    set "ERROR_MSG=Dependency verification failed (one or more imports did not load)."
    goto :fail
)

echo.
echo ============================================================
echo  Installation Complete!
echo ============================================================
echo.
echo To run the Damascus Pattern Simulator:
echo   1. Run: run_windows.bat
echo   OR
echo   2. Manually activate venv: venv\Scripts\activate.bat
echo   3. Then run: python damascus_3d_gui.py
echo.
echo ============================================================
pause
exit /b 0

:fail
echo.
echo [ERROR] %ERROR_MSG%
echo.
pause
exit /b 1
