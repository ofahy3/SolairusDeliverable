#!/bin/bash
# Quality Gate Check Script
# Enforces code quality standards before commits
# Based on the A+ quality practices developed for this codebase

set -e

echo "🔍 Running Quality Gate..."
echo ""

# Track if any warnings occurred
WARNINGS=0

# =================================================================
# P0: IMPORT HYGIENE (BLOCKING)
# =================================================================
echo "📦 P0: Checking import hygiene..."

# Check for broken imports (from config.xxx without package prefix)
if grep -r "from config\." --include="*.py" . 2>/dev/null | grep -v ".venv" | grep -v __pycache__ | grep -v "htmlcov"; then
    echo "❌ P0 FAIL: Broken imports found (from config.xxx without package prefix)"
    echo "   Fix: Use 'from mro_intelligence.config.xxx' instead"
    exit 1
fi

# Check for relative imports that escape the package
if grep -r "from \.\.\." --include="*.py" . 2>/dev/null | grep -v ".venv" | grep -v __pycache__; then
    echo "⚠️  P0 WARN: Deep relative imports found (consider absolute imports)"
    WARNINGS=$((WARNINGS + 1))
fi

echo "✅ P0: Import hygiene passed"
echo ""

# =================================================================
# P1: DEAD CODE DETECTION (WARNING)
# =================================================================
echo "🧹 P1: Checking for dead code..."

if command -v pyflakes &> /dev/null; then
    dead_code=$(python3 -m pyflakes mro_intelligence/ 2>&1 | grep -v "^$" || true)
    if [ -n "$dead_code" ]; then
        echo "⚠️  P1 WARN: Potential dead code found:"
        echo "$dead_code" | head -10
        WARNINGS=$((WARNINGS + 1))
    else
        echo "✅ P1: No dead code detected"
    fi
else
    echo "⚠️  P1 SKIP: pyflakes not installed (pip install pyflakes)"
fi
echo ""

# =================================================================
# P2: CONFIG ORGANIZATION (BLOCKING)
# =================================================================
echo "⚙️  P2: Checking config organization..."

# Config should be inside the package, not at root level
root_config=$(find . -maxdepth 1 -type d -name "config" 2>/dev/null | grep -v ".venv" || true)
if [ -n "$root_config" ]; then
    echo "❌ P2 FAIL: Config directory found at root level"
    echo "   Fix: Move config inside the package (e.g., mro_intelligence/config/)"
    exit 1
fi

echo "✅ P2: Config organization correct"
echo ""

# =================================================================
# P3: MODULE EXPORTS (BLOCKING)
# =================================================================
echo "📋 P3: Checking __init__.py files..."

# Find empty __init__.py files (excluding namespace packages and venv)
empty_init=$(find . -name "__init__.py" \
    -not -path "./.venv/*" \
    -not -path "./htmlcov/*" \
    -not -path "./.git/*" \
    -not -path "./build/*" \
    -not -path "./*.egg-info/*" \
    -exec sh -c 'if [ ! -s "$1" ]; then echo "$1"; fi' _ {} \;)

if [ -n "$empty_init" ]; then
    echo "❌ P3 FAIL: Empty __init__.py files found:"
    echo "$empty_init"
    echo "   Fix: Add explicit exports (__all__ = [...]) or docstrings"
    exit 1
fi

echo "✅ P3: All __init__.py files have content"
echo ""

# =================================================================
# P4: FILE SIZE LIMITS (WARNING)
# =================================================================
echo "📏 P4: Checking file sizes..."

# Files over 700 lines get a warning
large_files=$(find . -name "*.py" \
    -not -path "./.venv/*" \
    -not -path "./htmlcov/*" \
    -not -path "./.git/*" \
    -exec wc -l {} \; 2>/dev/null | awk '$1 > 700 {print}' | sort -rn)

if [ -n "$large_files" ]; then
    echo "⚠️  P4 WARN: Large files (>700 lines) - consider splitting:"
    echo "$large_files"
    WARNINGS=$((WARNINGS + 1))
else
    echo "✅ P4: All files under 700 lines"
fi
echo ""

# =================================================================
# TESTS (BLOCKING)
# =================================================================
echo "🧪 Running tests..."

if python3 -m pytest tests/ -q --tb=no 2>&1; then
    echo "✅ Tests passed"
else
    echo "❌ Tests failed"
    exit 1
fi
echo ""

# =================================================================
# SUMMARY
# =================================================================
echo "=========================================="
if [ $WARNINGS -gt 0 ]; then
    echo "✅ Quality Gate PASSED with $WARNINGS warning(s)"
else
    echo "✅ Quality Gate PASSED - A+ Quality"
fi
echo "=========================================="
