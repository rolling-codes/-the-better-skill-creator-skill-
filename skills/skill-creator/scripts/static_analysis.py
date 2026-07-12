#!/usr/bin/env python3
"""
Static analysis — semantic/wiring checks that go beyond structural validation.

These checks catch errors that survive quick_validate but surface at runtime:
dead references, unused tools, unreachable sections, etc.

Usage: python -m scripts.static_analysis <skill-path>
Exit codes: 0 = no errors, 1 = errors found, 2 = warnings only.
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from scripts.skill_ir import Skill


@dataclass
class Finding:
    severity: Literal["error", "warning", "info"]
    rule: str        # machine-readable rule id, e.g. "dead-reference"
    message: str
    line: Optional[int] = None

    def __str__(self) -> str:
        loc = f":{self.line}" if self.line else ""
        return f"[{self.severity.upper()}] {self.rule}{loc}: {self.message}"


def analyze(skill: Skill) -> list[Finding]:
    """Run all static-analysis rules on a loaded Skill. Returns findings list."""
    findings: list[Finding] = []
    findings.extend(_check_dead_references(skill))
    findings.extend(_check_missing_assets(skill))
    findings.extend(_check_unused_tools(skill))
    findings.extend(_check_unreachable_sections(skill))
    findings.extend(_check_recursive_call(skill))
    return findings


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def _check_dead_references(skill: Skill) -> list[Finding]:
    """error: file listed in Reference files section but absent on disk."""
    findings: list[Finding] = []
    # Match only backtick-quoted tokens that contain a slash (path separator)
    ref_pattern = re.compile(r"`([^`]+/[^`]+\.[a-zA-Z]{1,6})`")

    in_ref_section = False
    lines = skill.body.split("\n")
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if re.match(r"^#{1,3}\s+reference files?", stripped, re.IGNORECASE):
            in_ref_section = True
            continue
        if in_ref_section and re.match(r"^#{1,3}\s+", stripped):
            in_ref_section = False
        if not in_ref_section:
            continue
        for m in ref_pattern.finditer(line):
            ref = m.group(1).strip()
            if not ref:
                continue
            target = skill.skill_path / ref
            if not target.exists():
                findings.append(Finding(
                    severity="error",
                    rule="dead-reference",
                    message=f"'{ref}' listed in Reference files section but not found on disk",
                    line=lineno,
                ))
    return findings


def _check_missing_assets(skill: Skill) -> list[Finding]:
    """warning: asset path referenced in SKILL.md body but not present on disk."""
    findings: list[Finding] = []
    asset_ref = re.compile(r"assets/[\w./\-]+")
    for lineno, line in enumerate(skill.body.split("\n"), start=1):
        for m in asset_ref.finditer(line):
            asset_path = skill.skill_path / m.group(0)
            if not asset_path.exists():
                findings.append(Finding(
                    severity="warning",
                    rule="missing-asset",
                    message=f"Asset '{m.group(0)}' referenced but not found on disk",
                    line=lineno,
                ))
    return findings


def _check_unused_tools(skill: Skill) -> list[Finding]:
    """info: allowed-tools entry not mentioned anywhere in SKILL.md body."""
    findings: list[Finding] = []
    body_lower = skill.body.lower()
    for tool in skill.allowed_tools:
        # Check for the tool name (or its last segment after dot/slash)
        tool_bare = tool.split(".")[-1].split("/")[-1].lower()
        if tool_bare not in body_lower and tool.lower() not in body_lower:
            findings.append(Finding(
                severity="info",
                rule="unused-tool",
                message=f"Tool '{tool}' is in allowed-tools but never mentioned in SKILL.md body",
            ))
    return findings


def _check_unreachable_sections(skill: Skill) -> list[Finding]:
    """info: ## Section header never linked from any other location in body."""
    findings: list[Finding] = []
    lines = skill.body.split("\n")
    sections: list[tuple[int, str]] = []
    for lineno, line in enumerate(lines, start=1):
        m = re.match(r"^(#{2,3})\s+(.+)", line)
        if m:
            sections.append((lineno, m.group(2).strip()))

    body = skill.body.lower()
    for lineno, heading in sections:
        # Build likely anchor forms
        anchor = re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")
        if anchor not in body.replace(heading.lower(), "", 1) and f"#{anchor}" not in body:
            # Only flag if there are enough sections for reachability to matter
            if len(sections) >= 4:
                findings.append(Finding(
                    severity="info",
                    rule="unreachable-section",
                    message=f"Section '{heading}' is never linked from any other section",
                    line=lineno,
                ))
    return findings


def _check_recursive_call(skill: Skill) -> list[Finding]:
    """warning: skill body mentions own skill name as a skill to invoke."""
    findings: list[Finding] = []
    name = skill.name.lower()
    if not name:
        return findings
    invoke_pattern = re.compile(
        rf"(?:invoke|call|use|run|load|skill)\s+[`'\"]?{re.escape(name)}[`'\"]?",
        re.IGNORECASE,
    )
    for lineno, line in enumerate(skill.body.split("\n"), start=1):
        if invoke_pattern.search(line):
            findings.append(Finding(
                severity="warning",
                rule="recursive-call",
                message=f"Skill body appears to invoke itself ('{name}') — likely unintentional recursion",
                line=lineno,
            ))
    return findings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: python -m scripts.static_analysis <skill-path>", file=sys.stderr)
        return 1
    skill_path = Path(sys.argv[1])
    try:
        skill = Skill.from_path(skill_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    findings = analyze(skill)
    if not findings:
        print("No issues found.")
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
