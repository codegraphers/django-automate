#!/usr/bin/env bash
# ============================================================
# check_repo_clean.sh - CI hygiene enforcement script
# 
# Fails CI if forbidden files are tracked or present in the repo.
# This ensures publishable, reproducible builds.
# ============================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "🔍 Checking repository hygiene..."

ERRORS=0

# ============================================================
# Pattern 1: Files that should NEVER be tracked in git
# ============================================================
FORBIDDEN_TRACKED=(
    "**/__pycache__/*"
    "**/*.pyc"
    "**/*.pyo"
    "site/*"
    ".coverage"
    ".pytest_cache/*"
    ".mypy_cache/*"
    ".ruff_cache/*"
    "dist/*"
    "*.egg-info/*"
    "htmlcov/*"
)

echo "  Checking for forbidden tracked files..."
for pattern in "${FORBIDDEN_TRACKED[@]}"; do
    if git ls-files --cached "$pattern" 2>/dev/null | grep -q .; then
        echo "❌ FAIL: Tracked files match forbidden pattern: $pattern"
        git ls-files --cached "$pattern" | head -5
        ERRORS=$((ERRORS + 1))
    fi
done

# ============================================================
# Pattern 2: Directories that should not exist at all
# ============================================================
FORBIDDEN_DIRS=(
    "site"
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
    "dist"
    "htmlcov"
    "__MACOSX"
)

echo "  Checking for forbidden directories..."
for dir in "${FORBIDDEN_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "❌ FAIL: Forbidden directory exists: $dir/"
        ERRORS=$((ERRORS + 1))
    fi
done

# ============================================================
# Pattern 3: Check for __pycache__ anywhere in src/
# ============================================================
echo "  Checking for __pycache__ in source tree..."
PYCACHE_COUNT=$(find src -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    echo "❌ FAIL: Found $PYCACHE_COUNT __pycache__ directories in src/"
    find src -type d -name "__pycache__" | head -5
    ERRORS=$((ERRORS + 1))
fi

# ============================================================
# Pattern 4: Check for .pyc files anywhere
# ============================================================
echo "  Checking for .pyc files..."
PYC_COUNT=$(find . -name "*.pyc" -not -path "./.git/*" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PYC_COUNT" -gt 0 ]; then
    echo "❌ FAIL: Found $PYC_COUNT .pyc files"
    find . -name "*.pyc" -not -path "./.git/*" | head -5
    ERRORS=$((ERRORS + 1))
fi

# ============================================================
# Pattern 5: Check for .coverage file
# ============================================================
echo "  Checking for coverage artifacts..."
if [ -f ".coverage" ]; then
    echo "❌ FAIL: .coverage file exists"
    ERRORS=$((ERRORS + 1))
fi

# ============================================================
# Summary
# ============================================================
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "✅ Repository hygiene check PASSED"
    exit 0
else
    echo "❌ Repository hygiene check FAILED ($ERRORS issues)"
    echo ""
    echo "To fix:"
    echo "  1. Run 'make clean' to remove build artifacts"
    echo "  2. Check .gitignore covers all patterns"
    echo "  3. Run 'git rm --cached <file>' for any tracked forbidden files"
    exit 1
fi
