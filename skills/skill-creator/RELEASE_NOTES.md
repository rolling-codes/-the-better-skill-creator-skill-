# Better Skill Creator 2.0.2 Release Notes

This patch release corrects one documentation inaccuracy and records why the rest
of PR #10 was dropped.

## Fixes

- The SKILL.md reference entry for `scripts/dependency_graph.py` now shows it takes
  a skill root directory as its positional argument (`<skill-root>`), matching the
  tool's actual CLI and the README usage line.

## Dropped from PR #10

- PR #10 (`fix/variance-check-script-gate`) was authored against the retired
  `skill-architect` layout. Its Gate 0 frontmatter-only collection and its
  variance-check lint/dependency-graph gating have no equivalent in this
  `skill-creator` fork (no numbered gates, no variance-check mode,
  `dependency_graph.py` intentionally optional), so only the doc fix above carried
  over.

## Validation

- Offline pipeline green (`quick_validate`, `lint` 0 errors, `semantic_analysis`,
  score 90/100); `dependency_graph.py` exercised across a skill root in
  summary/json/dot plus the no-arg and bad-path contracts; regression suite 19/19.

---

# Better Skill Creator 2.0.1 Release Notes

This patch release fixes the validation-quality PR review findings.

## Fixes

- Restores cross-file lifecycle consistency validation between `skill.yaml` and
  `LIFECYCLE.md`.
- Replaces newly introduced PEP 604 union annotations in the changed validation
  and IR utilities with Python 3.8-compatible `typing.Union` forms.
- Hardens `safe_path_exists` so resolved sibling paths that merely share a text
  prefix with the base directory are rejected.

## Validation

- Added regression tests for lifecycle mismatch rejection, path-prefix traversal
  rejection, and avoiding PEP 604 unions in the changed modules.

---

# Better Skill Creator 2.0.0 Release Notes

This release adds an independent multi-agent review and adversarial completion
gate for complex skill creation and substantial skill updates.

## Highlights

- Complex skill work now routes through three fresh-context pre-draft reviewers:
  outcome interpretation, adversarial scope, and architecture/validation.
- Completion now requires a fresh completion adversary to try to prove the skill
  incomplete before it can be called done.
- `review.yaml` records activation, independent findings, disagreements,
  synthesis decisions, adversarial findings, dispositions, accepted limitations,
  unresolved decisive questions, and gate status.
- `scripts/review_gate.py` enforces the record deterministically and is wired into
  the package pipeline and full validation script.
- The behavioral checklist now includes the requested RPG, log-fixing,
  no-modification, narrow description-only, simple-skill, and ambiguous-request
  cases.

## Validation & evaluation

This release was held to its own gate. A fresh-context completion adversary tried
to prove the skill incomplete and returned `verdict: complete`; its three
low-severity findings are recorded and disposed in `review.yaml` (development-log
eval case added, `PackageStage` hardened to fail closed on review errors, and one
accepted limitation — offline validation cannot prove real subagent independence).
The full offline pipeline is green (`quick_validate`, `lint`, `static_analysis`,
`review_gate`), architecture score 95/100, and 16/16 pipeline tests pass.

A live previous-vs-new evaluation compared the skill against a no-skill baseline
(same model) over three representative prompts — RPG variant discrimination,
log-fix entailment-vs-authorization, and a no-modification constraint:

| Metric | With skill | Baseline | Delta |
|--------|-----------|----------|-------|
| Pass rate | 100% | 41.7% | +0.58 |
| Time | 104.7s | 65.2s | +39.4s |
| Tokens | 56,073 | 36,921 | +19,152 |

The skill's lift concentrates on ambiguous, underspecified prompts (it forces
variant enumeration and explicit entailment-vs-authorization reasoning); on an
already-constrained prompt the baseline nearly matches, so that case is the least
discriminating. The design-analysis pass costs additional time and tokens.

## Upgrade Notes

- Existing older specs remain compatible. `spec.yaml` continues to represent
  pre-generation intent; review/audit state lives in `review.yaml`.
- Narrow changes may skip the full multi-agent process, but the skip reason should
  be recorded. Substantial changes must pass the review gate before release.
