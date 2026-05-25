# DEVNOTES: Python Engine Dependency Fix
**Date:** 2026-05-03

## Problem
The Electron app failed on startup with:
```
Error: Python engine did not become healthy in time.
```

The Python backend (uvicorn + FastAPI) could not start because the `.venv` (Python 3.13.7) had no packages installed — `pip` itself was missing, and none of the required dependencies (`open3d`, `fastapi`, `uvicorn`, etc.) were present.

## Root Cause
The `.venv` was created but never had its dependencies installed. Additionally, the `open3d` PyPI release (v0.19.0) only ships wheels for Python ≤3.12. Since our venv uses Python 3.13, the standard `pip install open3d` fails.

## Fix Applied
1. Bootstrapped `pip` into the existing venv via `python -m ensurepip --upgrade`.
2. Installed the **Open3D development wheel** for Python 3.13 from the Open3D project's latest dev release:
   ```
   pip install -U -f https://www.open3d.org/docs/latest/getting_started.html --only-binary open3d open3d
   ```
   This pulled `open3d-0.19.0-cp313-cp313-manylinux_2_35_x86_64.whl` (~833 MB).
3. Installed remaining backend dependencies: `fastapi`, `uvicorn`, `pydantic`.
4. Created `requirements.txt` documenting all needed packages.

## Verified
- `uvicorn python.api:app` starts successfully.
- `/health` endpoint returns `{"ok":true,"engine":"damascus-python"}`.
- `npm run dev` should now work (Electron will find and start the Python engine).

## Notes
- Once Open3D publishes a stable Python 3.13 wheel to PyPI, the special `-f` flag for the dev wheel URL can be dropped.
- The full installed package list is in `requirements.txt`.
