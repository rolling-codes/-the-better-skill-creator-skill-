# Better Skill Creator

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v1.0.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Fork of Anthropic skill-creator](https://img.shields.io/badge/fork-Anthropic%2Fskill--creator-orange.svg)](#what-sets-this-fork-apart)
[![Python Scripts](https://img.shields.io/badge/Python-3.8%2B-green.svg)](#whats-included)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE.txt)

A fork of Anthropic's `skill-creator` that fixes what the original got wrong. Most of its scripts and agents were never referenced in SKILL.md, so Claude couldn't see them. Trigger tests were thin. The grader agent had no path to the expected-behavior file it was supposed to evaluate. This fork addresses those gaps, then adds tooling to catch the same class of mistakes in any skill you build.

---

## Anthropic vs Better Skill Creator

| | Anthropic skill-creator | Better Skill Creator |
|---|---|---|
| **SKILL.md length** | Uncontrolled. Claude.ai and Cowork instructions embedded inline, pushing the file past the 500-line guidance. | 463 lines. Environment docs extracted to `references/environments.md` and linked with a one-line pointer. |
| **Dependency discoverability** | `agents/grader.md`, `agents/analyzer.md`, `agents/comparator.md`, `references/schemas.md`, `references/trigger-confidence.md`, `references/dependency-graph.md`, `scripts/skill_test.py`, and `scripts/validate_all.sh` exist in the repo but are never mentioned in `SKILL.md`. Claude can't use what it doesn't know about. | All 14 dependencies listed in a dedicated **Reference files** section at the bottom of `SKILL.md`, with one-line guidance on when to read each one. |
| **Trigger test coverage** | Minimal | 10 positive + 9 near-miss negative test cases in `tests/` written against the skill's own eval-writing guidance (concrete, realistic, tricky negatives) |
| **Grader agent integration** | `agents/grader.md` and `tests/expected_behavior.yaml` both exist but there's no path between them. No script routes `expected_behavior.yaml` through the grader. | `scripts/skill_test.py --grade-transcript` grades `tests/expected_behavior.yaml` via `agents/grader.md` and writes structured pass/fail output. |
| **Cowork / headless support** | A prose paragraph saying "remember that Cowork has no browser, so you may need to use `--static`" that agents routinely skipped. | An explicit ordered checkpoint: detect no-display environment, switch to `--static <output_path>`, confirm `feedback.json` downloaded before proceeding. |

---

## What Sets This Fork Apart

### 1. All dependencies wired into SKILL.md

The original ships with a full set of scripts and agents (`grader.md`, `comparator.md`, `analyzer.md`, `schemas.md`, `trigger-confidence.md`, `dependency-graph.md`, `skill_test.py`, `validate_all.sh`) but never mentions most of them in `SKILL.md`. Under Claude Code's progressive disclosure model, a file that isn't referenced in `SKILL.md` is invisible. Claude doesn't load it and doesn't know it exists. This fork adds a **Reference files** section at the bottom of `SKILL.md` that lists every dependency with a one-line description of when to read it. Nothing is unreachable.

### 2. SKILL.md under 500 lines

Claude Code's own progressive disclosure guidance recommends keeping `SKILL.md` under 500 lines so the full body stays comfortably in context. The original violated this by embedding Claude.ai and Cowork environment instructions inline. This fork extracts those sections to [`references/environments.md`](skills/skill-creator/references/environments.md) and replaces them with a four-line pointer block. `SKILL.md` lands at 463 lines.

### 3. Trigger tests that actually test something

The original had a thin test suite. Near-miss negatives (queries that share keywords with the skill but should trigger something else) are the only tests that reveal whether a skill description is too broad. This fork ships 10 positive cases and 9 near-miss negatives in `tests/`, all written following the skill's own guidance: concrete, realistic prompts with enough context that a naive keyword match would fail.

### 4. `--grade-transcript` mode

`tests/expected_behavior.yaml` defines what the skill should *do* (not just whether it triggers). The original had this file and had `agents/grader.md` but no path between them. The grader couldn't evaluate the expected behaviors automatically. This fork adds `--grade-transcript` to `scripts/skill_test.py`, which routes `expected_behavior.yaml` through the grader agent and writes structured pass/fail output.

### 5. Cowork as an ordered checkpoint

The original's Cowork section was a reminder paragraph that agents routinely skipped. This fork restructures it as an explicit decision tree: check for display availability, switch to `--static <output_path>` if absent, confirm `feedback.json` was downloaded before continuing to the next step. Each decision is a discrete step, not prose.

---

## Why Skill Creators Need Work

Claude Code's native skill-creator has six known failure modes:

1. **Triggering failures.** Descriptions lack an explicit trigger or boundary, so skills either never fire or fire when they shouldn't.
2. **Imperative fragility.** Bare MUST/NEVER rules break when the agent hits edge cases the author didn't anticipate.
3. **The excuse trap.** Agents rationalize skipping important steps when nothing explicitly names the rationalization.
4. **Token tax.** Generic rules get stuffed into CLAUDE.md "just in case," bloating every session.
5. **Guessing modes.** No explicit output format means inconsistent results.
6. **Shallow verification.** A single happy-path test proves nothing about triggering accuracy or consistency.

Skill-Architect addressed all six. This fork carries that work forward.

---

## The Six Gates (Where This Came From)

Before this fork existed, the same author built **Skill-Architect**, a meta-skill that put new skills through a six-gate verification pipeline before shipping them. That research identified what specifically breaks when skills are built without a framework, and shaped the audit improvements in this fork.

### Gate 0: Evidence
Read every existing SKILL.md in the project's skills directory. Record name, description, paths, and allowed-tools. This is the foundation for the overlap check later.

### Gate 1: Deep Interviewing
Interview the user one level deeper than standard Q&A. After every answer, ask one follow-up "why" or edge-case probe. Then have the agent introspect on how it would rationalize skipping important steps. Use those rationalizations to populate the Red Flags table. Agents understand agent behavior better than users can speculate.

### Gate 2: Trigger Spec
Write the description in three explicit clauses:
- **Capability:** what the skill does
- **Trigger:** the concrete situations that activate it
- **Boundary:** what it explicitly does not cover

A description missing any clause is not acceptable.

### Gate 3: Iron Law and Red Flags
State one non-negotiable rule the skill enforces, phrased as "X because Y" reasoning rather than a bare imperative. Build a Red Flags table from Gate 1's rationalizations, paired with correct behavior.

### Gate 4: Self-Critique
Identify the single most likely way this skill will misfire in practice (over-trigger, under-trigger, or produce inconsistent output). State this critique to the user. They may know something that changes the fix.

### Gate 5: Overlap Check
Compare the new description against every existing skill. Flag pairs where a plausible user request could match both. Propose narrower Boundary clauses to prevent collisions.

### Gate 6: Variance Testing
Test against 2-3 varied prompts covering trigger, boundary/edge, and non-trigger cases. Report triggering accuracy and output consistency as separate findings.

---

## Design Philosophy

**Reasoning over rules.** Every constraint is phrased as "X because Y" so agents can generalize to edge cases the author didn't anticipate, rather than breaking when they hit a case not covered by a bare MUST/NEVER.

**Red Flags from real interviews.** Rationalizations come from actual adversarial questioning, not generic guesses. This makes the Red Flags table catch failures that actually happen.

**Overlap check before shipping.** Description collisions with other skills are caught before the skill ships, not discovered when two skills misbehave together months later.

**Variance testing as proof.** A single happy-path test proves nothing. Testing across trigger, boundary, and non-trigger cases confirms the skill actually works as intended.

---

## How It Was Built

Skill-Architect was built from NotebookLM research into Claude Code's skill system, drawing on:

- Claude Code skill documentation and behavior
- Fable 5 planning and skill-building methodology
- "One Agent Is NOT ENOUGH" (multi-agent failure modes)
- "I Turned Claude Into the Ultimate Second Brain" (memory and skill compounding)
- "Claude Code + Graphify" (knowledge graph integration)
- "How I Make Opus Think Like Fable" (model-specific skill routing)
- Production skill-building sessions and real failure cases

That research identified the specific gaps in the native skill-creator and produced the pipeline that Skill-Architect implements and that this fork audits against.

---

## What It Does

**Better Skill Creator** manages the full lifecycle of building and improving Claude Code skills:

- **Draft** a skill from intent: interviews, edge-case probing, SKILL.md generation
- **Test** by spawning Claude subprocesses against realistic prompts (with-skill vs baseline, in parallel)
- **Review** outputs in a browser-based viewer with side-by-side comparison and feedback collection
- **Iterate** with a blind A/B comparison agent that evaluates without knowing which version is which
- **Benchmark** across runs: pass rates, timing, token counts with mean ± stddev and per-version delta
- **Optimize** the skill description with an automated loop that splits train/test and selects by held-out score
- **Package** into a distributable `.skill` file

---

## What's Included

### Scripts (`scripts/`)
| Script | Purpose |
|--------|---------|
| `run_eval.py` | Tests trigger accuracy; spawns Claude subprocesses per prompt |
| `run_loop.py` | Iterates eval then improve; stops at target accuracy or iteration limit |
| `improve_description.py` | Standalone description rewriter for targeted triggering tuning |
| `skill_test.py` | Regression suite runner; `--grade-transcript` grades `expected_behavior.yaml` |
| `aggregate_benchmark.py` | Produces `benchmark.json` with mean ± stddev across runs |
| `generate_report.py` | Converts benchmark data to human-readable markdown |
| `quick_validate.py` | Read-only SKILL.md structural check (frontmatter, fields, lifecycle) |
| `package_skill.py` | Zips a skill folder into a distributable `.skill` archive |
| `validate_all.sh` | Runs `quick_validate.py` and `skill_test.py` in one shot |

### Agents (`agents/`)
| Agent | Purpose |
|-------|---------|
| `comparator.md` | Blind A/B: evaluates outputs without knowing which version produced which |
| `analyzer.md` | Flags non-discriminating assertions and high-variance evals |
| `grader.md` | Scores `expected_behavior.yaml` assertions against test outputs |

### Eval viewer (`eval-viewer/`)
Local web UI: with-skill vs baseline side by side, benchmark tab, structured feedback collection. Run `python eval-viewer/generate_review.py <workspace>`. Use `--static` for headless/Cowork environments.

### Tests (`tests/`)
- `should_trigger.yaml`: 10 positive test cases
- `should_not_trigger.yaml`: 9 near-miss negative test cases
- `expected_behavior.yaml`: Behavior assertions graded by `agents/grader.md`

---

## What's New in v1.1.0

All six architectural gaps from the original roadmap are now implemented.

### Intermediate Representation (`scripts/skill_ir.py`)

`Skill` dataclass as the single shared model for a skill. All scripts parse through `Skill.from_path()` rather than each doing their own frontmatter and yaml parsing. `utils.py`'s `parse_skill_md()` delegates here, so existing callers are unchanged.

### Formal Dependency Graph (`scripts/dependency_graph.py`)

`SkillGraph` builds a directed graph from `skill.yaml` dependencies and backtick file references in SKILL.md. Supports cycle detection, missing-node audit, reverse impact traversal, and export to JSON or Graphviz DOT.

```
python -m scripts.dependency_graph <skill-path> [--format json|dot|summary]
```

### Plugin Architecture (`generators/`)

`GeneratorRegistry` with a pluggable `Generator` base class. Three built-in archetypes: `default` (general-purpose layout), `python-skill` (pre-fills terminal/filesystem tools, creates `scripts/main.py` stub), `research` (pre-fills WebSearch/WebFetch, creates `references/overview.md`). New archetypes register themselves with `registry.register(MyGenerator())`.

```
python -m generators --archetype python-skill --name my-skill --output ./skills/
python -m generators --list
```

### Static Analysis (`scripts/static_analysis.py`)

Five semantic checks that run before packaging: dead references, missing assets, unused tools, unreachable sections, and recursive self-calls. Error-severity findings block the package step before the zip is written.

```
python -m scripts.static_analysis <skill-path>
```

### Skill Linting (`scripts/lint.py`)

Eight content-quality checks: description length, missing trigger clause, missing boundary clause, token budget, missing examples, missing reference section, frontmatter tools, and workflow output artifacts. Exit 0 = clean, 1 = errors (blocks pre-commit), 2 = warnings only (commit proceeds). Wired into `scripts/hooks/pre-commit`.

```
python -m scripts.lint <skill-path>
```

### Versioned Skill Schema (`scripts/migrations/`, `scripts/migrate_skill.py`)

`schemaVersion: 1` is now in frontmatter and `skill.yaml`. A migration registry maps version pairs to upgrade functions. `v1_to_v2.py` is the template. The CLI finds the shortest path and applies each step in sequence.

```
python -m scripts.migrate_skill <skill-path> --to 2 [--dry-run]
```

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

## Related

- **dev-workflow:** Claude Code skill that uses the skill-architect output format. Enforces the five-step development pipeline (Research, Plan, TDD, Code Review, Commit).
- **ECC:** Enterprise Claude Code rules. Foundational patterns Skill-Architect skills build on.

## License

[Apache 2.0](LICENSE.txt)
