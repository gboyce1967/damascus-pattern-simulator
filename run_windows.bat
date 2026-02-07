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

REM Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo.
    echo Please run Installation_and_Launch\install_windows.bat first to install dependencies.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if main GUI file exists
if not exist damascus_3d_gui.py (
    echo [ERROR] damascus_3d_gui.py not found!
    echo.
    echo Make sure you're running this from the project directory.
    echo.
    pause
    exit /b 1
)

REM Launch the application
echo.
echo Starting Damascus Pattern Simulator...
echo.
python damascus_3d_gui.py

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
