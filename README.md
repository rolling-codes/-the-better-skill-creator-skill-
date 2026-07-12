# Better Skill Creator

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v1.0.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Fork of Anthropic skill-creator](https://img.shields.io/badge/fork-Anthropic%2Fskill--creator-orange.svg)](#what-sets-this-fork-apart)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A fork of Anthropic's `skill-creator`, audited on 2026-07-11 to fix five concrete problems in the original. Same eval loop, viewer, and benchmark pipeline — but all the pieces actually connect.

---

## Anthropic vs Better Skill Creator

| | Anthropic skill-creator | Better Skill Creator |
|---|---|---|
| **SKILL.md length** | Uncontrolled — Claude.ai and Cowork instructions embedded inline, pushing the file past the 500-line guidance | 463 lines. Environment docs extracted to `references/environments.md` and linked with a one-line pointer |
| **Dependency discoverability** | `agents/grader.md`, `agents/analyzer.md`, `agents/comparator.md`, `references/schemas.md`, `references/trigger-confidence.md`, `references/dependency-graph.md`, `scripts/skill_test.py`, and `scripts/validate_all.sh` exist in the repo but are never mentioned in `SKILL.md` — Claude can't use what it doesn't know about | All 14 dependencies listed in a dedicated **Reference files** section at the bottom of `SKILL.md`, with one-line guidance on when to read each one |
| **Trigger test coverage** | Minimal | 10 positive + 9 near-miss negative test cases in `tests/` written against the skill's own eval-writing guidance (concrete, realistic, tricky negatives) |
| **Grader agent integration** | `agents/grader.md` and `tests/expected_behavior.yaml` both exist but there's no path between them — no script routes `expected_behavior.yaml` through the grader | `scripts/skill_test.py --grade-transcript` grades `tests/expected_behavior.yaml` via `agents/grader.md` and writes structured pass/fail output |
| **Cowork / headless support** | A prose paragraph saying "remember that Cowork has no browser, so you may need to use `--static`" — easily skipped | An explicit ordered checkpoint: detect no-display environment → use `--static <output_path>` → confirm `feedback.json` downloaded before proceeding |

---

## What Sets This Fork Apart

### 1. All dependencies wired into SKILL.md

The original ships with a full set of scripts and agents (`grader.md`, `comparator.md`, `analyzer.md`, `schemas.md`, `trigger-confidence.md`, `dependency-graph.md`, `skill_test.py`, `validate_all.sh`) but never mentions most of them in `SKILL.md`. Under Claude Code's progressive disclosure model, a file that isn't referenced in `SKILL.md` is invisible — Claude doesn't load it and doesn't know it exists. This fork adds a **Reference files** section at the bottom of `SKILL.md` that lists every dependency with a one-line description of when to read it. Nothing is unreachable.

### 2. SKILL.md under 500 lines

Claude Code's own progressive disclosure guidance recommends keeping `SKILL.md` under 500 lines so the full body stays comfortably in context. The original violated this by embedding Claude.ai and Cowork environment instructions inline. This fork extracts those sections to [`references/environments.md`](skills/skill-creator/references/environments.md) and replaces them with a four-line pointer block. `SKILL.md` lands at 463 lines.

### 3. Trigger tests that actually test something

The original had a thin test suite. Near-miss negatives — queries that share keywords with the skill but should trigger something else — are the only tests that reveal whether a skill description is too broad. This fork ships 10 positive cases and 9 near-miss negatives in `tests/`, all written following the skill's own guidance: concrete, realistic prompts with enough context that a naive keyword match would fail.

### 4. `--grade-transcript` mode

`tests/expected_behavior.yaml` defines what the skill should *do* (not just whether it triggers). The original had this file and had `agents/grader.md` but no path between them — the grader couldn't evaluate the expected behaviors automatically. This fork adds `--grade-transcript` to `scripts/skill_test.py`, which routes `expected_behavior.yaml` through the grader agent and writes structured pass/fail output.

### 5. Cowork as an ordered checkpoint

The original's Cowork section was a reminder paragraph that agents routinely skipped. This fork restructures it as an explicit decision tree: check for display availability → if absent, switch to `--static <output_path>` → confirm `feedback.json` was downloaded before continuing to the next step. Each decision is a discrete step, not prose.

---

## What It Does

**Better Skill Creator** manages the full lifecycle of building and improving Claude Code skills:

- **Draft** a skill from intent — interviews, edge-case probing, SKILL.md generation
- **Test** by spawning Claude subprocesses against realistic prompts (with-skill vs baseline, in parallel)
- **Review** outputs in a browser-based viewer with side-by-side comparison and feedback collection
- **Iterate** with a blind A/B comparison agent that evaluates without knowing which version is which
- **Benchmark** across runs — pass rates, timing, token counts with mean ± stddev and per-version delta
- **Optimize** the skill description with an automated loop that splits train/test and selects by held-out score
- **Package** into a distributable `.skill` file

---

## What's Included

### Scripts (`scripts/`)
| Script | Purpose |
|--------|---------|
| `run_eval.py` | Tests trigger accuracy; spawns Claude subprocesses per prompt |
| `run_loop.py` | Iterates eval → improve; stops at target accuracy or iteration limit |
| `improve_description.py` | Standalone description rewriter for targeted triggering tuning |
| `skill_test.py` | Regression suite runner; `--grade-transcript` grades `expected_behavior.yaml` |
| `aggregate_benchmark.py` | Produces `benchmark.json` with mean ± stddev across runs |
| `generate_report.py` | Converts benchmark data to human-readable markdown |
| `quick_validate.py` | Read-only SKILL.md structural check — frontmatter, fields, lifecycle |
| `package_skill.py` | Zips a skill folder into a distributable `.skill` archive |
| `validate_all.sh` | Runs `quick_validate.py` + `skill_test.py` in one shot |

### Agents (`agents/`)
| Agent | Purpose |
|-------|---------|
| `comparator.md` | Blind A/B — evaluates outputs without knowing which version produced which |
| `analyzer.md` | Flags non-discriminating assertions and high-variance evals |
| `grader.md` | Scores `expected_behavior.yaml` assertions against test outputs |

### Eval viewer (`eval-viewer/`)
Local web UI: with-skill vs baseline side by side, benchmark tab, structured feedback collection. Run `python eval-viewer/generate_review.py <workspace>`. Use `--static` for headless/Cowork environments.

### Tests (`tests/`)
- `should_trigger.yaml` — 10 positive test cases
- `should_not_trigger.yaml` — 9 near-miss negative test cases
- `expected_behavior.yaml` — Behavior assertions graded by `agents/grader.md`

---

## Installation

```bash
git clone https://github.com/rolling-codes/-the-better-skill-creator-skill-
claude plugin marketplace add /path/to/-the-better-skill-creator-skill-
claude plugin install skill-creator@skill-creator-local
```

Restart Claude Code (or `/reload-plugins`). The skill loads automatically when you ask Claude to create, test, or improve a skill.

## Requirements

- Claude Code with subprocess access (`claude -p`)
- Python 3.8+, stdlib only (no external dependencies)

## License

[Apache 2.0](LICENSE.txt)
