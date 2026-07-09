# Skill-Architect Setup

## Prerequisites

Skill-architect requires the following to be present in your Claude Code environment:

### 1. ECC Rules (Enterprise Claude Code)
Location: `~/.claude/rules/ecc/common/`

Required files:
- `development-workflow.md` — defines the feature development pipeline
- `git-workflow.md` — defines commit and PR conventions
- `testing.md` — defines test coverage requirements
- `code-review.md` — defines code review standards

**Check**: Run `setup.sh verify` to confirm these exist.

### 2. Claude Code Installation
- Claude Code CLI installed
- `~/.claude/skills/` directory exists and is writable
- `~/.claude/` directory initialized with git or configuration

**Check**: Run `gh --version` and `ls ~/.claude/skills/`

### 3. Python (for skill-architect's tooling)
- Python 3.8+
- No external packages required (scripts use only stdlib)

**Check**: Run `python3 --version`

## Installation

### Automatic (Recommended)
```bash
cd ~/.claude/skills/skill-architect
bash setup.sh install
```

This will:
1. Verify all prerequisites
2. Copy workflow and script files into place
3. Create a memory checkpoint
4. Output verification report

### Manual
1. Clone skill-architect to `~/.claude/skills/skill-architect/`
2. Verify prerequisites exist (see above)
3. Run `bash setup.sh verify` to confirm

## Verification

After installation:
```bash
bash setup.sh verify
```

Expected output:
```
✓ ECC rules found at ~/.claude/rules/ecc/common/
✓ Python 3.x installed
✓ skill-architect workflows present
✓ skill-architect scripts present
✓ All checks passed
```

## Troubleshooting

**"ECC rules not found"**
- Install ECC rules to `~/.claude/rules/ecc/common/`
- Confirm `development-workflow.md` and `git-workflow.md` exist

**"Python not found"**
- Ensure Python 3.8+ is in your PATH
- On Windows: run `python --version` or `py --version`

**"skill-architect scripts not found"**
- Confirm `scripts/` directory is present and has `lint.py`, `dependency_graph.py`, `overlap_check.py`
- If missing, re-clone skill-architect

## Using Skill-Architect

Once installed, invoke it:
```
/skill-architect
```

Mode options:
- `create` — build a new SKILL.md
- `audit` — review an existing SKILL.md
- `variance-check` — test a skill's triggering accuracy

For detailed usage, see `SKILL.md` or run `skill-architect` mode without arguments.
