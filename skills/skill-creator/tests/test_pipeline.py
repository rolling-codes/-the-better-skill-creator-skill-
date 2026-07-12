"""Tests for the v1.3.0+ compiler pipeline architecture."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.compiler_context import CompilerContext, RepairProposal, StageTrace
from scripts.pipeline import AgentStage, StageRegistry
from scripts.stages import DependencyStage, LintStage, SemanticStage, RepairStage, ScoreStage, PackageStage

SKILL_PATH = Path("C:/Temp/bsc-update/skills/skill-creator")


def test_context_creation():
    ctx = CompilerContext.create(SKILL_PATH)
    assert ctx.skill_spec is not None
    assert isinstance(ctx.skill_path, Path)
    assert ctx.diagnostics == []
    assert ctx.repairs == []
    assert ctx.score is None
    assert ctx.output_path is None


def test_stage_order():
    execution_log = []

    class OrderStage:
        def __init__(self, stage_name):
            self.name = stage_name
            self.requires = set()
            self.provides = set()
        def run(self, ctx):
            execution_log.append(self.name)

    registry = StageRegistry()
    registry.register(OrderStage("alpha"))
    registry.register(OrderStage("beta"))
    registry.register(OrderStage("gamma"))

    ctx = CompilerContext.create(SKILL_PATH)
    registry.run_all(ctx)

    assert execution_log == ["alpha", "beta", "gamma"]


def test_lint_stage_populates_diagnostics():
    ctx = CompilerContext.create(SKILL_PATH)
    LintStage().run(ctx)
    assert len(ctx.diagnostics) > 0
    valid_severities = {"error", "warning", "info"}
    for f in ctx.diagnostics:
        assert f.severity in valid_severities


def test_repair_stage_no_filesystem_writes():
    ctx = CompilerContext.create(SKILL_PATH)
    skill_md = SKILL_PATH / "SKILL.md"
    LintStage().run(ctx)
    SemanticStage().run(ctx)
    mtime_before = skill_md.stat().st_mtime
    RepairStage().run(ctx)
    mtime_after = skill_md.stat().st_mtime
    assert mtime_before == mtime_after, "RepairStage must not write to disk"
    assert isinstance(ctx.repairs, list)


def test_run_until():
    ctx = CompilerContext.create(SKILL_PATH)
    registry = StageRegistry()
    registry.register(LintStage())
    registry.register(SemanticStage())
    registry.register(ScoreStage())
    registry.run_until(ctx, "semantic")
    assert len(ctx.diagnostics) > 0
    assert ctx.score is None


def test_stage_trace_populated():
    ctx = CompilerContext.create(SKILL_PATH)
    registry = StageRegistry()
    registry.register(LintStage())
    registry.run_all(ctx)
    assert len(ctx.trace) == 1
    t = ctx.trace[0]
    assert t.stage_name == "lint"
    assert t.elapsed_ms >= 0
    assert t.diagnostics_added == len(ctx.diagnostics)
    assert isinstance(t, StageTrace)


def test_dependency_stage_no_errors_on_valid_skill():
    ctx = CompilerContext.create(SKILL_PATH)
    DependencyStage().run(ctx)
    missing = [f for f in ctx.diagnostics if f.rule == "missing-dependency"]
    assert missing == [], f"Unexpected missing deps: {missing}"


def test_agent_stage_uses_fallback():
    ctx = CompilerContext.create(SKILL_PATH)
    fallback_ran = []

    class StubFallback:
        name = "stub"
        requires: set = set()
        provides: set = set()

        def run(self, _ctx):
            fallback_ran.append(True)

    agent = AgentStage(
        name="test-agent",
        requires=set(),
        provides=set(),
        model="sonnet",
        prompt_template="",
        fallback=StubFallback(),
    )
    agent.run(ctx)
    assert fallback_ran == [True]


def test_agent_stage_raises_without_fallback():
    ctx = CompilerContext.create(SKILL_PATH)
    agent = AgentStage(
        name="no-fallback",
        requires=set(),
        provides=set(),
        model="sonnet",
        prompt_template="",
    )
    with pytest.raises(NotImplementedError):
        agent.run(ctx)
