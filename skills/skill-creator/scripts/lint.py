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
from typing import NamedTuple, List

from scripts.skill_ir import Skill
from scripts.static_analysis import Finding, _cap
from scripts.analysis_config import EXEMPT_LIBRARY_MODULES
from scripts.skill_md_utils import (
    has_reference_section,
    extract_referenced_dirs,
    is_reference_in_body,
)


def lint(skill: Skill) -> List[Finding]:
    """Run all lint rules on a loaded Skill. Returns findings list.
    
    Args:
        skill: The Skill instance to lint.
        
    Returns:
        A list of Finding objects (errors, warnings, info).
    """
    findings: List[Finding] = []
    findings.extend(_check_description_length(skill))
    findings.extend(_check_description_trigger(skill))
    findings.extend(_check_description_boundary(skill))
    findings.extend(_check_token_budget(skill))
    findings.extend(_check_missing_examples(skill))
    findings.extend(_check_missing_reference_section(skill))
    findings.extend(_check_reference_wiring_completeness(skill))
    findings.extend(_check_frontmatter_missing_tools(skill))
    findings.extend(_check_workflow_no_output(skill))
    findings.extend(_check_empty_body(skill))
    return findings


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def _check_empty_body(skill: Skill) -> List[Finding]:
    """error: SKILL.md has no body content after frontmatter."""
    if not skill.body.strip():
        return [Finding(
            severity="error",
            rule="empty-body",
            message="SKILL.md has no content after frontmatter. Add instructions for Claude.",
        )]
    return []


def _check_description_length(skill: Skill) -> List[Finding]:
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


def _check_description_trigger(skill: Skill) -> List[Finding]:
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


def _check_description_boundary(skill: Skill) -> List[Finding]:
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


def _check_token_budget(skill: Skill) -> List[Finding]:
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


def _check_missing_examples(skill: Skill) -> List[Finding]:
    """info: section with 'format' or 'structure' in heading but no code fence."""
    findings: List[Finding] = []
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


def _check_missing_reference_section(skill: Skill) -> List[Finding]:
    """error: agents/ or references/ files exist but no 'Reference files' section in body."""
    has_agents = any((skill.skill_path / "agents").iterdir()) if (skill.skill_path / "agents").exists() else False
    has_refs = any((skill.skill_path / "references").iterdir()) if (skill.skill_path / "references").exists() else False
    if not (has_agents or has_refs):
        return []
    
    # Use centralized utility for more robust section detection
    if not has_reference_section(skill.body):
        return [Finding(
            severity="error",
            rule="missing-reference-section",
            message=(
                "agents/ or references/ directories exist but SKILL.md has no "
                "'Reference files' section. Claude cannot use files it doesn't know about."
            ),
        )]
    return []


def _check_reference_wiring_completeness(skill: Skill) -> List[Finding]:
    """warning: a skill.yaml dependency is never referenced in SKILL.md.

    The fork's whole reason to exist is that a file Claude never sees might as
    well not ship. quick_validate confirms a Reference files section exists;
    this confirms it is actually complete — every declared dependency is linked
    from the body, either directly or via a referenced parent directory. Library
    modules imported by other scripts (not invoked directly) are exempt.
    """
    deps = skill.dependencies
    if not deps:
        return []
    
    body = skill.body
    referenced_dirs = extract_referenced_dirs(body)
    findings: list[Finding] = []

    for raw in deps:
        raw = raw.strip()
        if not raw:
            continue
        norm = raw.rstrip("/")
        if norm.rsplit("/", 1)[-1] in EXEMPT_LIBRARY_MODULES:
            continue
        
        # A dir dependency is covered when the dir itself is referenced; a file
        # dependency when any of its reference forms or a parent dir appears.
        if norm in referenced_dirs or is_reference_in_body(norm, body, referenced_dirs):
            continue
        
        findings.append(Finding(
            severity="warning",
            rule="unwired-dependency",
            message=(
                f"'{raw}' is declared in skill.yaml but never referenced in SKILL.md. "
                "Under progressive disclosure Claude never sees it — link it from the "
                "Reference files section or drop it from dependencies."
            ),
        ))
    return _cap(findings, "unwired-dependency")


def _check_frontmatter_missing_tools(skill: Skill) -> List[Finding]:
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


def _check_workflow_no_output(skill: Skill) -> List[Finding]:
    """info: an imperative workflow step that names no output artifact.

    Scoped deliberately. Markdown numbered lists are used for plenty of things
    that are not workflow steps: interview questions, enumerations of concepts,
    ordered explanations. Flagging all of them buries the cases that matter, so
    this rule only looks inside sections whose heading says it is a process,
    and only at lines that read as an instruction to do something.
    """
    findings: List[Finding] = []
    output_keywords = [
        "output", "write", "create", "generate", "produce", "return",
        "result", "save", "emit", "yield", "deliver", "file", "report",
        "json", "artifact",
    ]
    workflow_heading = re.compile(
        r"^#{2,4}\s+.*\b(workflow|process|steps?|pipeline|loop|procedure|"
        r"how to|running|iteration)\b",
        re.IGNORECASE,
    )
    heading_pattern = re.compile(r"^#{1,6}\s+")
    step_pattern = re.compile(r"^\s*\d+\.\s+(.+)")
    # An instruction starts with a bare imperative verb.
    imperative = re.compile(
        r"^(run|read|write|create|open|launch|spawn|apply|update|check|"
        r"grade|aggregate|save|kill|rerun|wait|package|install|copy|move|"
        r"draft|review|replace|export|generate|analyze|analyse|tell|add|"
        r"remove|set|point|start|stop|fix|edit)\b",
        re.IGNORECASE,
    )

    in_workflow = False
    for lineno, line in enumerate(skill.body.split("\n"), start=1):
        if heading_pattern.match(line):
            in_workflow = bool(workflow_heading.match(line))
            continue
        if not in_workflow:
            continue
        m = step_pattern.match(line)
        if not m:
            continue
        step_text = m.group(1).strip()
        # Questions are prompts to the user, not steps that produce artifacts.
        if step_text.endswith("?"):
            continue
        if not imperative.match(step_text):
            continue
        if any(kw in step_text.lower() for kw in output_keywords):
            continue
        display = step_text if len(step_text) <= 60 else step_text[:60] + "..."
        findings.append(Finding(
            severity="info",
            rule="workflow-no-output",
            message=f"Workflow step has no output artifact: '{display}'",
            line=lineno,
        ))
    return _cap(findings, "workflow-no-output")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    """Main entry point for the linter."""
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
    return 1 if errors else (2 if warnings else 0)


if __name__ == "__main__":
    sys.exit(_main())
