@echo off
setlocal enabledelayedexpansion

REM ==========================================================
REM Damascus Desktop - Windows Installer (stays open)
REM - Uses Python 3.12 for .venv (required for Open3D)
REM - Installs pip deps (python\requirements.txt)
REM - Installs npm deps (package.json)
REM - Writes install-log.txt
REM ==========================================================

REM --- Relaunch in a persistent window if double-clicked ---
if "%~1"=="" (
  cmd /k "%~f0" _RUN
  exit /b
)

cd /d "%~dp0"

set LOGFILE=%CD%\install-log.txt
echo ===================================== > "%LOGFILE%"
echo Damascus Desktop Installer - %DATE% %TIME% >> "%LOGFILE%"
echo ===================================== >> "%LOGFILE%"

echo.
echo ==============================
echo  Damascus Desktop Installer
echo ==============================
echo Log: "%LOGFILE%"
echo.

call :CHECK_TOOLS || goto :END
call :SELECT_PY312 || goto :END
call :ENSURE_FILES || goto :END
call :CREATE_VENV || goto :END
call :PIP_INSTALL || goto :END
call :SMOKE_TEST_OPEN3D || goto :END
call :NPM_INSTALL || goto :END

echo.
echo ==============================
echo  DONE!
echo ==============================
echo Next: npm run dev
echo.

goto :END

:CHECK_TOOLS
echo [CHECK] npm...
where npm >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js 18+ and ensure it's on PATH.
  echo [ERROR] npm not found >> "%LOGFILE%"
  exit /b 1
)

echo [CHECK] py launcher...
where py >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] py launcher not found. Reinstall Python 3.12 from python.org with launcher enabled.
  echo [ERROR] py not found >> "%LOGFILE%"
  exit /b 1
)

echo [CHECK] node/npm versions...
node -v >> "%LOGFILE%" 2>&1
npm -v  >> "%LOGFILE%" 2>&1

exit /b 0

:SELECT_PY312
echo [CHECK] Python 3.12 via launcher (py -3.12)...
py -3.12 -c "import sys,platform; print(sys.executable); print(sys.version); print(platform.architecture())" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.12 is NOT available via "py -3.12".
  echo         Run in PowerShell:  py -0p
  echo         Then reinstall Python 3.12 (x64) with the launcher enabled.
  echo [ERROR] py -3.12 failed >> "%LOGFILE%"
  exit /b 1
)

REM Capture venv python command (we will use py -3.12 directly)
set PY_CMD=py -3.12
exit /b 0

:ENSURE_FILES
if not exist "python\requirements.txt" (
  echo [ERROR] Missing python\requirements.txt
  echo [ERROR] Missing python\requirements.txt >> "%LOGFILE%"
  exit /b 1
)
if not exist "package.json" (
  echo [ERROR] Missing package.json
  echo [ERROR] Missing package.json >> "%LOGFILE%"
  exit /b 1
)
exit /b 0

:CREATE_VENV
echo [1/4] Creating/Updating .venv with Python 3.12...
if exist ".venv" (
  echo      .venv exists - reusing.
  echo .venv exists - reusing >> "%LOGFILE%"
) else (
  %PY_CMD% -m venv .venv >> "%LOGFILE%" 2>&1
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv. See install-log.txt
    exit /b 1
  )
)

set VENV_PY=%CD%\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
  echo [ERROR] Could not find venv python at: %VENV_PY%
  echo [ERROR] venv python missing >> "%LOGFILE%"
  exit /b 1
)

echo      Upgrading pip/setuptools/wheel...
"%VENV_PY%" -m pip install --upgrade pip setuptools wheel >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] Failed to upgrade pip tooling. See install-log.txt
  exit /b 1
)

exit /b 0

:PIP_INSTALL
echo [2/4] Installing Python dependencies (python\requirements.txt)...
"%VENV_PY%" -m pip install -r "python\requirements.txt" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] pip install failed. See install-log.txt
  echo         Most common causes:
  echo         - Python is not x64
  echo         - Open3D wheel mismatch
  exit /b 1
)
exit /b 0

:SMOKE_TEST_OPEN3D
echo [3/4] Smoke test: importing Open3D...
"%VENV_PY%" -c "import open3d as o3d; print('Open3D:', o3d.__version__)" >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] Open3D import failed (after install). See install-log.txt
  echo         Tip: run this for more detail:
  echo         .venv\Scripts\python.exe -W default -c "import open3d as o3d"
  exit /b 1
)
exit /b 0

:NPM_INSTALL
echo [4/4] Installing Node dependencies (npm install)...
call npm install >> "%LOGFILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] npm install failed. See install-log.txt
  exit /b 1
)
exit /b 0

:END
echo.
echo Installer finished. Press any key to close.
pause >nul
endlocal
exit /b 0
