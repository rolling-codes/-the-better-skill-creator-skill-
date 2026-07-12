#!/usr/bin/env python3
"""
Pipeline stage protocol and registry.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from scripts.compiler_context import CompilerContext


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

    def run_all(self, ctx: CompilerContext) -> None:
        for stage in self._stages:
            stage.run(ctx)

    def run_until(self, ctx: CompilerContext, stage_name: str) -> None:
        for stage in self._stages:
            stage.run(ctx)
            if stage.name == stage_name:
                break
