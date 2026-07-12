from __future__ import annotations
from scripts.compiler_context import CompilerContext
from scripts.semantic_analysis import semantic_analyze


class SemanticStage:
    name = "semantic"
    requires = {"skill_spec"}
    provides = {"diagnostics"}

    def run(self, ctx: CompilerContext) -> None:
        ctx.diagnostics.extend(semantic_analyze(ctx.skill_spec))
