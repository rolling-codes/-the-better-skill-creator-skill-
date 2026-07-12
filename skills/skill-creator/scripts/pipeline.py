#!/usr/bin/env python3
"""
Pipeline stage protocol and registry.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional, Protocol, runtime_checkable

from scripts.compiler_context import CompilerContext, StageTrace


@runtime_checkable
class PipelineStage(Protocol):
    name: str
    requires: set[str]
    provides: set[str]

    def run(self, ctx: CompilerContext) -> None: ...


class StageRegistry:
    def __init__(self) -> None:
        self._stages: list[PipelineStage] = []

    def register(self, stage: PipelineStage) -> None:
        self._stages.append(stage)

    def stage_names(self) -> list[str]:
        return [s.name for s in self._stages]

    def _run_stage(self, stage: PipelineStage, ctx: CompilerContext) -> None:
        before_diag = len(ctx.diagnostics)
        before_repairs = len(ctx.repairs)
        before_applied = len(ctx.applied_fixes)
        t0 = time.monotonic()
        stage.run(ctx)
        ctx.trace.append(StageTrace(
            stage_name=stage.name,
            elapsed_ms=round((time.monotonic() - t0) * 1000, 1),
            diagnostics_added=len(ctx.diagnostics) - before_diag,
            repairs_proposed=len(ctx.repairs) - before_repairs,
            repairs_applied=len(ctx.applied_fixes) - before_applied,
        ))

    def run_all(self, ctx: CompilerContext) -> None:
        for stage in self._stages:
            self._run_stage(stage, ctx)

    def run_until(self, ctx: CompilerContext, stage_name: str) -> None:
        for stage in self._stages:
            self._run_stage(stage, ctx)
            if stage.name == stage_name:
                break


@dataclass
class AgentStage:
    """PipelineStage backed by an LLM agent. Satisfies PipelineStage Protocol structurally.

    When model routing infrastructure is available, run() dispatches to the
    configured model. Until then, run() delegates to fallback if provided.
    """
    name: str
    requires: set[str]
    provides: set[str]
    model: str
    prompt_template: str
    confidence_threshold: float = 0.7
    fallback: Optional[PipelineStage] = None

    def run(self, ctx: CompilerContext) -> None:
        if self.fallback is not None:
            self.fallback.run(ctx)
            return
        raise NotImplementedError(
            f"AgentStage '{self.name}': model routing not yet wired. "
            "Provide a fallback stage or implement model dispatch."
        )
