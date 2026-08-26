# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
