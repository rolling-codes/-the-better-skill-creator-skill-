from __future__ import annotations
from scripts.compiler_context import CompilerContext
from scripts.score import score


class ScoreStage:
    name = "score"
    requires = {"skill_spec", "diagnostics"}
    provides = {"score"}

    def run(self, ctx: CompilerContext) -> None:
        ctx.score = score(ctx.skill_spec, ctx.diagnostics)
