#!/bin/bash
#
# Damascus Pattern Simulator (DPS) - Linux Installer
# Installs all dependencies and sets up the application
# Compatible with Debian/Ubuntu/Mint and derivatives
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running on Debian-based system
check_system() {
    if [ ! -f /etc/debian_version ]; then
        print_error "This installer is for Debian-based systems (Ubuntu, Debian, Mint, etc.)"
        print_warning "Other distributions may require manual installation - see README.md"
        exit 1
    fi
}

# Check if running as root for system packages
check_root() {
    if [ "$EUID" -eq 0 ]; then
        print_warning "Running as root. This is not recommended."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Main installation
main() {
    echo "=========================================="
    echo "  Damascus Pattern Simulator Installer"
    echo "  DPS v1.2"
    echo "=========================================="
    echo

    check_system
    check_root

    print_status "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        print_status "Installing Python 3..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-tk
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    fi

    print_status "Checking pip installation..."
    if ! command -v pip3 &> /dev/null; then
        print_status "Installing pip..."
        sudo apt install -y python3-pip
    fi

    print_status "Installing system dependencies..."
    sudo apt update
    sudo apt install -y \
        python3-pil \
        python3-numpy \
        python3-tk \
        python3-gi \
        gir1.2-gtk-3.0 \
        libgtk-3-0

    print_status "Python packages installed via system package manager"

    print_status "Making damascus_simulator.py executable..."
    chmod +x damascus_simulator.py

    print_status "Creating desktop entry..."
    DESKTOP_FILE="$HOME/.local/share/applications/damascus-simulator.desktop"
    mkdir -p "$HOME/.local/share/applications"
    
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Damascus Pattern Simulator
Comment=Simulate Damascus steel patterns with transformations
Exec=$PWD/damascus_simulator.py
Icon=applications-graphics
Terminal=false
Categories=Graphics;2DGraphics;
Keywords=damascus;steel;pattern;forge;metalwork;
EOF

    print_status "Updating desktop database..."
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    fi

    echo
    echo "=========================================="
    print_status "Installation complete!"
    echo "=========================================="
    echo
    echo "You can now run the simulator by:"
    echo "  1. Typing: ./damascus_simulator.py"
    echo "  2. Searching for 'Damascus Pattern Simulator' in your applications menu"
    echo
    echo "To uninstall, run: ./uninstall-DPS.sh"
    echo
}

# Run main installation
main
