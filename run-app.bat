@echo off
setlocal

REM Relaunch in a persistent window when double-clicked
if "%~1"=="" (
  cmd /k "%~f0" _RUN
  exit /b
)

cd /d "%~dp0"

set "NODEJS_DIR=C:\Program Files\nodejs"
if exist "%NODEJS_DIR%\npm.cmd" (
  set "PATH=%NODEJS_DIR%;%PATH%"
  set "NPM_CMD=%NODEJS_DIR%\npm.cmd"
) else (
  set "NPM_CMD=npm"
)

echo ==============================
echo  Damascus Desktop Launcher
echo ==============================
echo.

if not exist "package.json" (
  echo [ERROR] package.json not found. Run this from the project root.
  goto :END
)

if not exist "node_modules" (
  echo [INFO] node_modules not found. Installing dependencies first...
  call "%NPM_CMD%" install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    goto :END
  )
)

call "%NPM_CMD%" run dev
if errorlevel 1 (
  echo [ERROR] npm run dev failed.
)

:END
echo.
echo Launcher finished. Press any key to close.
pause >nul
endlocal
exit /b 0
