# Skill-Architect

[![Release v1.0.0](https://img.shields.io/badge/release-v1.0.0-blue.svg)](https://github.com/rolling-codes/-the-better-skill-creator-skill-/releases/tag/v1.0.0)
[![Claude Code Skill](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://claude.ai/code)
[![Python Scripts](https://img.shields.io/badge/Python-3.8%2B-green.svg)](#)
[![Open Source](https://img.shields.io/badge/license-Public-brightgreen.svg)](#license)

A meta-skill for Claude Code that creates, audits, and refines other skills through a rigorous six-gate pipeline. Replaces the native skill-creator with adversarial elicitation, trigger contract validation, Iron Law enforcement, Blast Radius analysis, and variance testing. Built from NotebookLM research into Claude Code's skill system failure modes.

## What It Does

**Skill-Architect** builds production-grade Claude Code skills that are more reliable, more edge-case-aware, and more verifiable than default-generated ones. It does this by:

1. **Reverse-engineering user expertise** — running adversarial interviews to ground skills in real experience, not generic best practices
2. **Enforcing trigger contracts** — ensuring descriptions have explicit Capability + Trigger + Boundary clauses
3. **Establishing Iron Laws** — naming the one non-negotiable rule each skill exists to enforce
4. **Analyzing blast radius** — checking new skills against existing ones for description overlap and collision risk
5. **Verifying with variance testing** — confirming skills trigger correctly and produce consistent output across varied inputs

## Modes

- **Create** — build a brand-new SKILL.md from an adversarial interview
- **Audit** — review an existing SKILL.md against Iron Law, Red Flags, and Blast Radius criteria
- **Variance-check** — test a skill against 2-3 varied prompts to verify triggering accuracy and output consistency

## Why It Exists

Claude Code's native skill-creator has known failure modes:

1. **Triggering failures** — descriptions lack explicit trigger or boundary, so skills either never fire or fire when they shouldn't
2. **Imperative fragility** — bare MUST/NEVER rules break when the agent hits edge cases the author didn't anticipate
3. **The excuse trap** — agents rationalize skipping important steps when nothing explicitly names the rationalization
4. **Token tax** — generic rules get stuffed into CLAUDE.md "just in case," bloating every session
5. **Guessing modes** — no explicit output format means inconsistent results
6. **Shallow verification** — a single happy-path test proves nothing about triggering accuracy or consistency

Skill-Architect closes all six gaps.

## How It Was Built

Skill-Architect was built from **NotebookLM research into Claude Code's skill system**, synthesizing insights from:

- Claude Code skill documentation and behavior
- Fable 5 planning and skill-building methodology  
- "One Agent Is NOT ENOUGH" — multi-agent failure modes
- "I Turned Claude Into the Ultimate Second Brain" — memory and skill compounding
- "Claude Code + Graphify" — knowledge graph integration
- "How I Make Opus Think Like Fable" — model-specific skill routing
- Production skill-building sessions and real failure cases

This research identified the specific gaps in the native skill-creator and produced the six-gate framework (Evidence, Adversarial Elicitation, Trigger Contract, Iron Law, Self-Critique, Blast Radius, Variance Analysis) that Skill-Architect implements.

## The Six Gates

### Gate 0 — Evidence
Read every existing SKILL.md in the project's skills directory. Record name, description, paths, and allowed-tools. This is the foundation for Blast Radius analysis later.

### Gate 1 — Adversarial Elicitation
Interview the user one level deeper than standard Q&A. After every answer, ask one follow-up "why" or edge-case probe. Then: have the agent introspect on how it would rationalize skipping important steps. Use those rationalizations to populate the Red Flags table. Agents understand agent behavior better than users can speculate.

### Gate 2 — Trigger Contract
Write the description in three explicit clauses:
- **Capability** — what the skill does
- **Trigger** — the concrete situations that activate it
- **Boundary** — what it explicitly does not cover

A description missing any clause is not acceptable.

### Gate 3 — Iron Law and Red Flags
State one non-negotiable rule the skill enforces, phrased as "X because Y" reasoning, not a bare imperative. Build a Red Flags table from Gate 1's rationalizations, paired with correct behavior.

### Gate 4 — Adversarial Self-Critique
Identify the single most likely way this skill will misfire in practice (over-trigger, under-trigger, or produce inconsistent output). State this critique to the user — they may know something that changes the fix.

### Gate 5 — Blast Radius Analysis
Compare the new description against every existing skill. Flag pairs where a plausible user request could match both. Propose narrower Boundary clauses to prevent collisions.

### Gate 6 — Variance Analysis
Test against 2-3 varied prompts covering trigger, boundary/edge, and non-trigger cases. Report triggering accuracy and output consistency as separate findings.

## Installation

See [SETUP.md](SETUP.md) for prerequisites and installation instructions.

## Quick Start

```bash
# Install as a plugin (from a local checkout)
claude plugin marketplace add /path/to/skill-architect
claude plugin install skill-architect@skill-architect-local

# Or from GitHub
/plugin marketplace add rolling-codes/-the-better-skill-creator-skill-
/plugin install skill-architect
```

Restart Claude Code (or `/reload-plugins`), then invoke `/skill-architect` and
choose a mode (create / audit / variance-check).

## Plugin Layout

The skill lives under `skills/skill-architect/`:

- `skills/skill-architect/SKILL.md` — router, Iron Law, Gate 0
- `skills/skill-architect/workflows/create.md` — Full Gate 0-6 walkthrough for brand-new skills
- `skills/skill-architect/workflows/audit.md` — Gates 0, 3, 4, 5 for reviewing existing skills
- `skills/skill-architect/workflows/variance-check.md` — Gate 6 in isolation, with test-prompt matrix

## Scripts

Under `skills/skill-architect/scripts/`:

- `lint.py` — Semantic checks (missing boundary, vague trigger, unused variable, bare MUST/NEVER, missing Red Flags)
- `dependency_graph.py` — Verifies all referenced workflow and script files exist
- `overlap_check.py` — Jaccard-similarity heuristic for detecting description overlap

## Memory

- `skills/skill-architect/memory/lessons.md` — Append-only log of real misfires, root causes, and fixes. Updated after each production failure so the framework continuously improves.

## Design Philosophy

**Reasoning over imperatives.** Every rule is phrased as "X because Y" so agents generalize to edge cases the author didn't anticipate, rather than breaking when hitting a case not covered by a bare MUST/NEVER.

**Red Flags from experience.** Rationalizations come from real adversarial elicitation, not generic guesses. This makes the Red Flags table actually catch the failures that happen in practice.

**Blast Radius before production.** Description overlap is checked before the skill ships, not discovered when two skills misbehave together months later.

**Variance testing as proof.** A single happy-path test proves nothing. Variance testing across trigger, boundary, and non-trigger cases confirms the skill actually works as intended.

**Memory that learns.** Every real misfire is logged to `memory/lessons.md` and feeds back into lint checks and Red Flags tables, so the framework improves over time.

## Related

- **dev-workflow** — Claude Code skill using Skill-Architect's output. Enforces the five-step development pipeline (Research → Plan → TDD → Code Review → Commit).
- **ECC** — Enterprise Claude Code rules. Foundational patterns Skill-Architect skills build on.

## License

Public. Build on this.
