# Better Skill Creator

[![Release v2.1.0](https://img.shields.io/badge/release-v2.1.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v2.1.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-green.svg)](#prerequisites)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A toolkit for building, checking, and packaging Claude Code skills — with a launcher
(`bsc.py`) that gives you one clear command per task.

---

## What makes it better

Most skill tooling stops at packaging. This one measures whether your skill actually
works — and keeps improving it until it does.

**Trigger evaluation that runs for real.** `bsc eval --live` spawns `claude -p` with a
synthetic command file, measures the trigger rate across N parallel runs, and
classifies every outcome: `TRIGGERED`, `NOT_TRIGGERED`, `TIMEOUT`,
`AUTHENTICATION`, `SUBPROCESS_CRASH`, or `PARSING`. Infrastructure failures are
separated from trigger failures so you know whether Claude didn't route to your skill
or whether the eval itself broke. A failed run is never counted as a pass.

**Description optimization loop.** Once you have trigger cases, `run_loop.py` runs
eval → improve → eval until all cases pass or you hit the iteration cap. It uses a
stratified train/test split to prevent overfitting, strips test scores from the
improvement prompt so the model can't see held-out signal, and stops immediately when
the eval infrastructure fails rather than optimizing on noise. The best description
across all iterations — by test score — is returned, not just the last one.

**Six-gate quality pipeline.** `bsc check` and `bsc package` run lint → semantic
analysis → dependency graph → auto-repair → independent review → score in sequence.
Every finding has a severity. Error-severity findings block packaging. Auto-repair runs
on a copy of your skill, never your original, and every file changed by repair is
reported.

**Behavior grading.** Beyond trigger rate, `bsc eval --grade-transcript` runs your
`expected_behavior.yaml` cases through an LLM grader and returns a pass/incomplete/fail
verdict per expectation — with evidence. Incomplete grading (wrong count, empty
evidence, duplicate rows) is flagged as a grader failure rather than silently passing.

**Independent review gate.** For substantial skill work, a multi-agent adversarial
review records findings and dispositions in `review.yaml`. A completion adversary must
sign off before packaging proceeds. High-severity findings must be explicitly disposed
with a rationale — closing the issue is not enough.

**Progressive-disclosure enforcement.** Claude Code only loads files referenced from
`SKILL.md`. Static analysis flags orphaned files (on disk but not referenced) and dead
references (referenced but absent) as errors. Lint checks that every `skill.yaml`
dependency is linked. The two checks are complementary: you can't accidentally ship
dead code or reference files that don't exist.

**Reliable subprocess transport.** The `claude -p` runner uses a thread-per-stream
queue with non-blocking `read1` on stderr so it never hangs on large output. Process
groups are cleaned up even when the parent exits first. Transcripts are opened before
`Popen` so a failed open can't leave a running subprocess. All of this is tested with a
fake subprocess — no live Claude needed in CI.

**One entry point.** `python bsc.py` from the repo root. No navigating into
subdirectories, no `PYTHONPATH`, no internal module paths to remember.

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
