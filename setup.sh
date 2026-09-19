#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="homeserverDashboard"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
SMART_HELPER="/usr/local/sbin/arduino-desk-smartctl"

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
    error "Do not run this script as root. Use a regular user with sudo privileges."
fi

# ── Sudo check ──────────────────────────────────────────────

if ! sudo -n true 2>/dev/null; then
    if [ -t 0 ]; then
        warn "This script requires sudo privileges."
        warn "You may be prompted for your password."
    else
        error "This script requires sudo privileges. Please run in an interactive terminal."
    fi
fi

# ── Detect user ─────────────────────────────────────────────

CURRENT_USER="$(whoami)"
CURRENT_GROUP="$(id -gn)"

info "Running as user: $CURRENT_USER ($CURRENT_GROUP)"
info "Project directory: $PROJECT_DIR"

# ── System packages ─────────────────────────────────────────

info "Updating package lists..."
sudo apt-get update -qq

info "Installing system dependencies..."
sudo apt-get install -y -qq \
    python3 \
    python3-venv \
    python3-pip \
    smartmontools \
    sudo \
    > /dev/null 2>&1

info "System packages installed."

# ── Python virtual environment ──────────────────────────────

if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    info "Virtual environment already exists."
fi

info "Installing Python packages..."
"$VENV_DIR/bin/pip" install --upgrade pip --quiet
"$VENV_DIR/bin/pip" install --quiet \
    fastapi \
    uvicorn \
    psutil

info "Python packages installed."

# ── SMART helper script ─────────────────────────────────────

info "Installing SMART helper script..."

sudo tee "$SMART_HELPER" > /dev/null <<'HELPER'
#!/usr/bin/env bash
exec smartctl "$@"
HELPER

sudo chmod 755 "$SMART_HELPER"

info "SMART helper installed at $SMART_HELPER"

# ── Sudoers rule for SMART helper ───────────────────────────

SUDOERS_FILE="/etc/sudoers.d/homeserver-dashboard-smart"

info "Configuring sudoers for SMART access..."

sudo tee "$SUDOERS_FILE" > /dev/null <<SUDOERS
${CURRENT_USER} ALL=(root) NOPASSWD: ${SMART_HELPER} *
SUDOERS

sudo chmod 440 "$SUDOERS_FILE"

info "Sudoers rule created."

# ── Validate sudoers ────────────────────────────────────────

if ! sudo visudo -cf "$SUDOERS_FILE" > /dev/null 2>&1; then
    error "Sudoers file has syntax errors. Removing $SUDOERS_FILE"
    sudo rm -f "$SUDOERS_FILE"
fi

# ── systemd service ─────────────────────────────────────────

info "Creating systemd service..."

sudo tee "$SERVICE_FILE" > /dev/null <<SERVICE
[Unit]
Description=Homeserver Dashboard
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${CURRENT_USER}
Group=${CURRENT_GROUP}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload

info "systemd service created."

# ── Enable and start ────────────────────────────────────────

sudo systemctl enable "$SERVICE_NAME" --quiet 2>/dev/null
sudo systemctl restart "$SERVICE_NAME"

sleep 2

if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    info "Service is running."
else
    warn "Service may not have started. Check: sudo journalctl -u $SERVICE_NAME -n 20"
fi

# ── Verify ──────────────────────────────────────────────────

echo ""
echo "========================================"
echo "  Setup Complete"
echo "========================================"
echo ""
echo "  Service:  $SERVICE_NAME"
echo "  Status:   $(sudo systemctl is-active $SERVICE_NAME)"
echo "  URL:      http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status $SERVICE_NAME"
echo "    sudo systemctl restart $SERVICE_NAME"
echo "    sudo journalctl -u $SERVICE_NAME -f"
echo ""
