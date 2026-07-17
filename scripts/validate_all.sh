#!/usr/bin/env bash
# Run every check this skill has: structural validation + trigger tests.
# Usage: scripts/validate_all.sh <path/to/skill-folder>
set -euo pipefail

SKILL_PATH="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== quick_validate.py =="
python3 "$SCRIPT_DIR/quick_validate.py" "$SKILL_PATH"

echo
echo "== meta tests (guards guarding the guards) =="
if python3 -c "import pytest" 2>/dev/null; then
    (cd "$SKILL_PATH" && python3 -m pytest tests/meta/ -q)
else
    echo "SKIPPED: pytest not installed — the validator mutation tests did not run."
    echo "Install with: pip install pytest"
fi

echo
echo "== skill_test.py =="
python3 "$SCRIPT_DIR/skill_test.py" "$SKILL_PATH"
