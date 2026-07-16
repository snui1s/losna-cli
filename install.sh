#!/usr/bin/env bash
# Losna CLI Installer for macOS / Linux
# Usage: curl -sSL https://raw.githubusercontent.com/snui1s/losna-cli/main/install.sh | bash

set -e

INSTALL_DIR="$HOME/.losna"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/snui1s/losna-cli.git"

echo ""
echo "  Losna CLI Installer"
echo "  ==================="
echo ""

# --- Check prerequisites ---
if ! command -v git &>/dev/null; then
    echo "  [ERROR] git is required. Install it first."
    exit 1
fi

PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "  [ERROR] Python 3.10+ is required. Install from https://python.org"
    exit 1
fi

# --- Clone or update ---
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  [1/4] Updating repository..."
    cd "$INSTALL_DIR" && git pull --quiet
else
    rm -rf "$INSTALL_DIR"
    echo "  [1/4] Cloning repository..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR"
fi

# --- Create venv ---
echo "  [2/4] Creating virtual environment..."
$PYTHON_CMD -m venv "$INSTALL_DIR/.venv"

# --- Install package (editable so git pull updates take effect immediately) ---
echo "  [3/4] Installing dependencies..."
"$INSTALL_DIR/.venv/bin/pip" install --quiet -e "$INSTALL_DIR"

# --- Create wrapper command ---
echo "  [4/4] Creating losna command..."
mkdir -p "$BIN_DIR"

cat > "$BIN_DIR/losna" << 'WRAPPER'
#!/usr/bin/env bash
exec "$HOME/.losna/.venv/bin/losna" "$@"
WRAPPER
chmod +x "$BIN_DIR/losna"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    SHELL_RC=""
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi

    if [ -n "$SHELL_RC" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_RC"
        echo "  Added ~/.local/bin to PATH in $SHELL_RC"
    fi
fi

echo ""
echo "  Losna CLI installed successfully!"
echo "  Restart your terminal, then type 'losna' to start."
echo ""
