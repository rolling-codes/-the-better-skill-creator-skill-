"""Shared utilities for skill-creator scripts."""

from pathlib import Path

from scripts.skill_ir import Skill


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a SKILL.md file, returning (name, description, full_content).

    Delegates to Skill.from_path() so all scripts share one parsing path.
    Signature kept identical to preserve existing callers.
    """
    skill = Skill.from_path(skill_path)
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    return skill.name, skill.description, content
