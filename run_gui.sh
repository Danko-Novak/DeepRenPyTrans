#!/usr/bin/env bash
# ============================================================
# DeepRenPyTrans Web Console Starter (Linux)
# ============================================================

echo "============================================================"
echo "  🎮 Starting DeepRenPyTrans Web Console..."
echo "============================================================"
echo ""

# Check if python3 is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 was not found on your system!"
    echo "Please install Python 3 (e.g. sudo pacman -S python or sudo apt install python3)"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$SCRIPT_DIR/gui_server.py"

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Web console server exited with an error."
    exit 1
fi
