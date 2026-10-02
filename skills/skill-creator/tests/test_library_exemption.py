"""Orphan rule exempts imported libraries, never entry points or unimported files."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

# CI runs pytest from the repo root; make the skill's packages importable.
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import textwrap

import pytest
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


@pytest.mark.parametrize("statement", ["from .helper import go", "from . import helper"])
@pytest.mark.parametrize("importer", ["runner.py", "__init__.py"])
def test_relative_library_imports(tmp_path, statement, importer):
    root = _make_skill(tmp_path)
    (root / "scripts" / "runner.py").write_text("")
    (root / "scripts" / importer).write_text(statement + "\nfrom .tool import main\n")
    assert find_library_modules(root) == {"scripts/helper.py"}
    flagged = {f.message.split("'")[1] for f in _check_orphaned_files(Skill.from_path(root))}
    assert "scripts/helper.py" not in flagged
    assert "scripts/tool.py" in flagged


@pytest.mark.parametrize("statement", ["from ..helper import go", "from .. import helper"])
def test_parent_package_imports(tmp_path, statement):
    root = _make_skill(tmp_path)
    (root / "scripts" / "runner.py").write_text("")
    nested = root / "scripts" / "nested"
    nested.mkdir()
    (nested / "__init__.py").write_text("")
    (nested / "runner.py").write_text(statement + "\n")
    assert find_library_modules(root) == {"scripts/helper.py"}


def test_relative_import_does_not_match_absolute_or_escape_root(tmp_path):
    root = _make_skill(tmp_path)
    (root / "helper.py").write_text("x = 1\n")
    (root / "scripts" / "runner.py").write_text("from . import helper\nfrom ... import stray\n")
    assert find_library_modules(root) == {"scripts/helper.py"}


def test_mutual_import_cycle_not_exempt(tmp_path):
    """Closed import cycles with no external anchor do not earn library exemption."""
    root = _make_skill(tmp_path)
    (root / "scripts" / "cycle_a.py").write_text("from scripts.cycle_b import foo\n")
    (root / "scripts" / "cycle_b.py").write_text("from scripts.cycle_a import bar\n")
    libs = find_library_modules(root)
    assert "scripts/cycle_a.py" not in libs
    assert "scripts/cycle_b.py" not in libs
    assert "scripts/helper.py" in libs
