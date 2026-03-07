#!/usr/bin/env bash
# ===========================================================================
# Zero-Touch ML — Lint & Format Check
# ===========================================================================
# Runs flake8 (style) and black (formatting check) on the codebase.
# ===========================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/venv"

echo "============================================"
echo " Zero-Touch ML — Code Quality Check"
echo "============================================"

if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Virtual environment not found. Run scripts/train-model.sh first."
    exit 1
fi

source "$VENV_DIR/bin/activate"

# Ensure tools are installed
pip install --quiet flake8 black

PASS=true

# --- flake8 ---------------------------------------------------------------
echo ""
echo "🔍 Running flake8..."
if flake8 service/ model/ tests/ --max-line-length=120 --exclude=__pycache__; then
    echo "   ✅ flake8 passed"
else
    echo "   ❌ flake8 found issues"
    PASS=false
fi

# --- black -----------------------------------------------------------------
echo ""
echo "🎨 Checking formatting with black..."
if black --check service/ model/ tests/ --line-length=120; then
    echo "   ✅ black passed"
else
    echo "   ❌ black found formatting issues (run: black service/ model/ tests/)"
    PASS=false
fi

# --- Summary ---------------------------------------------------------------
echo ""
if [ "$PASS" = true ]; then
    echo "============================================"
    echo " ✅ All checks passed!"
    echo "============================================"
else
    echo "============================================"
    echo " ❌ Some checks failed — see above"
    echo "============================================"
    exit 1
fi
