#!/usr/bin/env bash
# ============================================================================
# Damascus Pattern Simulator 3D — Desktop Launcher
# ============================================================================
# Starts the Electron + Python backend app via `npm run dev`.
# Designed to be called from a .desktop shortcut or directly.
# ============================================================================

set -o pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${PROJECT_DIR}/logs/launcher_$(date +%Y%m%d_%H%M%S).log"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
log()  { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
die()  { log "FATAL: $*"; notify-send -u critical "Damascus Simulator" "$*" 2>/dev/null; exit 1; }

mkdir -p "${PROJECT_DIR}/logs"

log "=== Damascus Pattern Simulator — Launcher ==="
log "Project dir: ${PROJECT_DIR}"

# ---------------------------------------------------------------------------
# Load nvm so npm/node are on PATH
# ---------------------------------------------------------------------------
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ -s "${NVM_DIR}/nvm.sh" ]]; then
    source "${NVM_DIR}/nvm.sh"
    log "nvm loaded (node $(node --version 2>/dev/null || echo 'n/a'))"
else
    log "WARN: nvm not found at ${NVM_DIR}/nvm.sh — hoping npm is already on PATH"
fi

command -v npm >/dev/null 2>&1 || die "npm not found. Install Node.js or check your nvm setup."

# ---------------------------------------------------------------------------
# Verify project health
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR" || die "Cannot cd to ${PROJECT_DIR}"

[[ -f package.json ]] || die "package.json not found in ${PROJECT_DIR}"

if [[ ! -d node_modules ]]; then
    log "node_modules missing — running npm install..."
    npm install 2>&1 | tee -a "$LOG_FILE" || die "npm install failed"
fi

# Check Python venv
VENV_PY="${PROJECT_DIR}/.venv/bin/python"
if [[ -x "$VENV_PY" ]]; then
    log "Python venv: $($VENV_PY --version 2>&1)"
else
    log "WARN: .venv/bin/python not found — the Python engine may fail to start"
fi

# ---------------------------------------------------------------------------
# Launch
# ---------------------------------------------------------------------------
log "Starting app (npm run dev)..."
npm run dev 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}

log "App exited with code ${EXIT_CODE}"
exit $EXIT_CODE
