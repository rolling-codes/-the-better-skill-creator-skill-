# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.6.0] - 2026-07-17

### Added
- `scripts/check_upstream.py` — reports drift against Anthropic's upstream skill-creator (upstream-only, local-only, changed files); run before each release
- `scripts/ci/validate.yml` — GitHub Actions workflow for validation on push and weekly drift watch
- `tests/meta/test_validators.py` — mutation tests: breaks each validator guard in a throwaway copy and asserts it fires; proves pass-everything/fail-everything/pass-list grader strategies are rejected, fabricated quotes demote, and Wilson math is correct; suite now covers 19 attacker strategies
- `NOTICE` file for Apache 2.0 attribution

### Changed
- **Canary hardening in `skill_test.py`**: replaced self-announcing canary with disguised integrity probes in both polarities — negative probes assert randomly-named artifacts absent from transcript, positive probes quote snippets sampled from it; shuffled into real expectations each run so neither wording nor position identifies them; `audit_grading` rejects runs where any probe is missing, a must-fail probe passes, or a must-pass probe fails
- **Mechanical quote verification**: passed assertions must cite a verbatim transcript quote (whitespace-normalized substring match, 15-char minimum); unverifiable quotes demote to failed; majority of fabrications rejects the whole run
- **Audit freshness enforcement in `quick_validate.py`**: warn when `last-audit` is >30 days old, hard-fail >90 days so a stale audit can't ride along silently
- **Reachability invariant in `quick_validate.py`**: any `references/` file or governance doc (LIFECYCLE.md, PERMISSIONS.md) not mentioned in SKILL.md is flagged as unreachable dead weight; closes the orphan-file failure mode from the 2026-07 audit
- **Removal detection in `quick_validate.py`**: three-direction check — dangling doc pointers, unregistered files, PERMISSIONS rows out of sync with scripts; any add or remove not reflected everywhere fails immediately
- `references/dependency-graph.md` updated with new scripts (check_upstream.py, validate.yml, tests/meta/test_validators.py)
- `references/trigger-confidence.md` updated with Wilson score interval documentation
- `scripts/validate_all.sh` updated to include meta tests via pytest

## [1.4.0] - 2026-07-15

### Added
- Self-checking validation: linter now validates skill-creator's own SKILL.md to catch regressions
- GitHub Actions CI workflow for automated testing on every push and PR
- Static analysis script for deeper structural checks beyond quick_validate
- Regression test suite wired into validate_all.sh for end-to-end testing
- Execution timing and trace logging in CompilerContext stages for observability

### Fixed
- CHANGELOG now properly documents all releases including v1.2.0 and v1.3.0
- Missing v1.2.0 release tag added retroactively
- Validate_all.sh now includes regression tests in CI/CD pipeline
- Pre-commit hooks properly integrated with validation scripts

### Changed
- Updated version in skill.yaml from 1.0.0 to 1.4.0
- Improved observability with stage-level timing traces

## [1.3.0] - 2026-07-12

### Added
- CompilerContext IR and multi-stage architecture
- StageRegistry for managing skill compilation stages
- Seven-stage compilation pipeline (parse, analyze, validate, optimize, generate, package, deploy)
- Integration with analyzer, comparator, and grader agents
- Regression test suite (5 tests in test_pipeline.py) for end-to-end validation
- Progressive disclosure system for skill resources
- Eval viewer for visual review of evaluation results

### Fixed
- Wired orphaned files into SKILL.md reference section for progressive disclosure
- Moved Claude.ai/Cowork sections to references/environments.md to keep SKILL.md concise
- Expanded trigger test coverage to 10 positives / 9 near-miss negatives
- Added --grade-transcript mode to skill_test.py for behavioral validation via agents

### Changed
- Restructured documentation for clarity
- Added --grade-transcript to skill_test.py for objective behavioral grading

## [1.2.0] - 2026-07-08

### Added
- New skills created using the skill-creator framework
- Workflow capture for repeatable skill creation

### Changed
- Skill creation workflow documentation improved

## [1.0.0] - 2026-01-01

### Added
- Initial release of skill-creator
- Core skill creation workflow (research, planning, testing, iteration)
- SKILL.md template and guidelines
- Test-driven evaluation system
- Support for quantitative benchmarking
- Skill description optimization tools
- Bundled resources support (scripts, references, assets)
- Progressive disclosure for skill loading

### Changed
- Initial stable API

[Unreleased]: https://github.com/anthropics/claude-code/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/anthropics/claude-code/compare/v1.4.0...v1.6.0
[1.4.0]: https://github.com/anthropics/claude-code/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/anthropics/claude-code/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/anthropics/claude-code/compare/v1.0.0...v1.2.0
[1.0.0]: https://github.com/anthropics/claude-code/releases/tag/v1.0.0
