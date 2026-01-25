#!/bin/bash
#
# Damascus Pattern Simulator (DPS) - Linux Uninstaller
# Compatible with Debian/Ubuntu/Mint and derivatives
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

# Python packages are installed via system package manager (apt)
# They will remain on the system unless manually removed

echo
print_status "Uninstall complete!"
echo
echo "The damascus_simulator.py file remains in: $PWD"
echo "To remove it manually: rm damascus_simulator.py"
echo
echo "To reinstall system packages that were installed:"
echo "  sudo apt remove python3-pil python3-numpy python3-tk python3-gi gir1.2-gtk-3.0"
echo
