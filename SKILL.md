---
name: skill-architect
description: Use this for creating, auditing, or variance-testing Claude Code SKILL.md files when the user wants a new skill built, an existing skill reviewed against Iron Law / Red Flags / Blast Radius criteria, or a skill's triggering accuracy checked against varied prompts; NOT for executing the end-task a skill performs, and NOT a replacement for editing non-skill project code.
paths: ["**/skills/**/SKILL.md", "**/*-pack/**"]
allowed-tools: [view, create_file, str_replace, bash]
variables:
  mode: "create | audit | variance-check — ask if not stated"
  skills_root: "path to the project's skills directory, resolved in Gate 0"
  target_skill: "path to SKILL.md under audit/variance-check, if mode != create"
---

# Skill-Architect

Purpose: build or review a SKILL.md so it triggers correctly and survives edge cases the author didn't anticipate — because a skill that only works on the happy path is worse than no skill, since it produces false confidence.

## Iron Law

A skill's description is its entire triggering surface — body text has zero effect on activation — so no skill ships without an explicit Capability + Trigger + Boundary description, because a description missing any of these three silently degrades either this skill or every other skill it now collides with.

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| "The description is basically clear, boundary is implied" | Implied boundaries don't stop the additive loading behavior — Claude opens every plausibly-relevant skill, so ambiguity compounds across the whole project | Write the Boundary clause explicitly, even if it feels redundant |
| "This is a simple skill, it doesn't need a Red Flags table" | Simple skills fail in production exactly because no one asked what rationalization looks like | Run Gate 1's adversarial probe regardless of perceived simplicity |
| "I'll check for overlap with other skills later" | Overlap discovered in production means two skills already misfired for a real user | Gate 5 runs before the skill is presented as finished, not after |
| "One good test run is enough to ship" | A single happy-path run proves nothing about triggering accuracy or output consistency | Gate 6 requires 2-3 varied prompts minimum |
| "The lint/dependency checks are just extra tooling, not required" | A skill that grants a real-effect tool it never uses, or references a workflow file that no longer exists, fails silently in production, not at review time | Run `scripts/lint.py` and `scripts/dependency_graph.py` before presenting any Create or Audit output as finished |

## Workflow router

| User intent | Go to |
|---|---|
| "Build me a skill for X" / no existing skill mentioned | Mode: Create → `workflows/create.md` |
| "Review/check/audit this skill" / points at existing SKILL.md | Mode: Audit → `workflows/audit.md` |
| "Does this skill trigger reliably?" / "test this skill" | Mode: Variance-check → `workflows/variance-check.md` |
| Ambiguous | Ask once which mode, don't guess silently — this is the one clarifying question worth asking since the three modes produce different artifacts |

All three modes share Gate 0 below before branching.

## Gate 0 — Evidence Gate (mandatory, all modes)

Before drafting or auditing anything, read every SKILL.md already present under the project's skills path. Record each existing skill's name, full description field, and paths/allowed-tools scope in a scratch table — this is the evidence Gate 5 (Blast Radius) consumes later. Confirm the directory is actually empty rather than assuming so if no skills are found.

```bash
find <skills_root> -name "SKILL.md" -exec sh -c 'echo "=== {} ==="; sed -n "/^---$/,/^---$/p" "{}"' \;
```

## Shared gates reference

Gates 1-6 (Adversarial Elicitation, Trigger Contract, Iron Law/Red Flags, Self-Critique, Blast Radius, Variance Analysis) are detailed per-mode in the workflow files, since Create runs all six, Audit runs 3/4/5 against an existing draft, and Variance-check runs only 6.

- `workflows/create.md` — full Gate 0-6 walkthrough for a brand-new skill
- `workflows/audit.md` — Gates 0, 3, 4, 5 applied to an existing SKILL.md
- `workflows/variance-check.md` — Gate 6 in isolation, with the test-prompt matrix
- `scripts/overlap_check.py` — Jaccard-similarity heuristic backing Gate 5, run it rather than eyeballing description overlap
- `scripts/lint.py` — semantic checks (missing boundary clause, vague trigger, unused variable, ungrounded tool grant, bare MUST/NEVER, missing Red Flags table) run in Create before Gate 4's self-critique, and in Audit alongside Gate 3
- `scripts/dependency_graph.py` — checks that every `workflows/*.md` and `scripts/*` reference in this skill resolves to a real file, and flags files on disk that nothing references; run it whenever workflows/ or scripts/ change, not just at creation
- `memory/lessons.md` — append-only log of real misfires and what should have caught them; check it during Gate 4 (has this failure mode already bitten a sibling skill?) and add to it after any real-world miss

## Output format (all modes)

1. The finished or annotated SKILL.md, in full — never a diff-only summary
2. Any `workflows/*.md` or `scripts/*` stub files it references
3. A short paragraph naming the specific trigger risks this version defends against that a naive, default-generated draft would have missed
4. Gate 5 Blast Radius findings — or "no existing skills to compare against" if Gate 0 found none
5. Gate 6 variance results, if mode was Create or Variance-check

## Notes — run free

These gates are a floor, not a ceiling. If the project's situation calls for judgment the gates don't cover, use it, and say what was done differently and why. Do not let this template suppress good judgment on a genuinely novel problem — that's exactly the failure mode this section exists to prevent.
