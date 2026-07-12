"""
Python skill generator — archetype for skills that invoke Python scripts.

Pre-fills allowed-tools with filesystem + terminal access and creates a
scripts/main.py stub alongside the standard layout.
"""
from __future__ import annotations

from pathlib import Path

from generators.base import Generator
from scripts.skill_ir import Skill

_BODY = """\

## What it does

<!-- Describe what this skill does in 2-3 sentences. -->

## When to use it

<!-- Trigger clause: what user requests activate this skill? -->

## When NOT to use it

<!-- Boundary clause: what does this skill explicitly not cover? -->

## How it works

1. Read the input from the user.
2. Run `python -m scripts.main` with appropriate arguments.
3. Return the output to the user.

## Reference files

- `scripts/main.py` - entry point; run via `python -m scripts.main`

## Iron Law

<!-- State the one non-negotiable rule this skill enforces. -->
"""

_MAIN_PY = """\
#!/usr/bin/env python3
import sys


def main() -> int:
    print("Hello from skill")
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""


class PythonSkillGenerator(Generator):
    archetypes: list[str] = ["python-skill", "python", "script"]

    def scaffold(self, name: str, description: str, output_path: Path) -> Skill:
        skill_dir = output_path / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "tests").mkdir(exist_ok=True)

        self._write_skill_md(
            skill_dir,
            name=name,
            description=description,
            allowed_tools=["filesystem.read", "filesystem.write", "terminal.execute"],
            body=_BODY,
        )
        self._write_skill_yaml(
            skill_dir,
            name=name,
            dependencies=["scripts/main.py"],
        )
        (skill_dir / "scripts" / "main.py").write_text(_MAIN_PY, encoding="utf-8")
        (skill_dir / "scripts" / "__init__.py").write_text("", encoding="utf-8")

        return Skill.from_path(skill_dir)
