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
    findings.extend(_check_orphaned_files(skill))
    findings.extend(_check_missing_assets(skill))
    findings.extend(_check_unused_tools(skill))
    findings.extend(_check_unreachable_sections(skill))
    findings.extend(_check_recursive_call(skill))
    return findings


# Files that ship under a resource dir but are imported by other scripts rather
# than invoked or read directly, so SKILL.md has no reason to name them.
_ORPHAN_EXEMPT_NAMES = {"__init__.py", "__main__.py", "utils.py", "skill_ir.py"}
_ORPHAN_SCAN_DIRS = ("scripts", "agents", "references", "generators")
_ORPHAN_SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", "generated"}


def _referenced_dirs(body: str) -> set[str]:
    """Directory tokens referenced as a whole in the body, e.g. `scripts/stages/`.

    A reference to a directory covers every file beneath it, mirroring how
    skill.yaml lets `scripts/stages/` stand in for its contents. Only
    backtick-quoted tokens ending in a slash count, so the bare substring
    'scripts/' inside `scripts/run_eval.py` is not mistaken for a directory
    reference — that mistake would make every file under scripts/ look covered.
    """
    return {m.rstrip("/") for m in re.findall(r"`([\w./\-]+/)`", body)}


def _reference_forms(rel: str) -> set[str]:
    """The strings that legitimately reference a file in SKILL.md prose.

    SKILL.md names scripts three ways: by path (`scripts/confidence.py`), by
    bare filename (`quick_validate.py`), and — for Python — by dotted module in
    `python -m scripts.confidence`. All three mean the file is reachable, so a
    reference in any form counts. Matching more forms errs toward silence, which
    is the right bias: a false 'orphaned' alarm trains people to ignore the rule.
    """
    forms = {rel, rel.rsplit("/", 1)[-1]}
    if rel.endswith(".py"):
        forms.add(rel[:-3].replace("/", "."))
    return forms


def _is_referenced(rel: str, body: str, referenced_dirs: set[str]) -> bool:
    """True if `rel` is reachable from SKILL.md by any reference form or via a
    referenced parent directory.

    Only *nested* directory references (those containing a slash, e.g.
    `scripts/stages/`) count as covering their children. A bare top-level bucket
    like `scripts/` — which shows up in ordinary prose such as "put it in
    `scripts/`" — is too coarse to prove any specific file is discoverable, and
    honouring it would silently mask every future orphan dropped into that dir.
    """
    if any(form in body for form in _reference_forms(rel)):
        return True
    parts = rel.split("/")
    ancestors = {"/".join(parts[:i]) for i in range(1, len(parts))}
    nested_dirs = {d for d in referenced_dirs if "/" in d}
    return bool(ancestors & nested_dirs)


# ---------------------------------------------------------------------------
# Noise control
# ---------------------------------------------------------------------------

MAX_FINDINGS_PER_RULE = 5


def _cap(findings: list[Finding], rule: str,
         limit: int = MAX_FINDINGS_PER_RULE) -> list[Finding]:
    """Collapse a flood of same-rule findings into the first few plus a count.

    A rule that fires on nearly every line stops being a signal and starts
    being wallpaper, which is the same non-discriminating-assertion problem
    agents/analyzer.md warns about in evals. Showing a handful of concrete
    examples plus a total keeps the detail without burying the other rules.
    """
    if len(findings) <= limit:
        return findings
    hidden = len(findings) - limit
    return findings[:limit] + [Finding(
        severity=findings[0].severity,
        rule=rule,
        message=(
            f"...and {hidden} more '{rule}' finding(s) suppressed. "
            f"A rule firing this often usually means the rule is too broad, "
            f"not that the skill is broken."
        ),
    )]


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


def _check_orphaned_files(skill: Skill) -> list[Finding]:
    """warning: a resource file exists on disk but is never referenced in SKILL.md.

    This is the reverse of the dead-reference check, and the specific failure this
    fork exists to prevent: under progressive disclosure Claude only loads the
    files SKILL.md names, so a script or agent that ships unreferenced is invisible
    at runtime — the model never discovers it. A reference to a parent directory
    (e.g. `scripts/stages/`) covers everything beneath it, and internal library
    modules imported by other scripts rather than invoked directly are exempt.
    """
    findings: list[Finding] = []
    body = skill.body
    referenced_dirs = _referenced_dirs(body)
    for scan_dir in _ORPHAN_SCAN_DIRS:
        base = skill.skill_path / scan_dir
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            parts = path.relative_to(skill.skill_path).parts
            if any(p in _ORPHAN_SKIP_DIRS for p in parts):
                continue
            if path.name in _ORPHAN_EXEMPT_NAMES:
                continue
            rel = "/".join(parts)
            if _is_referenced(rel, body, referenced_dirs):
                continue
            findings.append(Finding(
                severity="warning",
                rule="orphaned-file",
                message=(
                    f"'{rel}' exists on disk but is never referenced in SKILL.md. "
                    "Under progressive disclosure Claude never loads it — wire it into "
                    "the Reference files section or remove it."
                ),
            ))
    return _cap(findings, "orphaned-file")


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
    """info: ## Section header never linked, in a doc that navigates by link.

    A SKILL.md written as a linear procedure is read top to bottom, so an
    unlinked heading is normal and flagging it is pure noise. This rule only
    applies when the document actually uses in-body anchor links to navigate
    (three or more `](#anchor)` links). In that case an unlinked top-level
    section really is unreachable by the model following the links.
    """
    findings: list[Finding] = []
    body = skill.body
    anchor_links = re.findall(r"\]\(#([\w-]+)\)", body)
    if len(anchor_links) < 3:
        # Linear document: reachability by link is not the navigation model.
        return findings

    linked = {a.lower() for a in anchor_links}
    lines = body.split("\n")
    for lineno, line in enumerate(lines, start=1):
        m = re.match(r"^(#{2})\s+(.+)", line)   # top-level sections only
        if not m:
            continue
        heading = m.group(2).strip()
        # Sequential steps are reached by reading order, not by link.
        if re.match(r"^step\s+\d+", heading, re.IGNORECASE):
            continue
        anchor = re.sub(r"[^\w\s-]", "", heading.lower()).strip().replace(" ", "-")
        if anchor not in linked:
            findings.append(Finding(
                severity="info",
                rule="unreachable-section",
                message=f"Section '{heading}' is never linked from any other section",
                line=lineno,
            ))
    return _cap(findings, "unreachable-section")


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
