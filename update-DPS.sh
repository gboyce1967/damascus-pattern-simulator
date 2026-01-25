#!/bin/bash
#
# Damascus Pattern Simulator (DPS) - Update Script
# Updates the application to the latest version from GitHub
#

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[*]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo "=========================================="
echo "  Damascus Pattern Simulator - Update"
echo "=========================================="
echo

# Change to script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || {
    print_error "Could not change to script directory: $SCRIPT_DIR"
    exit 1
}

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    print_error "This directory is not a git repository."
    echo
    print_warning "You installed from a ZIP file (not git clone)."
    echo
    echo "Automatic updates are only available for git installations."
    echo
    echo "To enable automatic updates:"
    echo "  1. Remove current installation"
    echo "  2. Install via git clone:"
    echo "     git clone https://github.com/gboyce1967/damascus-pattern-simulator.git"
    echo "  3. Run: cd damascus-pattern-simulator && ./install-DPS.sh"
    echo
    echo "Or manually update:"
    echo "  Download: https://github.com/gboyce1967/damascus-pattern-simulator/archive/refs/heads/main.zip"
    echo
    exit 1
fi

print_status "Checking for updates..."

# Fetch latest changes
git fetch origin main 2>&1

# Check if we're behind
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u})

if [ "$LOCAL" = "$REMOTE" ]; then
    print_status "Already up to date!"
    echo
    CURRENT_VERSION=$(git log -1 --pretty=format:"%s")
    echo "Current version: $CURRENT_VERSION"
    exit 0
fi

print_warning "Updates available!"
echo
echo "Current version:"
git log -1 --pretty=format:"  %s (%h)" HEAD
echo
echo
echo "Latest version:"
git log -1 --pretty=format:"  %s (%h)" origin/main
echo
echo

read -p "Do you want to update? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled."
    exit 0
fi

print_status "Updating to latest version..."

# Pull latest changes
if git pull origin main; then
    print_status "Update complete!"
    echo
    echo "New version:"
    git log -1 --pretty=format:"  %s (%h)" HEAD
    echo
    echo
    print_status "Restart the application to use the new version."
else
    print_error "Update failed!"
    echo "Please check for conflicts and try again."
    exit 1
fi

echo
