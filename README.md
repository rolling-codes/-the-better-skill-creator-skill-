# Better Skill Creator

[![Release v2.1.0](https://img.shields.io/badge/release-v2.1.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v2.1.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](#prerequisites)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A toolkit for building, checking, and packaging Claude Code skills — with a launcher
(`bsc.py`) that gives you one clear command per task.

---

## Prerequisites

- **Python 3.12 or newer** (3.12 is the tested baseline)
- **PyYAML** — `pip install pyyaml`
- **Claude Code** — installed and authenticated

Verify everything in one step:

```
python bsc.py doctor
```

Doctor reports each check, explains any failure, and tells you exactly what to run to
fix it. It makes no model calls and does not change any settings.

---

## Five-minute walkthrough

**Step 1 — Check your setup:**
```
python bsc.py doctor
```
Expected output:
```
doctor: PASSED
Fix failed prerequisites; otherwise create the release-notes example.
Report: runs/20260908T120000Z-abc12345/report.md
```

**Step 2 — Create a starter skill:**
```
python bsc.py new my-skill --example release-notes
```
This copies the `release-notes` example into a new `my-skill/` directory and renames
the skill. Expected output:
```
new: PASSED
Edit my-skill/SKILL.md, then run check on this directory.
Report: runs/20260908T120001Z-def67890/report.md
```

**Step 3 — Check your skill:**
```
python bsc.py check my-skill
```
Runs structural validation, lint, static analysis, semantic checks, and dependency
graph. Expected output (clean skill):
```
check: PASSED
Fix error findings, inspect warnings, then package or preview eval.
Report: runs/20260908T120002Z-…/report.md
```

**Step 4 — Package it:**
```
python bsc.py package my-skill
```
Creates `dist/my-skill.skill` — a zip archive ready for distribution. Expected output:
```
package: PASSED
Inspect the archive and any repairs listed below; the original skill was not modified.
Report: runs/20260908T120003Z-…/report.md
```

Each command saves a machine-readable `results.json` and a human-readable `report.md`
under a timestamped subdirectory of `runs/`.

---

## Expected outputs

| Command | Exit 0 | Exit 1 | Exit 2 |
|---|---|---|---|
| `doctor` | All checks passed | A check failed | — |
| `new` | Skill created and passes check | Input error or missing prerequisite | Checks on new skill failed |
| `check` | All checks passed | Input error | One or more checks failed |
| `eval` (no `--live`) | Preview printed | Input error | — |
| `eval --live` | All trigger checks passed | Infrastructure failure | One or more checks failed |
| `package` | Archive created | Input error | Packaging failed |

---

## Troubleshooting

**PyYAML not found:**
```
pip install -r requirements.txt
```

**Claude not authenticated or unavailable:**
Run `claude --version` to confirm Claude Code is installed. For local checks (`check`,
`package`), Claude is not needed. For `eval --live`, authenticate with `claude` before
running.

**Directory already exists (`new` command):**
Choose a different name or output directory — `bsc.py new` never overwrites an
existing directory.

Full setup instructions: [SETUP.md](SETUP.md)

---

## Commands

```
python bsc.py doctor                          # verify prerequisites
python bsc.py new NAME --example release-notes  # create a starter skill
python bsc.py check PATH                     # run all local checks
python bsc.py eval PATH [--live]             # preview or run trigger evaluation
python bsc.py package PATH                   # package into a .skill archive
python bsc.py --help                         # full option reference
```

---

## Attribution

Built on Anthropic's `skill-creator`. This fork adds wired dependency discoverability,
richer trigger tests, `--grade-transcript` for behavior grading, and the `bsc.py`
standalone launcher. See [CHANGELOG.md](CHANGELOG.md) for the full history.
