# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
