from __future__ import annotations

from scripts.compiler_context import CompilerContext
from scripts.skill_ir import Skill


class ApplyRepairsStage:
    name = "apply_repairs"
    requires = {"repairs"}
    provides = {"applied_fixes", "skill_spec"}

    def run(self, ctx: CompilerContext) -> None:
        if not ctx.repairs:
            return

        current = ctx.skill_spec
        for proposal in ctx.repairs:
            updated = proposal.apply(current)
            if updated is not None:
                current = updated
                ctx.applied_fixes.append(proposal.description)

        if ctx.applied_fixes:
            current.write_skill_md()

        ctx.skill_spec = Skill.from_path(ctx.skill_path)
