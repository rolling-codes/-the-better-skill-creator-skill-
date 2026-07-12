#!/usr/bin/env python3
"""
Skill linter — content-quality checks complementing quick_validate.py's
structural checks and static_analysis.py's wiring checks.

Run standalone or as a pre-commit hook step.

Usage: python -m scripts.lint <skill-path>
Exit codes: 0 = no issues, 1 = errors found, 2 = warnings only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from scripts.skill_ir import Skill
from scripts.static_analysis import Finding


def lint(skill: Skill) -> list[Finding]:
    """Run all lint rules on a loaded Skill. Returns findings list."""
    findings: list[Finding] = []
    findings.extend(_check_description_length(skill))
    findings.extend(_check_description_trigger(skill))
    findings.extend(_check_description_boundary(skill))
    findings.extend(_check_token_budget(skill))
    findings.extend(_check_missing_examples(skill))
    findings.extend(_check_missing_reference_section(skill))
    findings.extend(_check_frontmatter_missing_tools(skill))
    findings.extend(_check_workflow_no_output(skill))
    return findings


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def _check_description_length(skill: Skill) -> list[Finding]:
    """warning: description under 50 or over 400 chars."""
    n = len(skill.description)
    if n < 50:
        return [Finding(
            severity="warning",
            rule="description-length",
            message=f"Description is only {n} chars (min 50). Short descriptions cause triggering gaps.",
        )]
    if n > 400:
        return [Finding(
            severity="warning",
            rule="description-length",
            message=f"Description is {n} chars (max 400). Overly long descriptions dilute the trigger signal.",
        )]
    return []


def _check_description_trigger(skill: Skill) -> list[Finding]:
    """warning: description missing an explicit trigger clause."""
    trigger_phrases = [
        "use when", "when the user", "trigger", "fires when",
        "activate", "invoked when", "called when",
    ]
    desc_lower = skill.description.lower()
    if not any(p in desc_lower for p in trigger_phrases):
        return [Finding(
            severity="warning",
            rule="description-no-trigger",
            message=(
                "Description has no trigger clause ('Use when...', 'when the user...', etc.). "
                "Without an explicit trigger, the skill may never fire or fire inconsistently."
            ),
        )]
    return []


def _check_description_boundary(skill: Skill) -> list[Finding]:
    """warning: description missing an explicit boundary/exclusion clause."""
    boundary_phrases = ["not for", "does not", "not when", "NOT", "exclud", "except"]
    desc_lower = skill.description.lower()
    if not any(p.lower() in desc_lower for p in boundary_phrases):
        return [Finding(
            severity="warning",
            rule="description-no-boundary",
            message=(
                "Description has no boundary clause ('NOT for...', 'does not...', etc.). "
                "Without a boundary, the skill may collide with adjacent skills."
            ),
        )]
    return []


def _check_token_budget(skill: Skill) -> list[Finding]:
    """warning: SKILL.md body over 500 lines."""
    line_count = len(skill.body.split("\n"))
    if line_count > 500:
        return [Finding(
            severity="warning",
            rule="token-budget",
            message=(
                f"SKILL.md body is {line_count} lines (recommended max 500). "
                "Consider extracting environment docs or reference details to references/."
            ),
        )]
    return []


def _check_missing_examples(skill: Skill) -> list[Finding]:
    """info: section with 'format' or 'structure' in heading but no code fence."""
    findings: list[Finding] = []
    lines = skill.body.split("\n")
    in_format_section = False
    has_code_fence = False
    section_lineno = 0
    section_heading = ""

    for lineno, line in enumerate(lines, start=1):
        heading_match = re.match(r"^#{1,3}\s+(.+)", line)
        if heading_match:
            # Close previous section check
            if in_format_section and not has_code_fence:
                findings.append(Finding(
                    severity="info",
                    rule="missing-example",
                    message=(
                        f"Section '{section_heading}' mentions format/structure "
                        "but contains no code fence example."
                    ),
                    line=section_lineno,
                ))
            heading = heading_match.group(1).lower()
            if any(kw in heading for kw in ("format", "structure", "schema", "output")):
                in_format_section = True
                has_code_fence = False
                section_lineno = lineno
                section_heading = heading_match.group(1)
            else:
                in_format_section = False

        if in_format_section and line.strip().startswith("```"):
            has_code_fence = True

    if in_format_section and not has_code_fence:
        findings.append(Finding(
            severity="info",
            rule="missing-example",
            message=(
                f"Section '{section_heading}' mentions format/structure "
                "but contains no code fence example."
            ),
            line=section_lineno,
        ))
    return findings


def _check_missing_reference_section(skill: Skill) -> list[Finding]:
    """error: agents/ or references/ files exist but no 'Reference files' section in body."""
    has_agents = any((skill.skill_path / "agents").iterdir()) if (skill.skill_path / "agents").exists() else False
    has_refs = any((skill.skill_path / "references").iterdir()) if (skill.skill_path / "references").exists() else False
    if not (has_agents or has_refs):
        return []
    ref_section = re.search(r"^#{1,3}\s+reference files?", skill.body, re.IGNORECASE | re.MULTILINE)
    if not ref_section:
        return [Finding(
            severity="error",
            rule="missing-reference-section",
            message=(
                "agents/ or references/ directories exist but SKILL.md has no "
                "'Reference files' section. Claude cannot use files it doesn't know about."
            ),
        )]
    return []


def _check_frontmatter_missing_tools(skill: Skill) -> list[Finding]:
    """warning: PERMISSIONS.md or tool references exist but allowed-tools is empty."""
    permissions_exists = (skill.skill_path / "PERMISSIONS.md").exists()
    if permissions_exists and not skill.allowed_tools:
        return [Finding(
            severity="warning",
            rule="frontmatter-missing-tools",
            message=(
                "PERMISSIONS.md exists but allowed-tools is absent in frontmatter. "
                "Claude Code will not know which tools this skill needs."
            ),
        )]
    return []


def _check_workflow_no_output(skill: Skill) -> list[Finding]:
    """info: numbered workflow step mentions no output artifact."""
    findings: list[Finding] = []
    output_keywords = [
        "output", "write", "create", "generate", "produce", "return",
        "result", "save", "emit", "yield", "deliver",
    ]
    step_pattern = re.compile(r"^\s*\d+\.\s+(.+)")
    for lineno, line in enumerate(skill.body.split("\n"), start=1):
        m = step_pattern.match(line)
        if not m:
            continue
        step_text = m.group(1).lower()
        if not any(kw in step_text for kw in output_keywords):
            findings.append(Finding(
                severity="info",
                rule="workflow-no-output",
                message=(
                    f"Workflow step has no output artifact: '{m.group(1)[:60]}...'"
                    if len(m.group(1)) > 60 else
                    f"Workflow step has no output artifact: '{m.group(1)}'"
                ),
                line=lineno,
            ))
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.lint <skill-path>", file=sys.stderr)
        return 1
    skill_path = Path(sys.argv[1])
    try:
        skill = Skill.from_path(skill_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    findings = lint(skill)
    if not findings:
        print("No lint issues found.")
        return 0

    errors = [f for f in findings if f.severity == "error"]
    warnings = [f for f in findings if f.severity == "warning"]
    infos = [f for f in findings if f.severity == "info"]

    for f in findings:
        print(str(f))

    print(
        f"\n{len(findings)} finding(s): "
        f"{len(errors)} error(s), {len(warnings)} warning(s), {len(infos)} info(s)"
    )
    return 1 if errors else 2


if __name__ == "__main__":
    sys.exit(_main())
