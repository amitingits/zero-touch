#!/usr/bin/env bash
# ===========================================================================
# Zero-Touch ML — Train Model Script
# ===========================================================================
# Creates a virtualenv (if needed), installs deps, and trains the model.
# ===========================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

echo "============================================"
echo " Zero-Touch ML — Model Training"
echo "============================================"

# --- Virtual environment ---------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

echo "🐍 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "📥 Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r "$PROJECT_ROOT/service/requirements.txt"

# --- Train -----------------------------------------------------------------
echo ""
echo "🧠 Training model..."
python "$PROJECT_ROOT/model/train.py"

echo ""
echo "============================================"
echo " Training complete!"
echo " Artifacts: model/artifacts/"
echo "============================================"
