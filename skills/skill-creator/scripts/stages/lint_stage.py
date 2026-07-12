from __future__ import annotations
from scripts.compiler_context import CompilerContext
from scripts.static_analysis import analyze
from scripts.lint import lint


class LintStage:
    name = "lint"
    requires = {"skill_spec"}
    provides = {"diagnostics"}

    def run(self, ctx: CompilerContext) -> None:
        ctx.diagnostics.extend(analyze(ctx.skill_spec))
        ctx.diagnostics.extend(lint(ctx.skill_spec))
