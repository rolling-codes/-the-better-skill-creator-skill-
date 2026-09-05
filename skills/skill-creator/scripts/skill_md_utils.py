"""Utilities for parsing and validating SKILL.md structure.

Consolidates section detection, reference parsing, and skill validation
to prevent fragile regex duplication across lint and static_analysis.
"""

from __future__ import annotations

import re
from pathlib import Path


def find_section_header(body: str, section_name: str) -> tuple[int, str] | None:
    """Find a section header by name (case-insensitive).
    
    Returns (line_number, full_heading_text) or None if not found.
    Searches for headings (## or ###) that contain the section name.
    """
    pattern = re.compile(
        rf"^#{{{1,3}}}\s+.*\b{re.escape(section_name)}\b",
        re.IGNORECASE | re.MULTILINE,
    )
    match = pattern.search(body)
    if not match:
        return None
    
    line_num = body[:match.start()].count('\n') + 1
    heading_text = match.group(0).strip()
    return (line_num, heading_text)


def has_reference_section(body: str) -> bool:
    """Check if SKILL.md has a Reference files section."""
    pattern = re.compile(
        r"^#{1,3}\s+reference\s+files?",
        re.IGNORECASE | re.MULTILINE,
    )
    return bool(pattern.search(body))


def get_reference_section_content(body: str) -> str | None:
    """Extract the content of the Reference files section.
    
    Returns the section content between the heading and the next heading,
    or None if no Reference files section exists.
    """
    pattern = re.compile(
        r"^#{1,3}\s+reference\s+files?$(.*?)(?=^#{1,3}\s+|\Z)",
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if not match:
        return None
    return match.group(1).strip()


def extract_referenced_files(body: str) -> set[str]:
    """Extract all file paths referenced in backticks in SKILL.md.
    
    Returns a set of normalized file paths that appear in backtick references.
    """
    # Match backtick-quoted tokens containing a path separator
    ref_pattern = re.compile(r"`([^`]*[/\\][^`]*\.[a-zA-Z]{1,6})`")
    return {m.group(1).strip() for m in ref_pattern.finditer(body) if m.group(1).strip()}


def extract_referenced_dirs(body: str) -> set[str]:
    """Extract all directory references (ending in /) from SKILL.md.
    
    Returns a set of normalized directory paths.
    """
    # Match backtick-quoted tokens ending in a slash
    ref_pattern = re.compile(r"`([\w./\-]+/)`")
    return {m.rstrip("/") for m in re.findall(ref_pattern, body)}


def normalize_reference(ref: str) -> str:
    """Normalize a file or directory reference for comparison.
    
    Strips whitespace and converts backslashes to forward slashes.
    """
    return ref.strip().replace("\\", "/")


def reference_forms(rel: str) -> set[str]:
    """Generate all valid reference forms for a file path.
    
    For a file like 'scripts/confidence.py', returns:
    - scripts/confidence.py (full path)
    - confidence.py (bare filename)
    - scripts.confidence (Python module form, if .py file)
    """
    forms = {rel, rel.rsplit("/", 1)[-1]}
    if rel.endswith(".py"):
        forms.add(rel[:-3].replace("/", "."))
    return forms


def is_reference_in_body(rel: str, body: str, referenced_dirs: set[str]) -> bool:
    """Check if a file reference appears in SKILL.md body.
    
    Returns True if the file is referenced directly or via a parent directory.
    """
    # Check direct reference in any form
    if any(form in body for form in reference_forms(rel)):
        return True
    
    # Check if covered by a nested directory reference
    parts = rel.split("/")
    ancestors = {"/".join(parts[:i]) for i in range(1, len(parts))}
    nested_dirs = {d for d in referenced_dirs if "/" in d}
    return bool(ancestors & nested_dirs)


def validate_skill_structure(skill_path: Path) -> list[str]:
    """Validate basic SKILL.md structure (frontmatter, required fields).
    
    Returns a list of validation errors, empty if valid.
    """
    errors = []
    skill_md = skill_path / "SKILL.md"
    
    if not skill_md.exists():
        return ["SKILL.md not found"]
    
    content = skill_md.read_text(encoding="utf-8")
    
    # Check frontmatter
    if not content.startswith("---"):
        errors.append("Missing YAML frontmatter (should start with ---)")
    
    # Extract frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not fm_match:
        errors.append("Invalid YAML frontmatter format")
        return errors
    
    frontmatter = fm_match.group(1)
    
    # Check required fields
    if "name:" not in frontmatter:
        errors.append("Missing 'name' in frontmatter")
    if "description:" not in frontmatter:
        errors.append("Missing 'description' in frontmatter")
    if "schemaVersion:" not in frontmatter:
        errors.append("Missing 'schemaVersion' in frontmatter")
    
    return errors
