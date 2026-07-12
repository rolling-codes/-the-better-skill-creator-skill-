#!/usr/bin/env python3
"""
Confidence report — how complete and unambiguous is a skill's intent capture.

Derives entirely from structural analysis of the Skill IR and spec.yaml (if present).
No LLM calls.

Usage: python -m scripts.confidence <skill-path>
Exit codes: 0 = overall ≥80, 1 = overall <80.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from scripts.skill_ir import Skill


@dataclass
class ConfidenceReport:
    """Confidence metrics for a skill's intent capture."""
    requirement_coverage: int       # 0–100: % of expected fields populated
    ambiguity_score: int            # 0–100: 0=very ambiguous, 100=precise
    missing_info: list[str]         # fields or sections absent/thin
    inferred_assumptions: list[str] # things assumed that weren't stated
    overall: int                    # weighted average (60% coverage, 40% clarity)

    def __str__(self) -> str:
        lines = [
            f"Requirement coverage : {self.requirement_coverage}%",
            f"Ambiguity score      : {self.ambiguity_score}%",
            f"Overall confidence   : {self.overall}%",
        ]
        if self.missing_info:
            lines.append("\nMissing information:")
            for item in self.missing_info:
                lines.append(f"  - {item}")
        if self.inferred_assumptions:
            lines.append("\nInferred assumptions:")
            for item in self.inferred_assumptions:
                lines.append(f"  - {item}")
        return "\n".join(lines)


def assess_skill(skill: Skill) -> ConfidenceReport:
    """Assess confidence from an existing skill."""
    missing: list[str] = []
    assumptions: list[str] = []
    coverage_checks: list[bool] = []

    # --- Name ---
    coverage_checks.append(bool(skill.name))
    if not skill.name:
        missing.append("name field is empty")

    # --- Description ---
    desc = skill.description
    coverage_checks.append(bool(desc and len(desc) >= 50))
    if not desc:
        missing.append("description is empty")
    elif len(desc) < 50:
        missing.append(f"description is too short ({len(desc)} chars; min 50)")

    # --- Trigger clause ---
    trigger_phrases = ["use when", "when the user", "trigger", "fires when", "invoked when"]
    has_trigger = any(p in desc.lower() for p in trigger_phrases)
    coverage_checks.append(has_trigger)
    if not has_trigger:
        missing.append("no trigger clause in description ('Use when...' or similar)")
        assumptions.append("assumed the skill triggers on any vaguely related request")

    # --- Boundary clause ---
    boundary_phrases = ["not for", "does not", "not when", "NOT", "exclud", "except"]
    has_boundary = any(p.lower() in desc.lower() for p in boundary_phrases)
    coverage_checks.append(has_boundary)
    if not has_boundary:
        missing.append("no boundary clause in description ('NOT for...' or similar)")
        assumptions.append("assumed no adjacent skills overlap with this one")

    # --- SKILL.md body ---
    body_lines = len(skill.body.split("\n"))
    has_body = body_lines > 5
    coverage_checks.append(has_body)
    if not has_body:
        missing.append("SKILL.md body is empty or very thin")

    # --- Test coverage ---
    tests_dir = skill.skill_path / "tests"
    test_files = list(tests_dir.glob("*.yaml")) if tests_dir.exists() else []
    has_tests = len(test_files) >= 1
    coverage_checks.append(has_tests)
    if not has_tests:
        missing.append("no test files in tests/")
        assumptions.append("assumed triggering behaviour is correct without verification")

    # --- Reference section ---
    has_ref_section = bool(
        re.search(r"^#{1,3}\s+reference files?", skill.body, re.IGNORECASE | re.MULTILINE)
    )
    agents_dir = skill.skill_path / "agents"
    refs_dir = skill.skill_path / "references"
    has_ref_dirs = (
        (agents_dir.exists() and any(agents_dir.iterdir())) or
        (refs_dir.exists() and any(refs_dir.iterdir()))
    )
    if has_ref_dirs:
        coverage_checks.append(has_ref_section)
        if not has_ref_section:
            missing.append("agents/ or references/ exist but no Reference files section")
            assumptions.append("assumed Claude can find reference files without being told")
    else:
        coverage_checks.append(True)  # no ref dirs, not a gap

    # --- allowed-tools ---
    coverage_checks.append(bool(skill.allowed_tools))
    if not skill.allowed_tools:
        assumptions.append("assumed no specific tool permissions are needed")

    # --- Output format ---
    output_keywords = ["output", "format", "returns", "produces", "result"]
    body_lower = skill.body.lower()
    has_output_spec = any(kw in body_lower for kw in output_keywords)
    coverage_checks.append(has_output_spec)
    if not has_output_spec:
        missing.append("no output format or expected result described in body")
        assumptions.append("assumed any output format is acceptable")

    # --- spec.yaml (bonus) ---
    spec_file = skill.skill_path / "spec.yaml"
    has_spec = spec_file.exists()
    coverage_checks.append(has_spec)
    if not has_spec:
        assumptions.append("no spec.yaml; intent was captured directly in SKILL.md")

    # Scores
    requirement_coverage = int(100 * sum(coverage_checks) / max(len(coverage_checks), 1))

    # Ambiguity: fewer missing fields + fewer assumptions = higher clarity
    ambiguity_score = max(
        0,
        100 - (len(missing) * 8) - (len(assumptions) * 5)
    )

    overall = int(0.6 * requirement_coverage + 0.4 * ambiguity_score)

    return ConfidenceReport(
        requirement_coverage=requirement_coverage,
        ambiguity_score=ambiguity_score,
        missing_info=missing,
        inferred_assumptions=assumptions,
        overall=overall,
    )


def assess_spec(spec) -> ConfidenceReport:
    """Assess confidence from a SkillSpec (pre-generation)."""
    # Import here to avoid circular dependency if spec imports confidence
    missing: list[str] = []
    assumptions: list[str] = []
    coverage_checks: list[bool] = []

    fields = [
        ("name", spec.name),
        ("purpose", spec.purpose),
        ("inputs", spec.inputs),
        ("outputs", spec.outputs),
        ("workflows", spec.workflows),
    ]
    optional_fields = [
        ("constraints", spec.constraints),
        ("dependencies", spec.dependencies),
        ("examples", spec.examples),
    ]

    for name, val in fields:
        present = bool(val)
        coverage_checks.append(present)
        if not present:
            missing.append(f"'{name}' is empty in spec.yaml")

    for name, val in optional_fields:
        present = bool(val)
        coverage_checks.append(present)
        if not present:
            assumptions.append(f"no {name} specified — defaults assumed")

    requirement_coverage = int(100 * sum(coverage_checks) / max(len(coverage_checks), 1))
    ambiguity_score = max(0, 100 - (len(missing) * 12) - (len(assumptions) * 4))
    overall = int(0.6 * requirement_coverage + 0.4 * ambiguity_score)

    return ConfidenceReport(
        requirement_coverage=requirement_coverage,
        ambiguity_score=ambiguity_score,
        missing_info=missing,
        inferred_assumptions=assumptions,
        overall=overall,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.confidence <skill-path>", file=sys.stderr)
        return 1
    skill_path = Path(sys.argv[1])
    try:
        skill = Skill.from_path(skill_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = assess_skill(skill)
    print(str(report))
    print()

    if report.overall >= 80:
        print(f"✅ Confidence OK ({report.overall}%)")
        return 0
    else:
        print(f"⚠️  Low confidence ({report.overall}%) — address missing info before sharing.")
        return 1


if __name__ == "__main__":
    sys.exit(_main())
