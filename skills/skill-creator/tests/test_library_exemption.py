"""Orphan rule exempts imported libraries, never entry points or unimported files."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

# CI runs pytest from the repo root; make the skill's packages importable.
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import textwrap
from pathlib import Path

from scripts.skill_md_utils import find_library_modules
from scripts.skill_ir import Skill
from scripts.static_analysis import _check_orphaned_files


def _make_skill(root: Path) -> Path:
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "__init__.py").write_text("")
    (root / "SKILL.md").write_text(textwrap.dedent("""\
        ---
        name: probe
        description: Probe skill for orphan-rule tests.
        schemaVersion: 1
        ---

        # Probe

        ## Reference files

        - `scripts/runner.py` runs things.
        """))
    (root / "scripts" / "runner.py").write_text(textwrap.dedent("""\
        from scripts.helper import go
        from scripts.tool import main
        if __name__ == "__main__":
            go()
        """))
    (root / "scripts" / "helper.py").write_text("def go():\n    pass\n")
    (root / "scripts" / "tool.py").write_text(
        "def main():\n    pass\nif __name__ == '__main__':\n    main()\n")
    (root / "scripts" / "stray.py").write_text("x = 1\n")
    return root


def test_imported_library_is_exempt(tmp_path):
    libs = find_library_modules(_make_skill(tmp_path))
    assert "scripts/helper.py" in libs


def test_imported_entry_point_is_not_exempt(tmp_path):
    libs = find_library_modules(_make_skill(tmp_path))
    assert "scripts/tool.py" not in libs


def test_unimported_file_is_not_exempt(tmp_path):
    libs = find_library_modules(_make_skill(tmp_path))
    assert "scripts/stray.py" not in libs


def test_orphan_rule_flags_only_real_orphans(tmp_path):
    skill = Skill.from_path(_make_skill(tmp_path))
    flagged = {f.message.split("'")[1] for f in _check_orphaned_files(skill)}
    assert flagged == {"scripts/tool.py", "scripts/stray.py"}
