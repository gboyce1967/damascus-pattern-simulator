# Damascus Desktop Dependencies and Setup

This project uses two dependency systems:

- Node/Electron dependencies are in `package.json` and installed to `node_modules/`.
- Python dependencies are in `python/requirements.txt` and installed into `.venv/`.

`node_modules/` and `out/` are generated folders. They should not be committed to Git.

## Prerequisites

- Windows 10/11 (project scripts currently target Windows)
- Node.js 18+ (includes `npm`)
- Python 3.12 (x64) with `py` launcher

## One-command install (Windows)

From the project root:

```bat
install-deps.cmd
```

This script:

- creates `.venv` with Python 3.12
- installs `python/requirements.txt`
- runs an Open3D import smoke test
- runs `npm install`

## Manual install (Windows)

From the project root:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.venv\Scripts\python.exe -m pip install -r python\requirements.txt
npm install
```

## Run the app

Use either:

```bat
run-app.bat
```

or:

```bat
npm run dev
```

## Dependency manifests

- Node dependencies: `package.json` + `package-lock.json`
- Python dependencies: `python/requirements.txt`

## Generated folders

- `node_modules/`: created by `npm install`
- `out/`: created by Electron/Vite build/dev pipeline
- `.venv/`: Python virtual environment

These are expected local artifacts and are ignored by `.gitignore`.
