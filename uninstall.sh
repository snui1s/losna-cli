#!/usr/bin/env bash
# Losna CLI Uninstaller for macOS / Linux
# Usage: curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/uninstall.sh | bash

set -e

INSTALL_DIR="$HOME/.losna"
BIN_FILE="$HOME/.local/bin/losna"

echo ""
echo "  Losna CLI Uninstaller"
echo "  ====================="
echo ""

# --- Remove installation directory ---
if [ -d "$INSTALL_DIR" ]; then
    echo "  [1/2] Removing $INSTALL_DIR ..."
    rm -rf "$INSTALL_DIR"
else
    echo "  [1/2] No installation found at $INSTALL_DIR"
fi

# --- Remove command from PATH ---
if [ -f "$BIN_FILE" ]; then
    echo "  [2/2] Removing losna command..."
    rm -f "$BIN_FILE"
else
    echo "  [2/2] No losna command found"
fi

echo ""
echo "  Losna CLI uninstalled successfully."
echo ""
