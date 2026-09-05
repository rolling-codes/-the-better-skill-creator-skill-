# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-30

Adds an independent multi-agent review system and adversarial completion gate for
complex skill creation and substantial updates. This is a major release because
the review gate now blocks packaging of complex skills that lack a passing
`review.yaml`.

### Added

- Fresh-context review roles for outcome interpretation, adversarial scope,
  architecture/validation, and completion-adversary review.
- `references/independent-review.md` to document adaptive activation,
  independence requirements, synthesis, and the completion gate.
- `scripts/review.py`, `scripts/review_gate.py`, and
  `scripts/stages/review_stage.py` for recording review state and enforcing the
  gate in the package pipeline.
- Behavioral coverage for RPG variant discrimination, log-fix
  entailment-vs-authorization, no-modification constraints, narrow
  description-only edits, simple-skill requests, ambiguous requests, and
  development-log review behavior.

### Changed

- `SKILL.md` now requires independent review for complex skills and substantial
  updates, while allowing narrow edits to record a skip reason.
- `skill.yaml` declares the new reviewer agents, review scripts, and
  independent-review reference so progressive disclosure can discover them.
- Bumped version to 2.0.0 in `.claude-plugin/plugin.json`,
  `skills/skill-creator/skill.yaml`, and the README release badge.

### Fixed

- `PackageStage` now fails closed on error-severity diagnostics before writing a
  `.skill`, preventing callers from bypassing an unresolved review gate.
- Python 3.8 compatibility for scripts that used runtime `list[...]`/`dict[...]`
  annotations.

### Validation

- The v2.0.0 review system was applied to itself: the completion adversary
  returned `verdict: complete`, its three low-severity findings were disposed in
  `review.yaml`, and `review_gate.py` passed.
- Offline validation passed: `quick_validate`, `lint`, `static_analysis`,
  `review_gate`, architecture score 95/100, and 16/16 pipeline tests.
- Live previous-vs-new evaluation over three representative prompts scored 100%
  with-skill vs 41.7% baseline.

## [1.10.0] - 2026-08-30

Makes Design Analysis *adaptive and bounded*. v1.9.0 told the model to work every
angle in order, which invites mechanical checklists and over-scoping — the opposite of
the flat scoping it cured. This release adds focus, a permission guardrail, and a
stopping rule.

### Added

- **Adaptive lenses** (`references/design-analysis.md`): an always-evaluate core
  (outcome, material interpretations, necessary entailments, boundaries & authorization,
  validation) plus evaluate-when-relevant lenses (accessibility, security, performance,
  persistence, creative direction, integration, multi-user, error recovery). The model
  justifies each lens it picks up; an unused lens is focus, not omission.
- **Entailment ≠ permission.** Discovered work is classified required-and-authorized
  (do it), required-but-unauthorized (identify and ask), optional (recommend, never add
  silently), or out-of-scope (exclude). Recorded in a new
  `SkillSpec.authorization_boundaries` field. Prevents multi-angle reasoning from
  becoming uncontrolled or unauthorized scope expansion.
- **Scope-selection matrix** (goal fit, evidence, complexity, reversibility, risk,
  clarification need) to choose among interpretations by reasoning, not listing.
- **Design brief** — new `SkillSpec` fields `chosen_interpretation`,
  `optional_features`, `authorization_boundaries` (existing `interpretations` /
  `open_questions` serve as alternatives-considered / decisive-questions).
- **Contradiction handling** and a **stopping rule** in the doctrine: explicit user
  constraints win and compromises are recorded; the analysis stops once another lens
  wouldn't change the architecture.
- **Adversarial behavioral tests** in `tests/expected_behavior.yaml`: nine prompts that
  check for both under- and over-scoping and for permission boundaries ("diagnose but
  do not modify", "only change the CSS", "make a simple skill, no optional systems").

### Changed

- `scripts/confidence.py` `assess_spec` now flags entailed work with no
  `authorization_boundaries` ("assumed all entailed work is authorized") and multiple
  interpretations with no `chosen_interpretation`.
- Bumped version to 1.10.0 in `.claude-plugin/plugin.json`, `skill.yaml`, and the
  README release badge.

## [1.9.1] - 2026-08-30

Completes the v1.9.0 Design Analysis feature — the scoring was authored but not
fully wired, and the compatibility story needed fixing.

### Fixed

- **`assess_spec` is now reachable.** `scripts/confidence.py`'s CLI only called
  `assess_skill`; the flat-scope scoring in `assess_spec` was dead code. The CLI now
  also assesses `spec.yaml` when present and gates on the lower of the two scores.
- **Back-compatible validation.** v1.9.0 added `outcome`/`entailments` to
  `missing_fields()`, so `spec validate` hard-failed specs authored before those
  fields existed — contradicting the "loads unchanged" claim. `missing_fields()` is
  back to the original core set; a new `missing_design_fields()` reports
  `outcome`/`entailments` as a **non-fatal warning** (exit 2), not an error.
- **Behavioral tests updated.** `tests/expected_behavior.yaml` still encoded the old
  question-first flow. It now covers the design-analysis behavior: RPG variant
  enumeration, log→diagnose→patch→verify entailment expansion, stated assumptions,
  and flexibility-without-vagueness scope control.

### Changed

- Bumped version to 1.9.1 in `.claude-plugin/plugin.json`,
  `skills/skill-creator/skill.yaml`, and the README release badge.

## [1.9.0] - 2026-08-30

Turns the Skill Creator from a request-transcriber into a design-and-reasoning
system. When creating or improving a skill it now scopes the *outcome* from
multiple angles before choosing a structure, instead of converting the literal
wording into a basic instruction file. "Build me an RPG skill" is treated as a
family of very different skills (flat narrative vs. persistent campaign with
world-state and progression); "watch my logs" is scoped as detect → diagnose →
patch → verify, not a log grepper.

### Added

- **Gate 1 reframed to Design Analysis** in `SKILL.md`, backed by a new
  `skills/skill-creator/references/design-analysis.md` doctrine: work an angle
  checklist (real outcome, valid interpretations, modes, cross-cutting
  requirements, entailments, failure points, self-validation), compare, decide
  what's in scope, then architect. Bias flipped from ask-heavy to analyze-first —
  make and *state* assumptions when intent is safe to infer; ask a focused
  question only when two interpretations would produce substantially different
  skills.
- **Design-analysis fields on `SkillSpec`** (`scripts/spec.py`): `outcome`,
  `interpretations`, `modes`, `entailments`, `failure_points`, `validation`,
  `assumptions`, `open_questions`. `outcome` and `entailments` are now required
  for a complete spec.
- **Flat-scope scoring** in `scripts/confidence.py`: an outcome that was never
  expanded into entailments, or unresolved decisive `open_questions`, now lowers
  confidence and is surfaced as an inferred assumption.
- A Red Flags row for the "build the literal request" shortcut.

### Changed

- Bumped version to 1.9.0 in `.claude-plugin/plugin.json`,
  `skills/skill-creator/skill.yaml`, and the README release badge.

## [1.8.1] - 2026-08-30

### Documentation

- Clarified that `scripts/dependency_graph.py` is an optional inspection tool:
  the skill-creator workflow and packaging pipeline do not depend on it, and it
  has no connection to any external graph service. Documentation only, no
  behaviour or wiring change.

### Changed

- Bumped version to 1.8.1 in `.claude-plugin/plugin.json`,
  `skills/skill-creator/skill.yaml`, and the README release badge.

## [1.8.0] - 2026-08-30

Fixed a wiring regression in the v1.2-v1.7 features: `generators/`,
`static_analysis.py`, `lint.py`, `dependency_graph.py`, `migrate_skill.py` and
`generate_report.py` were documented in the README but never referenced in
`SKILL.md`, so under progressive disclosure Claude could not discover them — the
same defect this fork was built to remove, reintroduced a layer up. Also
tightened the linter rules so the regression cannot recur. See
`skills/skill-creator/CHANGELOG.md` for component-level detail.

### Fixed

- Wired all six orphaned features into `SKILL.md` (Reference files section,
  Validation Pipeline, and a scaffolding note for the generators).
- README: static analysis runs via `LintStage`, not a `StaticAnalysisStage`;
  linter check count corrected from eight to nine.
- Python 3.8 compatibility in `package_skill.py` and `skill_test.py`
  (`from __future__ import annotations` for `list[...]` subscripts).
- `tests/test_pipeline.py` no longer hardcodes an absolute `C:/Temp` skill path,
  so the suite runs on any checkout.

### Added

- `static_analysis.py` orphaned-file rule and `lint.py` reference-wiring
  completeness rule, both run in the package pipeline via `LintStage`, so a
  shipped-but-unreferenced file now fails the linter instead of shipping silently.

### Changed

- Bumped version to 1.8.0 in `.claude-plugin/plugin.json`,
  `skills/skill-creator/skill.yaml`, and the README release badge.

## [1.7.0] - 2026-08-26

Version-alignment release. `1.7.0` was chosen to sit above the highest existing
GitHub release tag (`v1.6.0`) so the release marked "Latest" points at the code
actually shipping on `main`. The earlier `v1.0.0`–`v1.6.0` tags were cut from an
earlier packaging of this same project on a since-reinitialized git history, so
they share no commit ancestor with the current tree even though they carry the
same project's version numbers — the content history those numbers refer to is
the set of entries below, plus `skills/skill-creator/CHANGELOG.md`. No functional
changes over 1.4.0.

### Changed

- Bumped version to 1.7.0 in `.claude-plugin/plugin.json`, `skills/skill-creator/skill.yaml`,
  and the README release badge.

## [1.4.0] - 2026-08-26

Tightens SKILL.md and closes the Gate 3 gap the fork advocated but never applied
to itself.

### Added

- **Iron law and Red Flags table** in `SKILL.md`. The README described Gate 3
  (one non-negotiable rule phrased as reasoning, plus a table of rationalizations
  paired with correct behaviour) as the fix for imperative fragility and the
  excuse trap, but the skill itself had neither. The iron law is that a skill is
  never reported as better without a baseline run from the same iteration,
  because with-skill output that looks good on its own does not show the skill
  caused it. The seven table rows are drawn from the shortcuts this loop actually
  invites, most of which SKILL.md previously addressed as scattered one-line
  pleas ("don't stop partway through", "this is the only opportunity to capture
  this data", "please use generate_review.py").
- `references/description-optimization.md` — the trigger-eval and
  description-tuning loop, extracted from `SKILL.md` with a table of contents,
  a pointer back to `references/environments.md` for the no-subprocess case, and
  an entry in both the Reference files section and `skill.yaml` dependencies.

### Changed

- **`SKILL.md` cut from 500 to 446 lines.** The 73-line Description Optimization
  section moved to `references/`, following the same extraction pattern already
  used for environments. Remaining trims were duplicated or ornamental prose: the
  closing recap restated the opening summary, and three short paragraphs were
  merged.
- **`scripts/validate_all.sh` now runs the offline checks it claimed to.** It ran
  `quick_validate.py` and `skill_test.py` only, skipping `lint.py` and
  `static_analysis.py`, and invoked scripts by file path, which breaks the
  `scripts.skill_ir` import for the module-based ones. It now runs all three
  offline checks as modules from inside the skill directory, treats exit 2
  (warnings only) as a pass, skips the live trigger tests with an explicit
  message when the `claude` CLI is absent instead of failing, and returns a
  non-zero exit if any check genuinely failed.

### Fixed

- **Wrong flag documented.** The Reference files section told the model to grade
  expected behaviour with `--transcript`. The actual flag is
  `--grade-transcript <path>`, so the documented invocation would have been
  rejected by the argument parser.

### Note on the Robustness score

Robustness rose from 60 to 90, and the overall score from 92 to 95. Read that
carefully: `scripts/score.py` awards 20 points for the body matching the regex
`red flags?` and 10 for `iron law`, so the metric can be moved by typing two
headings. The content added here is meant to earn the points, but the rubric
would not have noticed the difference. Tightening that rule to require an actual
table with a rationalization column is open work.

---

## [1.3.1] - 2026-08-26

Repository consistency and linter-signal fixes. No change to skill behaviour.

### Fixed

- **Plugin install was broken.** `.claude-plugin/marketplace.json` declared the
  plugin as `skill-architect` in a marketplace named `skill-architect-local`,
  while `.claude-plugin/plugin.json` declared `skill-creator`. The documented
  install command matched neither, so `claude plugin install` failed. Both
  manifests now agree on `skill-creator@skill-creator-local`.
- **Pre-commit hook never ran.** It matched staged paths against
  `skill-creator/`, but the skill lives at `skills/skill-creator/`, so the
  condition was never true. It also invoked `python3 -m scripts.lint` from the
  repo root, where no `scripts` package exists. The hook now resolves the repo
  root via `git rev-parse`, uses the correct path, runs both checks from inside
  the skill directory, and fails loudly if the configured directory is missing.
- **Undeclared PyYAML dependency.** The README claimed standard library only,
  but six modules import `yaml`. Added `requirements.txt` and corrected the
  README and SETUP.md. `quick_validate.py` and `skill_ir.py` now fail with an
  install hint instead of a bare `ModuleNotFoundError`.
- **License conflict.** `plugin.json` declared MIT while `LICENSE.txt` is
  Apache 2.0. `plugin.json` now declares `Apache-2.0`.
- **Version drift.** README badge said 1.0.0, root changelog stopped at 1.1.0,
  `plugin.json` said 1.2.0, `skill.yaml` said 1.3.0. All now agree.
- **SETUP.md described a different project.** It documented `skill-architect`
  install commands and a `/skill-architect` verification step, neither of which
  exist here. Rewritten against the actual plugin.
- **Stage list was incomplete.** `SKILL.md` and the skill changelog both said
  "seven concrete stage wrappers" and then listed six. `DependencyStage` was
  missing.
- **Attribution.** `skill.yaml` credited Anthropic as author while
  `plugin.json` credited RollingCodes. `skill.yaml` now names the fork.

### Changed

- **`unreachable-section` narrowed** (`scripts/static_analysis.py`). It flagged
  any heading not cross-linked, which fired on 23 of ~25 sections of this
  skill's own SKILL.md. A linear procedural document is read top to bottom, so
  the rule now only applies to documents that actually navigate by anchor link
  (three or more), skips `Step N` headings, and considers top-level sections only.
- **`workflow-no-output` narrowed** (`scripts/lint.py`). It matched every
  markdown numbered list, including interview questions and concept
  enumerations. It now only inspects numbered lines inside sections whose
  heading names a process, skips questions, and requires the line to begin with
  an imperative verb.
- **Findings are capped per rule.** New `_cap()` helper in
  `static_analysis.py` shows the first five findings for a rule plus a count of
  the rest, with a note that a rule firing this often is usually too broad. This
  is the same non-discriminating-signal problem `agents/analyzer.md` warns about
  in evals, applied to the linters themselves. Combined effect on this skill:
  static analysis went from 35 findings to 1, lint from 17 to 7.

### Known issues

- `SKILL.md` is 500 lines, exactly on the progressive-disclosure guidance
  boundary rather than comfortably under it. The README claim of 463 lines was
  stale and has been corrected to the true figure.

---

## [1.1.0] - 2026-07-12

Six architectural improvements implemented from the roadmap.

### Added

- **Intermediate Representation** (`scripts/skill_ir.py`) — `Skill` dataclass as
  the canonical in-memory model for a skill. All scripts now parse through
  `Skill.from_path()` rather than each doing their own frontmatter/yaml parsing.
  `scripts/utils.py`'s `parse_skill_md()` delegates here, keeping existing callers
  unchanged.

- **Formal dependency graph** (`scripts/dependency_graph.py`) — `SkillGraph` class
  that builds a directed node graph from `skill.yaml` dependencies and backtick
  references in SKILL.md. Supports cycle detection (DFS), missing-node audit,
  impact analysis (reverse traversal), and export to JSON or Graphviz DOT.
  `python -m scripts.dependency_graph <path> [--format json|dot|summary]`

- **Static analysis** (`scripts/static_analysis.py`) — shared `Finding` datatype
  (severity + rule + message + line) plus five semantic rules: `dead-reference`,
  `missing-asset`, `unused-tool`, `unreachable-section`, `recursive-call`. Wired
  into `package_skill.py` after validation — error-severity findings block packaging.

- **Skill linter** (`scripts/lint.py`) — eight content-quality rules:
  `description-length`, `description-no-trigger`, `description-no-boundary`,
  `token-budget`, `missing-example`, `missing-reference-section`,
  `frontmatter-missing-tools`, `workflow-no-output`. Exit 0 = clean, 1 = errors
  (blocks commit), 2 = warnings only (commit proceeds). Wired into the pre-commit
  hook alongside `quick_validate.py`.

- **Versioned skill schema** (`schemaVersion` frontmatter field,
  `scripts/migrations/`, `scripts/migrate_skill.py`) — `schemaVersion: 1` added
  to `skill.yaml` and accepted by `quick_validate.py`. Migration registry maps
  `(from, to)` pairs to functions; `v1_to_v2.py` is the identity template.
  `python -m scripts.migrate_skill <path> --to <version> [--dry-run]`

- **Plugin architecture** (`generators/`) — `GeneratorRegistry` with pluggable
  `Generator` base class. Three built-in archetypes: `default` (general-purpose),
  `python-skill` (pre-fills terminal/filesystem tools, creates `scripts/main.py`
  stub), `research` (pre-fills WebSearch/WebFetch, creates `references/overview.md`).
  `python -m generators --archetype python-skill --name my-skill --output ./skills/`

- **Pylance config** (`pyrightconfig.json` at repo root, `skills/skill-creator/`) —
  `extraPaths: ["skills/skill-creator"]` so Pylance resolves `scripts.*` and
  `generators.*` imports without false positives.

### Changed

- `skill.yaml` version bumped to `1.1.0`; `schemaVersion: 1` added; 12 new
  dependency entries for all new scripts and generators.
- `scripts/quick_validate.py`: `schemaVersion` added to `ALLOWED_PROPERTIES`.
- `scripts/package_skill.py`: static analysis runs after validation; errors block.
- `scripts/hooks/pre-commit`: `lint.py` runs alongside `quick_validate.py`;
  exit 2 (warnings) allows commit, exit 1 (errors) blocks it.
- `scripts/utils.py`: `parse_skill_md()` delegates to `Skill.from_path()`.

---

## [1.0.0] - 2026-07-12

Initial release of **skill-creator** — a meta-skill for Claude Code that handles
the full lifecycle of building, testing, and iteratively refining other skills.

### Added

- **Eval runner** (`scripts/run_eval.py`) — spawns Claude subprocesses against a
  set of test prompts and measures whether the skill description causes the skill
  to load. Produces per-query trigger rates so you can see exactly which prompts
  are flaky.

- **Optimization loop** (`scripts/run_loop.py`) — iterates on the skill description
  automatically, proposing rewrites after each eval round until trigger accuracy
  reaches a target threshold or a max iteration count is hit.

- **Description improver** (`scripts/improve_description.py`) — targeted rewriter
  for skill descriptions; can be run standalone when you only need to tune the
  triggering surface without a full eval loop.

- **Browser-based eval viewer** (`eval-viewer/generate_review.py` + `viewer.html`)
  — launches a local web UI that shows with-skill vs baseline outputs side by side,
  displays benchmark metrics, and collects structured user feedback. Use `--static`
  for headless environments.

- **Blind A/B comparison agents** (`agents/analyzer.md`, `comparator.md`,
  `grader.md`) — three specialist agents for objective evaluation: the comparator
  runs blind comparisons without knowing which version is which, the grader scores
  assertions in `expected_behavior.yaml`, and the analyzer flags non-discriminating
  evals and high-variance results.

- **Benchmark pipeline** (`scripts/aggregate_benchmark.py`,
  `scripts/generate_report.py`) — aggregates grading results across runs into
  `benchmark.json` with pass rates, token/timing statistics (mean ± stddev), and
  per-version deltas. Generates a human-readable markdown report.

- **Regression test suite** (`tests/should_trigger.yaml`,
  `tests/should_not_trigger.yaml`, `tests/expected_behavior.yaml`) — 10 positive
  and 9 near-miss negative test cases covering the full intent space; expected
  behaviour graded by the grader agent via `--grade-transcript`.

- **Skill packaging** (`scripts/package_skill.py`) — bundles a skill folder into
  a distributable `.skill` zip archive ready for sharing or installation.

- **Quick validator** (`scripts/quick_validate.py`) — read-only structural check
  of `SKILL.md` frontmatter, required fields, and lifecycle consistency. Runs in
  under a second; wired into the pre-commit hook and `validate_all.sh`.

- **JSON schema reference** (`references/schemas.md`) — complete field-by-field
  definitions for `evals.json`, `grading.json`, `history.json`, `benchmark.json`,
  `timing.json`, and `feedback.json`.

- **Environment adaptations** (`references/environments.md`) — instructions for
  using the skill in Claude Code, Claude.ai (no subagents), and Cowork (no browser),
  including how to update an already-installed skill.

- **Apache 2.0 license** — project is now explicitly open-source.

### Removed

- `skill-architect` six-gate pipeline (`skills/skill-architect/`) — replaced by
  the eval-driven `skill-creator` workflow. The six-gate approach (Evidence,
  Adversarial Elicitation, Trigger Contract, Iron Law, Self-Critique, Blast Radius,
  Variance Analysis) was effective for manual audits but lacked automated eval
  infrastructure; `skill-creator` covers the same quality goals with measurable,
  repeatable benchmarks.
