#!/usr/bin/env bash
# Run every check this skill has: structural validation, linting, static analysis, and trigger tests.
# Usage: scripts/validate_all.sh <path/to/skill-folder>
set -euo pipefail

SKILL_PATH="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Skill Validation Pipeline ==="
echo

echo "== 1. Quick Structural Validation =="
python3 "$SCRIPT_DIR/quick_validate.py" "$SKILL_PATH"
echo

echo "== 2. Comprehensive Linting =="
python3 "$SCRIPT_DIR/lint.py" "$SKILL_PATH"
echo

echo "== 3. Static Analysis =="
python3 "$SCRIPT_DIR/static_analysis.py" "$SKILL_PATH"
echo

echo "== 4. Regression Tests =="
python3 "$SCRIPT_DIR/skill_test.py" "$SKILL_PATH"
echo

echo "=== All Validations Passed ==="
