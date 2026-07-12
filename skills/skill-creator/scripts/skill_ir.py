#!/usr/bin/env python3
"""
Skill Intermediate Representation (IR) — canonical in-memory model for a skill.

All scripts that need to read skill state should use Skill.from_path() rather
than parsing SKILL.md and skill.yaml independently.
"""
from __future__ import annotations

import re
import yaml
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Skill:
    """Canonical in-memory representation of a Claude Code skill."""
    name: str
    description: str
    allowed_tools: list[str]
    schema_version: int          # from schemaVersion frontmatter field (default 1)
    compatibility: Optional[str]
    skill_path: Path
    body: str                    # SKILL.md content after the closing ---
    yaml_data: dict              # raw skill.yaml dict; empty {} if file absent
    dependencies: list[str]      # from skill.yaml dependencies list
    lifecycle: Optional[str]
    version: Optional[str]
    author: Optional[str]

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_path(cls, skill_path) -> "Skill":
        """Load a Skill from a directory that contains SKILL.md."""
        skill_path = Path(skill_path).resolve()
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"SKILL.md not found in {skill_path}")

        content = skill_md.read_text(encoding="utf-8")
        if not content.startswith("---"):
            raise ValueError("SKILL.md missing opening --- frontmatter delimiter")

        # Find closing ---
        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break
        if end_idx is None:
            raise ValueError("SKILL.md frontmatter has no closing ---")

        fm_text = "\n".join(lines[1:end_idx])
        body = "\n".join(lines[end_idx + 1:])

        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in frontmatter: {exc}") from exc
        if not isinstance(fm, dict):
            raise ValueError("Frontmatter must be a YAML mapping")

        # skill.yaml (optional)
        yaml_data: dict = {}
        syp = skill_path / "skill.yaml"
        if syp.exists():
            try:
                yaml_data = yaml.safe_load(syp.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML in skill.yaml: {exc}") from exc

        deps = yaml_data.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []

        return cls(
            name=str(fm.get("name", "")).strip(),
            description=str(fm.get("description", "")).strip(),
            allowed_tools=list(fm.get("allowed-tools") or []),
            schema_version=int(fm.get("schemaVersion", 1)),
            compatibility=fm.get("compatibility") or None,
            skill_path=skill_path,
            body=body,
            yaml_data=yaml_data,
            dependencies=[str(d) for d in deps],
            lifecycle=yaml_data.get("lifecycle") or None,
            version=str(yaml_data.get("version", "")) or None,
            author=str(yaml_data.get("author", "")) or None,
        )

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_frontmatter_dict(self) -> dict:
        """Return ordered dict suitable for writing back to SKILL.md frontmatter."""
        fm: dict = {"name": self.name, "description": self.description}
        fm["schemaVersion"] = self.schema_version
        if self.allowed_tools:
            fm["allowed-tools"] = self.allowed_tools
        if self.compatibility:
            fm["compatibility"] = self.compatibility
        return fm

    def write_skill_md(self) -> None:
        """Serialise frontmatter + body back to SKILL.md (in-place)."""
        fm_yaml = yaml.dump(
            self.to_frontmatter_dict(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        ).rstrip()
        content = f"---\n{fm_yaml}\n---\n{self.body}"
        (self.skill_path / "SKILL.md").write_text(content, encoding="utf-8")
