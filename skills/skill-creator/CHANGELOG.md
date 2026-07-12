# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  `RepairStage`, `ApplyRepairsStage`, `ScoreStage`, `PackageStage`
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
