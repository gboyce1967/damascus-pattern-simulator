#!/bin/bash
#
# Damascus Pattern Simulator - RedHat/Fedora Uninstaller
#

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Detect package manager
if command -v dnf &> /dev/null; then
    PKG_MGR="dnf"
elif command -v yum &> /dev/null; then
    PKG_MGR="yum"
else
    PKG_MGR="dnf/yum"
fi

echo "=========================================="
echo "  Damascus Pattern Simulator Uninstaller"
echo "=========================================="
echo

print_warning "This will remove the desktop entry and user-installed Python packages."
print_warning "System packages will NOT be removed."
echo
read -p "Continue with uninstall? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

print_status "Removing desktop entry..."
rm -f "$HOME/.local/share/applications/damascus-simulator.desktop"

print_status "Updating desktop database..."
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

print_status "Removing user-installed Python packages..."
pip3 uninstall -y pillow numpy 2>/dev/null || true

echo
print_status "Uninstall complete!"
echo
echo "The damascus_simulator.py file remains in: $PWD"
echo "To remove it manually: rm damascus_simulator.py"
echo
echo "To remove system packages that were installed:"
echo "  sudo $PKG_MGR remove python3-pillow python3-numpy python3-tkinter python3-gobject gtk3"
echo
