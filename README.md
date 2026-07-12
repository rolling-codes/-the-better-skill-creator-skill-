# Better Skill Creator

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v1.0.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Fork of Anthropic skill-creator](https://img.shields.io/badge/fork-Anthropic%2Fskill--creator-orange.svg)](#fork)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A fork of [Anthropic's skill-creator](https://github.com/anthropics/anthropic-quickstarts), audited and extended with a fuller test suite, navigable documentation, and a transcript grading mode.

---

## What Sets This Fork Apart

The original Anthropic skill-creator is solid but shipped with some rough edges. This fork fixes them:

### 1. Orphaned files wired in
Several scripts and agents existed in the repo but were unreachable — the SKILL.md's progressive disclosure model never pointed to them, so Claude couldn't use them. Every dependency is now explicitly referenced in `SKILL.md` under the appropriate section.

### 2. Cleaner SKILL.md (under 500 lines)
The original embedded Claude.ai and Cowork environment instructions inline, bloating the main file and making it hard to navigate. Those sections have been extracted to [`references/environments.md`](skills/skill-creator/references/environments.md) and linked from `SKILL.md`. The main file now reads cleanly in a single pass.

### 3. Expanded trigger test suite (10/9)
The original had a thin set of test cases. This fork ships with **10 positive** (`should_trigger.yaml`) and **9 near-miss negative** (`should_not_trigger.yaml`) test cases written per the skill's own eval-writing guidance — covering intent, draft-from-scratch, eval, description improvement, workflow capture, blind comparison, and packaging prompts.

### 4. Ordered Cowork checkpoint
The original Cowork section was a "please remember to..." plea that agents routinely skipped. It's been restructured as an explicit ordered checkpoint that Claude steps through before attempting browser-dependent actions in Cowork environments.

### 5. `--grade-transcript` mode
`skill_test.py` now accepts a `--grade-transcript` flag that routes `expected_behavior.yaml` through `agents/grader.md` for structured pass/fail grading. The original had the grader agent and the `expected_behavior.yaml` file but no wired path between them.

---

## What It Does

**Better Skill Creator** handles the full lifecycle of building and improving Claude Code skills:

- **Draft** a new skill from a description of what you want it to do
- **Eval** whether the skill triggers correctly on real prompts (using `claude -p` subprocesses)
- **Review** outputs side-by-side in a browser-based viewer
- **Iterate** with a blind A/B comparison agent that doesn't know which version is which
- **Benchmark** across runs with pass rates, token/timing statistics, and per-version deltas
- **Ship** by packaging the skill into a distributable `.skill` file

---

## What's Included

### Scripts (`scripts/`)
| Script | Purpose |
|--------|---------|
| `run_eval.py` | Tests trigger accuracy; spawns Claude subprocesses against test prompts |
| `improve_description.py` | Rewrites skill descriptions to improve trigger accuracy |
| `run_loop.py` | Iterates eval → improve until a target accuracy or iteration limit is hit |
| `skill_test.py` | Regression suite runner; supports `--grade-transcript` for grader-agent scoring |
| `aggregate_benchmark.py` | Aggregates grading results into `benchmark.json` with mean±stddev |
| `generate_report.py` | Human-readable markdown report from benchmark data |
| `quick_validate.py` | Structural SKILL.md validation (frontmatter, fields, lifecycle) |
| `package_skill.py` | Bundles a skill into a distributable `.skill` zip |
| `validate_all.sh` | Runs quick_validate + skill_test in sequence |

### Agents (`agents/`)
| Agent | Purpose |
|-------|---------|
| `comparator.md` | Blind A/B comparison — evaluates without knowing which version is which |
| `analyzer.md` | Flags non-discriminating assertions and high-variance evals |
| `grader.md` | Scores `expected_behavior.yaml` assertions against test outputs |

### Eval viewer (`eval-viewer/`)
Browser-based UI that shows with-skill vs baseline outputs side by side, displays benchmark metrics, and collects structured feedback. Run with `python eval-viewer/generate_review.py`; use `--static` for headless environments.

### References (`references/`)
- `schemas.md` — JSON schema for every data file the eval pipeline produces
- `environments.md` — Adaptations for Claude Code, Claude.ai, and Cowork
- `dependency-graph.md` — Hand-maintained map of script/agent dependencies
- `trigger-confidence.md` — How to interpret trigger rate output from `run_eval.py`

### Tests (`tests/`)
- `should_trigger.yaml` — 10 positive test cases
- `should_not_trigger.yaml` — 9 near-miss negative test cases
- `expected_behavior.yaml` — Behavior expectations for grader-agent scoring

---

## Installation

```bash
# Clone and install as a local plugin
git clone https://github.com/rolling-codes/-the-better-skill-creator-skill-
claude plugin marketplace add /path/to/-the-better-skill-creator-skill-
claude plugin install skill-creator@skill-creator-local
```

Restart Claude Code (or `/reload-plugins`). The skill loads automatically when you ask Claude to create, test, or improve a skill.

---

## Requirements

- Claude Code with subprocess access (`claude -p`)
- Python 3.8+
- No external Python dependencies (stdlib only)

---

## License

[Apache 2.0](LICENSE.txt). Fork it, modify it, ship it.
