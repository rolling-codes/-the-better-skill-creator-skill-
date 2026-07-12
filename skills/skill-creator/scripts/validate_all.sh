#!/usr/bin/env bash
# Run every check this skill has: structural validation + trigger tests.
# Usage: scripts/validate_all.sh <path/to/skill-folder>
set -euo pipefail

SKILL_PATH="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== quick_validate.py =="
python3 "$SCRIPT_DIR/quick_validate.py" "$SKILL_PATH"

echo
echo "== skill_test.py =="
python3 "$SCRIPT_DIR/skill_test.py" "$SKILL_PATH"
