#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── Root check ──────────────────────────────────────────────

if [ "$EUID" -eq 0 ]; then
    error "Do not run this script as root."
fi

info "Project directory: $PROJECT_DIR"

# ── Check Python ────────────────────────────────────────────

if ! command -v python3 &> /dev/null; then
    error "Python3 is not installed. Install it with: sudo apt install python3 python3-venv"
fi

info "Python3 found: $(python3 --version)"

# ── Python virtual environment ──────────────────────────────

if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    info "Virtual environment already exists."
fi

# ── Install Python packages ─────────────────────────────────

info "Installing Python packages..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install --quiet \
    fastapi \
    uvicorn \
    psutil

info "Python packages installed."

# ── Verify installation ─────────────────────────────────────

info "Verifying installation..."

"$VENV_DIR/bin/python" -c "import fastapi; print(f'FastAPI: {fastapi.__version__}')" 2>/dev/null || error "FastAPI import failed"
"$VENV_DIR/bin/python" -c "import uvicorn; print(f'Uvicorn: {uvicorn.__version__}')" 2>/dev/null || error "Uvicorn import failed"
"$VENV_DIR/bin/python" -c "import psutil; print(f'psutil: {psutil.__version__}')" 2>/dev/null || error "psutil import failed"

# ── Test application import ─────────────────────────────────

info "Testing application import..."

cd "$PROJECT_DIR"
"$VENV_DIR/bin/python" -c "from app.main import app; print('Application imports OK')" 2>/dev/null || error "Application import failed"

# ── Summary ─────────────────────────────────────────────────

echo ""
echo "========================================"
echo "  Local Setup Complete"
echo "========================================"
echo ""
echo "  To run the dashboard:"
echo "    source venv/bin/activate"
echo "    uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  Or without activating venv:"
echo "    $VENV_DIR/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  Note: SMART monitoring requires smartmontools."
echo "  Install with: sudo apt install smartmontools"
echo ""
