#!/usr/bin/env python3
"""
Skill Specification (SkillSpec) — pre-generation intent IR.

Captures what a skill should be *before* any files are written.
Written to spec.yaml in the skill directory during creation.
The existing Skill IR (skill_ir.py) is the post-generation counterpart.

Usage:
    python -m scripts.spec validate <skill-path>   # check spec.yaml completeness
    python -m scripts.spec init <skill-path>        # write a blank spec.yaml
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class SkillSpec:
    """Pre-generation intent representation for a skill."""
    name: str
    purpose: str                       # one sentence: what problem this solves
    inputs: list[str]                  # what the skill receives
    outputs: list[str]                 # what the skill produces
    constraints: list[str]             # things the skill must/must not do
    dependencies: list[str]            # tools, MCPs, external resources needed
    examples: list[dict]               # [{"input": "...", "output": "..."}]
    workflows: list[str]               # ordered steps in the main workflow
    archetype: str = "default"         # which generator archetype to use

    # ------------------------------------------------------------------
    # Completeness helpers
    # ------------------------------------------------------------------

    def missing_fields(self) -> list[str]:
        """Return names of fields that are empty or absent."""
        missing = []
        if not self.name:
            missing.append("name")
        if not self.purpose:
            missing.append("purpose")
        if not self.inputs:
            missing.append("inputs")
        if not self.outputs:
            missing.append("outputs")
        if not self.workflows:
            missing.append("workflows")
        return missing

    def coverage(self) -> int:
        """Return completeness as 0–100 (% of non-empty fields)."""
        fields = [
            bool(self.name), bool(self.purpose), bool(self.inputs),
            bool(self.outputs), bool(self.constraints), bool(self.dependencies),
            bool(self.examples), bool(self.workflows),
        ]
        return int(100 * sum(fields) / len(fields))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "archetype": self.archetype,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "examples": self.examples,
            "workflows": self.workflows,
        }

    def to_yaml(self) -> str:
        return yaml.dump(
            self.to_dict(),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    def write(self, skill_path: Path) -> None:
        """Write spec.yaml into skill_path."""
        (skill_path / "spec.yaml").write_text(self.to_yaml(), encoding="utf-8")

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> "SkillSpec":
        """Load a SkillSpec from a spec.yaml file."""
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(data, dict):
            raise ValueError("spec.yaml must be a YAML mapping")
        return cls(
            name=str(data.get("name", "")).strip(),
            purpose=str(data.get("purpose", "")).strip(),
            inputs=list(data.get("inputs") or []),
            outputs=list(data.get("outputs") or []),
            constraints=list(data.get("constraints") or []),
            dependencies=list(data.get("dependencies") or []),
            examples=list(data.get("examples") or []),
            workflows=list(data.get("workflows") or []),
            archetype=str(data.get("archetype", "default")),
        )

    @classmethod
    def from_skill_path(cls, skill_path: Path) -> "SkillSpec":
        """Load spec.yaml from a skill directory."""
        spec_file = skill_path / "spec.yaml"
        if not spec_file.exists():
            raise FileNotFoundError(f"spec.yaml not found in {skill_path}")
        return cls.from_yaml(spec_file)

    @classmethod
    def blank(cls, name: str = "") -> "SkillSpec":
        """Return a blank SkillSpec template."""
        return cls(
            name=name,
            purpose="",
            inputs=[],
            outputs=[],
            constraints=[],
            dependencies=[],
            examples=[],
            workflows=[],
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_validate(skill_path: Path) -> int:
    """Validate spec.yaml completeness and print a report."""
    spec_file = skill_path / "spec.yaml"
    if not spec_file.exists():
        print(f"No spec.yaml found in {skill_path}.")
        print("Run: python -m scripts.spec init <skill-path>  to create one.")
        return 1

    try:
        spec = SkillSpec.from_yaml(spec_file)
    except (ValueError, Exception) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    missing = spec.missing_fields()
    cov = spec.coverage()

    print(f"Skill: {spec.name or '(unnamed)'}")
    print(f"Coverage: {cov}%")
    if missing:
        print(f"Missing fields: {', '.join(missing)}")
        return 1
    else:
        print("All required fields populated.")
        return 0


def _cmd_init(skill_path: Path) -> int:
    """Write a blank spec.yaml into the skill directory."""
    spec_file = skill_path / "spec.yaml"
    if spec_file.exists():
        print(f"spec.yaml already exists in {skill_path}. Delete it first to reinitialise.")
        return 1
    if not skill_path.exists():
        print(f"Directory not found: {skill_path}", file=sys.stderr)
        return 1
    name = skill_path.name
    blank = SkillSpec.blank(name=name)
    blank.write(skill_path)
    print(f"Created {spec_file}")
    print("Fill in the fields, then run: python -m scripts.spec validate <skill-path>")
    return 0


def _main() -> int:
    if len(sys.argv) < 3:
        print("Usage:", file=sys.stderr)
        print("  python -m scripts.spec validate <skill-path>", file=sys.stderr)
        print("  python -m scripts.spec init <skill-path>", file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    skill_path = Path(sys.argv[2])

    if cmd == "validate":
        return _cmd_validate(skill_path)
    elif cmd == "init":
        return _cmd_init(skill_path)
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(_main())
