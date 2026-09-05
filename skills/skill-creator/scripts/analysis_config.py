"""Centralized configuration for lint and static analysis checks.

This module consolidates shared configuration (exemption lists, section patterns)
so they can be maintained in one place and synchronized across all analysis scripts.
"""

from __future__ import annotations

# Files that ship under a resource dir but are imported by other scripts rather
# than invoked or read directly, so SKILL.md has no reason to name them.
EXEMPT_LIBRARY_MODULES = {"__init__.py", "__main__.py", "utils.py", "skill_ir.py"}

# Resource directories to scan for orphaned files
SCAN_DIRS = ("scripts", "agents", "references", "generators")

# Directories to skip during orphan file scanning (vendored, generated, etc)
SKIP_DIRS = {"__pycache__", ".pytest_cache", "node_modules", "generated"}

# Section name patterns used in SKILL.md (case-insensitive)
REFERENCE_SECTION_PATTERNS = [
    "reference files",
    "reference file",
]

# Analysis finding severity levels
SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"
SEVERITY_INFO = "info"

# Maximum findings per rule before collapsing into summary
MAX_FINDINGS_PER_RULE = 5
