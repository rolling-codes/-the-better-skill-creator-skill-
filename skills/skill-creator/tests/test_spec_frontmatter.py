"""Frontmatter stays inside the Agent Skills spec, and allowed-tools uses real names."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path

# CI runs pytest from the repo root; make the skill's packages importable.
_sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

import subprocess
import sys
import textwrap
from pathlib import Path

from scripts.lint import _check_invalid_tool_names
import yaml

from scripts.quick_validate import _validate_frontmatter, validate_skill
from scripts.skill_ir import Skill, _read_allowed_tools

SKILL_ROOT = Path(__file__).resolve().parents[1]


def _skill(tmp_path: Path, frontmatter: str) -> Path:
    d = tmp_path / "probe-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        f"---\n{textwrap.dedent(frontmatter).strip()}\n---\n\n# Probe\n\nBody text.\n",
        encoding="utf-8",
    )
    return d


def test_top_level_schema_version_is_rejected(tmp_path):
    d = _skill(tmp_path, "name: probe-skill\ndescription: Probes things.\nschemaVersion: 1")
    ok, msg = validate_skill(d)
    assert not ok and "metadata" in msg


def test_schema_version_under_metadata_is_read(tmp_path):
    d = _skill(tmp_path, "name: probe-skill\ndescription: Probes things.\nmetadata:\n  schemaVersion: 3")
    assert validate_skill(d)[0]
    assert Skill.from_path(d).schema_version == 3


def test_rewrite_moves_legacy_key_and_keeps_other_fields(tmp_path):
    d = _skill(tmp_path, """
        name: probe-skill
        description: Probes things.
        license: MIT
        schemaVersion: 1
        metadata:
          owner: tom
        """)
    skill = Skill.from_path(d)
    assert skill.legacy_schema_key
    skill.write_skill_md()
    again = Skill.from_path(d)
    assert not again.legacy_schema_key
    assert again.license == "MIT"
    assert again.metadata == {"owner": "tom", "schemaVersion": 1}
    assert validate_skill(d)[0]


def test_allowed_tools_string_form_keeps_patterns_whole():
    assert _read_allowed_tools("Read Grep Bash(git add *), WebFetch") == [
        "Read", "Grep", "Bash(git add *)", "WebFetch"]


def test_lint_flags_non_tool_names(tmp_path):
    d = _skill(tmp_path, """
        name: probe-skill
        description: Probes things.
        allowed-tools:
          - filesystem.read
          - Read
          - Bash(git log *)
          - mcp__github__create_issue
        """)
    flagged = [f.message for f in _check_invalid_tool_names(Skill.from_path(d))]
    assert len(flagged) == 1 and "filesystem.read" in flagged[0]


def test_generated_skills_pass_validation(tmp_path):
    listing = subprocess.run([sys.executable, "-m", "generators", "--list"],
                             cwd=SKILL_ROOT, capture_output=True, text=True, check=True).stdout
    archetypes = [ln.strip() for ln in listing.splitlines() if ln.startswith("  ") and ln.strip()]
    assert archetypes
    for kind in archetypes:
        out = tmp_path / kind
        subprocess.run(
            [sys.executable, "-m", "generators", "--name", f"gen-{kind}",
             "--archetype", kind, "--output", str(out)],
            cwd=SKILL_ROOT, capture_output=True, text=True, check=True,
        )
        created = next(out.rglob("SKILL.md")).parent
        # Frontmatter only: some archetypes also write an empty tests/ dir,
        # which is a separate known issue tracked outside this test.
        text = (created / "SKILL.md").read_text(encoding="utf-8")
        fm = yaml.safe_load(text.split("---")[1])
        ok, msg = _validate_frontmatter(fm, fm.get("name", ""))
        assert ok, f"{kind}: {msg}"
        assert not _check_invalid_tool_names(Skill.from_path(created)), kind


def test_shipped_skills_have_spec_frontmatter():
    for d in (SKILL_ROOT, SKILL_ROOT.parents[1] / "examples" / "release-notes"):
        ok, msg = validate_skill(d)
        assert ok, f"{d}: {msg}"
        assert not _check_invalid_tool_names(Skill.from_path(d))
