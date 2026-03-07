#!/usr/bin/env bash
# ===========================================================================
# Zero-Touch ML — Run Locally
# ===========================================================================
# Starts the Flask inference API on localhost:5000 for development.
# ===========================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

echo "============================================"
echo " Zero-Touch ML — Local Development Server"
echo "============================================"

# --- Check venv ------------------------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found. Run scripts/train-model.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# --- Check model artifact --------------------------------------------------
if [ ! -f "$PROJECT_ROOT/model/artifacts/model.pkl" ]; then
    echo "⚠️  Model not found. Training now..."
    python "$PROJECT_ROOT/model/train.py"
fi

# --- Run Flask dev server --------------------------------------------------
echo ""
echo "🚀 Starting Flask development server on http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

export FLASK_APP="$PROJECT_ROOT/service/app.py"
export FLASK_ENV=development

python "$PROJECT_ROOT/service/app.py"
