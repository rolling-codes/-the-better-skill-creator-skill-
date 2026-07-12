"""
Abstract Generator base class for the pluggable skill scaffolding system.

Each generator targets a specific skill archetype and produces a ready-to-use
skill directory with SKILL.md, skill.yaml, and archetype-specific stubs.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

import yaml

from scripts.skill_ir import Skill


class Generator(ABC):
    """Base class for all skill generators."""

    archetypes: ClassVar[list[str]] = []

    @abstractmethod
    def scaffold(self, name: str, description: str, output_path: Path) -> Skill:
        """
        Create a new skill directory at output_path/name.
        Returns the loaded Skill IR for the newly created skill.
        """
        ...

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _write_skill_md(
        self,
        skill_dir: Path,
        name: str,
        description: str,
        allowed_tools: list[str],
        body: str = "",
        schema_version: int = 1,
    ) -> None:
        fm = {
            "name": name,
            "description": description,
            "schemaVersion": schema_version,
        }
        if allowed_tools:
            fm["allowed-tools"] = allowed_tools
        fm_yaml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False).rstrip()
        content = f"---\n{fm_yaml}\n---\n{body}"
        (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")

    def _write_skill_yaml(
        self,
        skill_dir: Path,
        name: str,
        version: str = "0.1.0",
        dependencies: list[str] | None = None,
    ) -> None:
        data: dict = {
            "name": name,
            "version": version,
            "schemaVersion": 1,
        }
        if dependencies:
            data["dependencies"] = dependencies
        (skill_dir / "skill.yaml").write_text(
            yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
