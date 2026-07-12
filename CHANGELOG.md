# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
