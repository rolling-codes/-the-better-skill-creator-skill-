# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-30

Adds an independent multi-agent review system and adversarial completion gate for
complex skill creation and substantial updates. Major bump: the review gate now
blocks packaging of a complex skill that lacks a passing `review.yaml`, which
changes the packaging contract for substantial skill work.

### Added

- `agents/outcome-analyst.md`, `agents/scope-adversary.md`,
  `agents/architecture-reviewer.md`, and `agents/completion-adversary.md` define
  the required fresh-context review roles.
- `references/independent-review.md` documents adaptive activation, independence
  requirements, synthesis without voting, and the completion gate.
- `scripts/review.py` adds a `ReviewRecord` IR stored in `review.yaml` for
  independent findings, disagreements, adversarial findings, dispositions,
  completion-gate status, accepted limitations, and unresolved decisive questions.
- `scripts/review_gate.py` deterministically detects missing required reports,
  undisposed high/material findings, invalid dispositions, unwired review agents,
  and completion claims before the gate has passed.
- `scripts/stages/review_stage.py` wires the review gate into the package
  pipeline.

### Changed

- `SKILL.md` now requires the review process for complex skills and substantial
  updates, while allowing narrow edits to record a skip reason.
- `skill.yaml` declares all new reviewer agents, review scripts, and the
  independent-review reference so progressive disclosure can discover them.
- `tests/expected_behavior.yaml` now includes the exact RPG, log-fix,
  no-modification, description-only, simple-skill, ambiguous-request, and
  development-log prompts from the v1.11 evaluation matrix.

### Fixed

- Added unit coverage for `SkillSpec` design-analysis scoring and review-gate
  behavior so the new system is validated by behavior, not just by shipped files.
- `PackageStage` now fails closed on error-severity diagnostics (e.g. an
  unresolved review gate) before writing the `.skill`, so the completion gate
  cannot be bypassed by a caller invoking `StageRegistry.run_all` directly rather
  than the `package_skill.py` driver; `review_stage.py`'s docstring corrected to
  locate the enforcement in both layers.
- Python 3.8 compatibility: added `from __future__ import annotations` to
  `aggregate_benchmark.py`, `generate_report.py`, `improve_description.py`,
  `run_eval.py`, `run_loop.py`, and `utils.py`, which used `list[...]`/`dict[...]`
  runtime annotations that raise `TypeError` on the project's stated minimum
  (Python 3.8).
- Review gate no longer requires skill-creator's own reviewer agent files in every
  packaged target: the `review-agent-missing`/`review-agent-unwired` checks now run
  only when the record activates the review, so a normal target skill (no
  `review.yaml`, no reviewer agents) still packages instead of failing with four
  spurious errors.
- Review gate rejects a `passed` completion gate whose completion-adversary verdict
  isn't `complete` (new `review-incomplete-verdict` error), closing a hole where a
  passed status could stand over an `incomplete` adversary verdict.
- `ReviewRecord.from_yaml` validates that `independent_findings`,
  `adversarial_findings`, and `finding_disposition` are lists of mappings, so a
  malformed entry surfaces as a clean `review-parse` diagnostic instead of an
  `AttributeError` mid-gate.
- Clarified in `SKILL.md` that the architecture-reviewer receives the proposed
  architecture sketch (not a finished `SKILL.md`), while the outcome-analyst and
  scope-adversary still receive no proposed solution — resolving a contradiction
  between the pre-draft "never your proposed solution" rule and that reviewer's
  input contract.

### Validation

- The review system was applied to this release itself. A fresh-context
  completion adversary attempted to prove the skill incomplete and returned
  `verdict: complete`; its three low-severity findings are recorded and disposed
  in `review.yaml` (two fixed — the development-log case and the `PackageStage`
  guard above; one accepted limitation — offline validation cannot prove real
  subagent independence). `review_gate.py` passes and `completion_gate_status` is
  `passed`.
- Live previous-vs-new evaluation over three representative prompts (RPG variant
  discrimination, log-fix entailment-vs-authorization, no-modification constraint),
  with-skill vs no-skill baseline, same model: pass rate 100% vs 41.7%
  (delta +0.58), at +39s and +19k tokens per run. The lift concentrates on the
  ambiguous prompts; the already-constrained prompt was least discriminating.

## [1.10.0] - 2026-08-30

Makes the Design Analysis stage adaptive and bounded, and adds the
entailment-is-not-permission guardrail.

### Added

- `references/design-analysis.md` restructured: adaptive lenses (always-evaluate core
  vs evaluate-when-relevant, justify each), an "Entailment is not permission" section
  with the four-way work classification, a scope-selection matrix, a design-brief
  template, contradiction handling (explicit user constraints win), and a stopping rule.
  Added a table of contents.
- `SkillSpec` (`scripts/spec.py`): `chosen_interpretation`, `optional_features`,
  `authorization_boundaries`. `to_dict`/`from_yaml` round-trip them; `coverage()` counts
  the meaningful ones; existing specs load unchanged.
- `scripts/confidence.py` `assess_spec`: raises an assumption when entailments exist but
  `authorization_boundaries` is empty (entailed work not classified for authorization),
  and a missing-info flag when `interpretations` has more than one entry but
  `chosen_interpretation` is empty.
- `tests/expected_behavior.yaml`: nine adversarial prompts asserting decisions —
  RPG variant discrimination (build / one-shot / persistent-with-ranks),
  entailment-vs-permission ("watch these logs and tell me what crashes",
  "diagnose but do not modify anything"), authorization boundaries
  ("only change the CSS; don't touch the backend"), and over-scoping guard
  ("make a simple skill, do not add optional systems").

### Changed

- `SKILL.md` Design analysis section rewritten to the adaptive-lens split with the
  entailment≠permission rule and the stopping rule; added a Red Flags row for treating
  entailment as authorization.

## [1.9.1] - 2026-08-30

Wires up and back-fills the v1.9.0 Design Analysis feature.

### Fixed

- `scripts/confidence.py` CLI now invokes `assess_spec` when a `spec.yaml` is present
  (previously it only ran `assess_skill`, leaving the flat-scope scoring unreachable
  from `python -m scripts.confidence`). It gates on the lower of the skill and spec
  scores.
- `scripts/spec.py`: `missing_fields()` reverted to the original core set so specs
  written before the design-analysis fields still validate; `outcome`/`entailments`
  moved to a new `missing_design_fields()` that `spec validate` reports as a warning
  (exit 2), not a hard failure (exit 1).
- `tests/expected_behavior.yaml`: replaced the question-first assertions with
  design-analysis behavior — variant enumeration ("Build me an RPG skill"), entailment
  expansion ("watch my logs" → detect → diagnose → patch → verify), stated assumptions,
  and tight-Boundary scope control.

## [1.9.0] - 2026-08-30

Adds a multi-angle **Design Analysis** scoping stage so the skill-creator designs
for the full problem space instead of transcribing the literal request.

### Added

- `references/design-analysis.md` — the scoping doctrine: an angle checklist (real
  outcome, valid interpretations, modes/use-cases, cross-cutting requirements,
  entailments, failure points, self-validation, infer-vs-clarify, flexibility
  without vagueness), a compare→decide→architect step, an ask-vs-assume rule, and
  two worked examples (a dev/logs skill and an RPG skill).
- `SkillSpec` (`scripts/spec.py`) gains `outcome`, `interpretations`, `modes`,
  `entailments`, `failure_points`, `validation`, `assumptions`, and
  `open_questions`. `missing_fields()` now requires `outcome` and `entailments`;
  `coverage()` counts the new fields (except `open_questions`, where empty is the
  goal). `to_dict`/`from_yaml` round-trip them; existing specs load unchanged.
- `assess_spec` (`scripts/confidence.py`) scores the design analysis: a stated
  outcome with no entailments is flagged as flat scope ("assumed the literal
  request is the whole job"), and unresolved decisive `open_questions` lower
  confidence.

### Changed

- `SKILL.md` Gate 1 / intent capture is now "Design analysis: scope the outcome
  from multiple angles," pointing at `references/design-analysis.md`. Bias flipped
  from ask-first to analyze-first with stated assumptions. Added a Red Flags row
  for the "build the literal request" shortcut.

## [1.8.1] - 2026-08-30

### Documentation

- `scripts/dependency_graph.py` is now documented as optional in both SKILL.md
  and the README: the workflow and packaging pipeline do not depend on it, and
  it reads only the skill's own files (no external graph service). No code change.

## [1.8.0] - 2026-08-30

Fixes the wiring regression this fork was created to prevent. The features added
across v1.2-v1.7 shipped in the repo but were never referenced in `SKILL.md`, so
progressive disclosure kept them invisible: Claude running the skill never
scaffolded with the generators, never invoked the linter or static analyzer, and
never migrated schemas. Neither of the fork's own wiring checkers caught it —
`static_analysis` only flagged references pointing at missing files, and `lint`
only checked that a Reference files section existed, not that it was complete.

(Entries 1.4.0 through 1.7.0 were tracked only in the repository-root
`CHANGELOG.md`; this file resumes the component-level history here.)

### Added

- **Orphaned-file rule** in `scripts/static_analysis.py` (`orphaned-file`): flags
  any file under `scripts/`, `agents/`, `references/`, or `generators/` that is
  never referenced in `SKILL.md`. This is the reverse of the existing
  dead-reference rule and runs in the package pipeline through `LintStage`.
- **Reference-wiring completeness rule** in `scripts/lint.py`
  (`unwired-dependency`): flags any `skill.yaml` dependency not linked from
  `SKILL.md`. Raises the linter from eight checks to nine.
- Shared `_is_referenced` / `_reference_forms` helpers matching the three ways
  `SKILL.md` names a script (path, `python -m` module, bare filename). Only
  nested directory references (e.g. `scripts/stages/`) cover their children, so a
  bare `scripts/` in ordinary prose cannot mask a real orphan.

### Fixed

- Wired the six orphaned features (`generators/`, `static_analysis.py`,
  `lint.py`, `dependency_graph.py`, `migrate_skill.py`, `generate_report.py`)
  into the `SKILL.md` Reference files section, Validation Pipeline, and a new
  "Scaffolding a skeleton" note.
- `README.md`: corrected the claim that static analysis runs as a
  `StaticAnalysisStage` (it runs inside `LintStage`) and the linter check count.
- Python 3.8 support: added `from __future__ import annotations` to
  `package_skill.py` and `skill_test.py`, whose `list[...]` annotations would
  raise at import on 3.8. Corrected `package_skill.py`'s stale `python utils/...`
  usage strings.
- `tests/test_pipeline.py`: resolve the skill path from `__file__` instead of a
  hardcoded `C:/Temp/bsc-update` path that made the suite pass only on one
  machine; fixed the `StubFallback` stage signature to match the `PipelineStage`
  protocol.

## [1.3.0] - 2026-07-12

### Added
- `CompilerContext` dataclass — shared mutable IR passed through all pipeline stages,
  carrying `skill_spec`, `diagnostics`, `repairs`, `applied_fixes`, `score`, and
  `output_path` (`scripts/compiler_context.py`)
- `RepairProposal` dataclass — a deferred repair closure that separates fix planning
  from filesystem mutation
- `StageRegistry` — executes registered `PipelineStage` implementations in order,
  with `run_all()` and `run_until()` entry points (`scripts/pipeline.py`)
- `PipelineStage` Protocol — structural interface all stage wrappers satisfy
- Seven concrete pipeline stages in `scripts/stages/`: `LintStage`, `SemanticStage`,
  `DependencyStage`, `RepairStage`, `ApplyRepairsStage`, `ScoreStage`, `PackageStage`
- `RepairStage` builds repair proposals without touching disk; `ApplyRepairsStage`
  is the sole filesystem-writing stage — enforces the proposal/apply split
- Five regression tests for the compiler pipeline in `tests/test_pipeline.py`

### Changed
- `package_skill.py` now orchestrates the pipeline via `CompilerContext` and stage
  instances rather than direct function calls; all observable behaviour preserved
- `.pytest_cache` excluded from packaged `.skill` archives

### Architecture note
v1.2.0 created skills. v1.3.0 compiles them. The stage/registry model decouples
*what* work happens from *who* performs it — future LLM-backed stages slot in by
replacing a stage's `run()` body; the registry and orchestrator are unchanged.

## [1.2.0] - 2026-07-07

### Added
- `scripts/spec.py` — pre-generation SkillSpec intent IR; writes `spec.yaml`
- `scripts/confidence.py` — requirement coverage + ambiguity score
- `scripts/semantic_analysis.py` — contradiction, duplicate-section, and
  inconsistent-terminology checks
- `scripts/repair.py` — deterministic auto-fix loop for known lint errors
- `scripts/score.py` — architecture scoring rubric (7 dimensions, 0–100 each)
- `scripts/generate_tests.py` — generates edge-case and malformed-input test scenarios
- All six scripts wired into `package_skill.py` compile pipeline
