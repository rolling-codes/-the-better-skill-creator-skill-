# Better Skill Creator

[![Release v3.1.0](https://img.shields.io/badge/release-v3.1.0-blue.svg)](https://github.com/rolling-codes/better-skill-creator/releases/tag/v3.1.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](#prerequisites)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A toolkit for building, checking, and packaging Claude Code skills — with a launcher
(`bsc.py`) that gives you one clear command per task.


---


## Why this exists

Most Claude Code skills are written by feel: the description is guessed at, the
instructions are copy-pasted from examples, and whether it actually triggers
correctly is never measured. Better Skill Creator fixes that with a structured
pipeline and evidence-backed defaults.


### Skills fail in predictable ways

**Over-specification.** Anthropic's guidance for Fable 5+ models is explicit:
overly detailed instruction files degrade output. Rigid step sequences and
ALL-CAPS rules consume reasoning budget the model should spend on the task.

```
# What most skills look like
Step 1: Run quick_validate with the --strict flag. If it exits 0, proceed to Step 2.
NEVER skip this step. ALWAYS address every warning.

# What actually works
Validate before eval. Fix blocking issues; warnings are informational.
```

**Untested descriptions.** A skill's `description` field is what decides whether
Claude invokes it at all. Without measurement, optimizing it is guesswork.
`run_loop` tests each candidate description against 20 real queries — including
near-misses that share keywords but shouldn't trigger — and picks the winner by
held-out test score, not train score.

**Hedged instructions.** These phrasings silently make your rules optional:

```
"Try to be concise."      →  suggestion
"If possible, use tables" →  suggestion
"Be concise."             →  rule
```

The writing phase now flags `try to`, `if possible`, `where relevant`, `you may`,
`consider`, and `when appropriate` as compliance escape hatches.


### The quality pipeline

Six gates run before a skill can be packaged:

| Gate | What it catches |
|---|---|
| Structure | Missing frontmatter fields, invalid schema |
| Lint | Hedged instructions, orphaned references, unwired dependencies |
| Static analysis | Dead links, unreachable files, unused tools |
| Semantic | Vague descriptions, over-specification, trigger ambiguity |
| Dependency | Circular imports, missing scripts |
| Review | Independent multi-agent adversarial review |

All six must pass at error level before `package` completes. Warnings are
surfaced but non-blocking.


### 2026 model guidance built in

- `budget_tokens` returns HTTP 400 on Claude 4.7+ — replaced with `output_config.effort`
- Fable 5.1 / Opus 5.5 / Sonnet 5.5 context windows: 1M tokens, 128K max output
- Model routing table (Fable 5.1 for architecture, Sonnet 5.5 for execution, Haiku 4.5 for eval loops)
- Prompt injection defenses: session-salted delimiters, dual-LLM gatekeeper, compaction trust boundary


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
