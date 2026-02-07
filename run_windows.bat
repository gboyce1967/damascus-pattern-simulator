@echo off
REM ============================================================
REM Damascus Pattern Simulator 3D - Windows Launcher
REM ============================================================
REM Launches the Damascus Pattern Simulator application
REM ============================================================

echo.
echo ============================================================
echo  Damascus Pattern Simulator 3D
echo ============================================================
echo.

REM Always run from project root (directory containing this script)
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"
set "VENV_PYTHON=%SCRIPT_DIR%venv\Scripts\python.exe"

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run Installation_and_Launch\install_windows.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Use venv interpreter directly (robust if project folder is renamed/moved)
if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment Python not found!
    echo.
    echo Expected: %VENV_PYTHON%
    echo.
    echo Please run Installation_and_Launch\install_windows.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

echo Using virtual environment interpreter...

REM Check if main GUI file exists
if not exist damascus_3d_gui.py (
    echo [ERROR] damascus_3d_gui.py not found!
    echo.
    echo Make sure you're running this from the project directory.
    echo.
    pause
    exit /b 1
)

REM Verify dependencies before launching to avoid raw traceback
"%VENV_PYTHON%" -c "import numpy, scipy, matplotlib, PIL, vispy, open3d; import tkinter" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Missing Python dependencies in virtual environment.
    echo.
    echo Run Installation_and_Launch\install_windows.bat to install or repair dependencies.
    echo.
    echo If you installed packages manually, make sure they were installed into: venv\Scripts\python.exe
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo.
echo Starting Damascus Pattern Simulator...
echo.
"%VENV_PYTHON%" damascus_3d_gui.py

REM If there's an error, keep window open
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  Application exited with an error
    echo ============================================================
    echo.
    echo Check the error messages above for details.
    echo.
    pause
)