# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Claude Code **plugin** (`.claude-plugin/`) that wraps a single **meta-skill** at
`skills/skill-creator/`. The skill builds, tests, and iteratively improves *other* Claude Code
skills. It is a fork of Anthropic's `skill-creator`. Almost all real work happens under
`skills/skill-creator/`; the repo root just holds the plugin/marketplace manifests and docs.

## Commands

Dependencies: `pip install -r requirements.txt` (PyYAML; everything else is stdlib). Python 3.12+ is
the supported floor and the type-check target (`pyrightconfig.json`).

**All Python tooling runs as modules with the CWD set to `skills/skill-creator/`** (see Import root
below). From that directory:

```bash
# Offline validators (fast, no network/model). Exit 0 = clean, 2 = warnings-only, 1 = blocking error.
python -m scripts.quick_validate .      # structural: frontmatter, required fields, lifecycle
python -m scripts.lint .                # content-quality + reference-wiring completeness
python -m scripts.static_analysis .     # dead references, orphaned files, unused tools, etc.
python -m scripts.review_gate .         # gate over review.yaml (see Review gate)
scripts/validate_all.sh .               # all of the above, then live trigger tests if `claude` is on PATH

# Tests (pure-Python; streaming tests use a fake subprocess, never a live `claude`)
python -m pytest tests/
python -m pytest tests/test_run_eval_stream.py::test_timeout    # single test

# Live trigger evals + behaviour grading (require the `claude` CLI + subprocess access)
python -m scripts.skill_test <skill-folder>                     # runs tests/should_(not_)trigger.yaml
python -m scripts.skill_test <skill-folder> --grade-transcript <transcript>   # grade expected_behavior.yaml
python -m scripts.run_loop --eval-set <eval.json> --skill-path <dir> --model <model>  # optimize the description

# Package a skill into a distributable .skill (runs the compiler pipeline; blocks on error findings)
python -m scripts.package_skill .

# From the repo root:
claude plugin validate .                # validate plugin.json + marketplace.json
```

**Exit-code convention across `run_eval` / `run_loop` / `skill_test`:** `0` = all passed, `1` =
execution/input/infrastructure error, `2` = completed but some expectations failed.

## Architecture (the parts that span multiple files)

**Import root.** `skills/skill-creator/scripts/` is a package; code imports siblings as
`from scripts.X import …` and expects the *parent* dir (`skills/skill-creator/`) on the path. Always
invoke as `python -m scripts.X` from `skills/skill-creator/` — running a script by file path breaks
imports. `pyrightconfig.json` (root and skill dir) and `.vscode/settings.json` encode the same root
for editors; `skill_test.py` runs the toolkit module from the toolkit dir while pointing `--skill-path`
at the (possibly external) target skill.

**Progressive-disclosure invariant.** Under Claude Code, a file not referenced from `SKILL.md` is
never loaded — so it effectively does not exist. This is enforced mechanically and will block a
release if violated:
- `static_analysis.py` flags an **orphaned file** (present on disk, unreferenced in SKILL.md) as an
  error, and a **dead reference** (referenced but absent) — runtime workspace outputs like
  `evals/evals.json` are exempted via `RUNTIME_OUTPUT_PREFIXES` in `analysis_config.py`.
- `lint.py` enforces the reverse: every `skill.yaml` dependency must be linked from SKILL.md.
- Therefore the SKILL.md **Reference files** section, `skill.yaml` `dependencies`, and the files on
  disk must stay in sync. Keep SKILL.md within the ~500-line budget (environment/optimization docs are
  extracted to `references/`).

**Eval machinery (how "does the description trigger the skill?" is measured).** `run_eval.py` writes a
synthetic command file into the project's `.claude/commands/`, spawns `claude -p` per query (prompt
over **stdin**, output as stream-json read by a background reader thread + queue — do not reintroduce
`select` on the pipe; it is not portable), and classifies each run into a `QueryOutcome`
(`structured_logging.py`): a clean `triggered`/`not_triggered`, or a failure category
(`TIMEOUT`/`AUTHENTICATION`/`SUBPROCESS_CRASH`/`PARSING`). **A failed execution is never counted as a
pass** — trigger rate is computed over clean runs only, and `run_eval` surfaces `execution_error` per
query and `infrastructure_failed` in the summary. `run_loop.py` wraps eval + `improve_description.py`
into an optimization loop that **stops instead of optimizing when infrastructure fails**.
`tests_loader.py` normalizes every trigger-test file (bool or legacy `triggered`/`not_triggered`
labels, `prompt`/`query` aliases; rejects malformed, de-dupes) into the eval set.

**Compiler pipeline.** `compiler_context.py` (`CompilerContext`) + `pipeline.py`
(`StageRegistry.run_all`) + `scripts/stages/` run a staged quality gate (lint → semantic → dependency
→ repair → review → score → package) sharing one context. `package_skill.py` drives it and refuses to
package when error-severity findings remain after auto-repair.

**Independent review gate.** For substantial skill work, `review.py` records an independent
multi-agent review + adversarial completion gate in `review.yaml`; `review_gate.py` / `ReviewStage`
deterministically block packaging until high-severity findings are disposed and
`completion_gate_status: passed`. See `references/independent-review.md`.

**Agents** (`agents/*.md`) are subagent instruction files spawned during evals and reviews (grader,
comparator, analyzer, the reviewers, the completion-adversary) — not executable code.

## Releasing

Version lives in `.claude-plugin/plugin.json`, `skills/skill-creator/skill.yaml`, and the README
badge — keep them in lockstep. `CHANGELOG.md` follows Keep a Changelog. `main` is branch-protected:
land changes via a feature branch → PR. Run `scripts/validate_all.sh` and `claude plugin validate .`
before tagging.
