#!/bin/bash
#
# Damascus Pattern Simulator - RedHat/Fedora/CentOS Installer
# Installs all dependencies and sets up the application
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

# Detect package manager (dnf for Fedora, yum for older RHEL/CentOS)
detect_package_manager() {
    if command -v dnf &> /dev/null; then
        PKG_MGR="dnf"
    elif command -v yum &> /dev/null; then
        PKG_MGR="yum"
    else
        print_error "Neither dnf nor yum package manager found!"
        exit 1
    fi
    print_status "Using package manager: $PKG_MGR"
}

# Check if running on RedHat-based system
check_system() {
    if [ ! -f /etc/redhat-release ] && [ ! -f /etc/fedora-release ]; then
        print_error "This installer is for RedHat-based systems (Fedora, RHEL, CentOS, etc.)"
        print_warning "For Debian-based systems, use install-debian.sh"
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
    echo "  RedHat/Fedora/CentOS"
    echo "=========================================="
    echo

    check_system
    check_root
    detect_package_manager

    print_status "Checking Python installation..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed!"
        print_status "Installing Python 3..."
        sudo $PKG_MGR install -y python3 python3-pip python3-tkinter
    else
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python $PYTHON_VERSION found"
    fi

    print_status "Checking pip installation..."
    if ! command -v pip3 &> /dev/null; then
        print_status "Installing pip..."
        sudo $PKG_MGR install -y python3-pip
    fi

    print_status "Installing system dependencies..."
    sudo $PKG_MGR install -y \
        python3-pillow \
        python3-numpy \
        python3-tkinter \
        python3-gobject \
        gtk3 \
        gobject-introspection

    print_status "Installing Python packages via pip..."
    pip3 install --user pillow numpy

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
    echo "To uninstall, run: ./uninstall-redhat.sh"
    echo
}

# Run main installation
main
