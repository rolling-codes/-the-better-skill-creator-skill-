#!/usr/bin/env bash
# Run every check this skill has: structural validation, linting, static
# analysis, then the live trigger-test suite.
#
# Usage: scripts/validate_all.sh [path/to/skill-folder]
#
# The first three checks are offline and fast. skill_test.py shells out to a
# live `claude -p` subprocess per query, so it is slow and needs Claude Code;
# that is why the pre-commit hook runs only the offline checks and this script
# is what you run before a release.
set -uo pipefail

SKILL_PATH="$(cd "${1:-.}" && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

fail=0

# lint.py and static_analysis.py import scripts.skill_ir, so they must be run
# as modules from inside the skill directory.
run_module() {
    local label="$1"; shift
    echo "== ${label} =="
    ( cd "$SKILL_PATH" && python3 -m "$@" . )
    local rc=$?
    # 0 = clean, 2 = warnings/notes only. Anything else is a real failure.
    if [ $rc -ne 0 ] && [ $rc -ne 2 ]; then
        fail=1
    fi
    echo
}

run_module "quick_validate.py" scripts.quick_validate
run_module "lint.py"           scripts.lint
run_module "static_analysis.py" scripts.static_analysis
run_module "review_gate.py"    scripts.review_gate

echo "== skill_test.py =="
if command -v claude >/dev/null 2>&1; then
    python3 "$SCRIPT_DIR/skill_test.py" "$SKILL_PATH" || fail=1
else
    echo "SKIPPED: the \`claude\` CLI is not on PATH, so trigger tests cannot run."
fi

exit $fail
