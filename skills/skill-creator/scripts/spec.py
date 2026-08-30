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

    # --- design analysis (multi-angle scoping; see references/design-analysis.md) ---
    outcome: str = ""                                          # the real end-state, in outcome terms
    interpretations: list[str] = field(default_factory=list)  # valid readings considered; chosen marked
    modes: list[str] = field(default_factory=list)            # modes/categories/use-cases to support
    entailments: list[str] = field(default_factory=list)      # implied tasks/tools/files/workflow steps
    failure_points: list[str] = field(default_factory=list)   # errors/edge-cases/limits to guard or test
    validation: list[str] = field(default_factory=list)       # how the skill checks its own output
    assumptions: list[str] = field(default_factory=list)      # what was inferred and stated
    open_questions: list[str] = field(default_factory=list)   # decisive forks still needing the user

    # ------------------------------------------------------------------
    # Completeness helpers
    # ------------------------------------------------------------------

    def missing_fields(self) -> list[str]:
        """Core fields a spec must have — hard requirement. A spec missing any of
        these is malformed, and this set is unchanged from before the design-analysis
        fields were added, so specs authored on earlier versions still validate."""
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

    def missing_design_fields(self) -> list[str]:
        """Design-analysis fields that keep a spec from being flat (`outcome` and
        `entailments`). Their absence is a scope-quality warning, not a hard error —
        an older spec is still valid, it just hasn't been scoped from multiple angles
        yet (see references/design-analysis.md)."""
        gaps = []
        if not self.outcome:
            gaps.append("outcome")
        if not self.entailments:
            gaps.append("entailments")
        return gaps

    def coverage(self) -> int:
        """Return completeness as 0–100 (% of non-empty fields)."""
        fields = [
            bool(self.name), bool(self.purpose), bool(self.inputs),
            bool(self.outputs), bool(self.constraints), bool(self.dependencies),
            bool(self.examples), bool(self.workflows),
            # design-analysis fields (open_questions excluded — empty is the goal)
            bool(self.outcome), bool(self.interpretations), bool(self.modes),
            bool(self.entailments), bool(self.failure_points),
            bool(self.validation), bool(self.assumptions),
        ]
        return int(100 * sum(fields) / len(fields))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "outcome": self.outcome,
            "archetype": self.archetype,
            "interpretations": self.interpretations,
            "modes": self.modes,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "entailments": self.entailments,
            "constraints": self.constraints,
            "dependencies": self.dependencies,
            "failure_points": self.failure_points,
            "validation": self.validation,
            "examples": self.examples,
            "workflows": self.workflows,
            "assumptions": self.assumptions,
            "open_questions": self.open_questions,
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
            outcome=str(data.get("outcome", "")).strip(),
            interpretations=list(data.get("interpretations") or []),
            modes=list(data.get("modes") or []),
            entailments=list(data.get("entailments") or []),
            failure_points=list(data.get("failure_points") or []),
            validation=list(data.get("validation") or []),
            assumptions=list(data.get("assumptions") or []),
            open_questions=list(data.get("open_questions") or []),
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
    design_gaps = spec.missing_design_fields()
    cov = spec.coverage()

    print(f"Skill: {spec.name or '(unnamed)'}")
    print(f"Coverage: {cov}%")
    if missing:
        print(f"Missing required fields: {', '.join(missing)}")
        return 1
    if design_gaps:
        # Non-fatal: the spec is structurally valid but wasn't scoped from multiple
        # angles. Warn (exit 2) rather than fail, so specs authored before the
        # design-analysis fields existed still pass.
        print(f"WARN: design analysis incomplete — {', '.join(design_gaps)} not set.")
        print("Scope may be flat; see references/design-analysis.md. Fill these in for a full spec.")
        return 2
    print("All required fields populated, design analysis present.")
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
