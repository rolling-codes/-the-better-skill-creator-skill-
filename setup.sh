#!/bin/bash
# setup.sh — skill-architect environment verification and installation

set -e

SKILL_ROOT="$HOME/.claude/skills/skill-architect"
ECC_ROOT="$HOME/.claude/rules/ecc/common"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
check_ecc_rules() {
  if [[ -f "$ECC_ROOT/development-workflow.md" ]] && [[ -f "$ECC_ROOT/git-workflow.md" ]]; then
    echo -e "${GREEN}✓${NC} ECC rules found at $ECC_ROOT"
    return 0
  else
    echo -e "${RED}✗${NC} ECC rules not found at $ECC_ROOT"
    echo "  Required: development-workflow.md, git-workflow.md"
    return 1
  fi
}

check_python() {
  if command -v python3 &> /dev/null; then
    VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python $VERSION installed"
    return 0
  else
    echo -e "${RED}✗${NC} Python 3 not found in PATH"
    return 1
  fi
}

check_scripts() {
  local scripts_missing=0
  for script in "lint.py" "dependency_graph.py" "overlap_check.py"; do
    if [[ ! -f "$SCRIPT_DIR/scripts/$script" ]]; then
      echo -e "${RED}✗${NC} Missing: scripts/$script"
      scripts_missing=1
    fi
  done

  if [[ $scripts_missing -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} All skill-architect scripts present"
    return 0
  fi
  return 1
}

check_workflows() {
  local workflows_missing=0
  for workflow in "create.md" "audit.md" "variance-check.md"; do
    if [[ ! -f "$SCRIPT_DIR/workflows/$workflow" ]]; then
      echo -e "${RED}✗${NC} Missing: workflows/$workflow"
      workflows_missing=1
    fi
  done

  if [[ $workflows_missing -eq 0 ]]; then
    echo -e "${GREEN}✓${NC} All skill-architect workflows present"
    return 0
  fi
  return 1
}

verify() {
  echo "Verifying skill-architect environment..."
  echo ""

  local all_pass=1

  check_ecc_rules || all_pass=0
  check_python || all_pass=0
  check_scripts || all_pass=0
  check_workflows || all_pass=0

  echo ""
  if [[ $all_pass -eq 1 ]]; then
    echo -e "${GREEN}All checks passed${NC}"
    return 0
  else
    echo -e "${RED}Some checks failed${NC}"
    return 1
  fi
}

install() {
  echo "Installing skill-architect..."
  echo ""

  # Verify prerequisites first
  if ! verify; then
    echo ""
    echo -e "${RED}Cannot install: prerequisites not met${NC}"
    return 1
  fi

  echo ""
  echo -e "${GREEN}✓ All prerequisites verified${NC}"
  echo "skill-architect is ready to use"
  echo ""
  echo "Next: Invoke with /skill-architect"
}

# Main
case "${1:-verify}" in
  verify)
    verify
    ;;
  install)
    install
    ;;
  *)
    echo "Usage: $0 {verify|install}"
    echo ""
    echo "  verify  — Check that skill-architect can run"
    echo "  install — Verify prerequisites and enable skill-architect"
    exit 1
    ;;
esac
