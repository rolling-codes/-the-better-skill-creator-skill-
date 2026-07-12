#!/usr/bin/env python3
"""
Quick validation script for skills - minimal version
"""

import sys
import os
import re
import yaml
from pathlib import Path

def validate_skill(skill_path):
    """Basic validation of a skill"""
    skill_path = Path(skill_path)

    # Check SKILL.md exists
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, "SKILL.md not found"

    # Read and validate frontmatter
    content = skill_md.read_text()
    if not content.startswith('---'):
        return False, "No YAML frontmatter found"

    # Extract frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    frontmatter_text = match.group(1)

    # Parse YAML frontmatter
    try:
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    # Define allowed properties
    ALLOWED_PROPERTIES = {'name', 'description', 'license', 'allowed-tools', 'metadata', 'compatibility', 'schemaVersion'}

    # Check for unexpected properties (excluding nested keys under metadata)
    unexpected_keys = set(frontmatter.keys()) - ALLOWED_PROPERTIES
    if unexpected_keys:
        return False, (
            f"Unexpected key(s) in SKILL.md frontmatter: {', '.join(sorted(unexpected_keys))}. "
            f"Allowed properties are: {', '.join(sorted(ALLOWED_PROPERTIES))}"
        )

    # Check required fields
    if 'name' not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if 'description' not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    # Extract name for validation
    name = frontmatter.get('name', '')
    if not isinstance(name, str):
        return False, f"Name must be a string, got {type(name).__name__}"
    name = name.strip()
    if name:
        # Check naming convention (kebab-case: lowercase with hyphens)
        if not re.match(r'^[a-z0-9-]+$', name):
            return False, f"Name '{name}' should be kebab-case (lowercase letters, digits, and hyphens only)"
        if name.startswith('-') or name.endswith('-') or '--' in name:
            return False, f"Name '{name}' cannot start/end with hyphen or contain consecutive hyphens"
        # Check name length (max 64 characters per spec)
        if len(name) > 64:
            return False, f"Name is too long ({len(name)} characters). Maximum is 64 characters."

    # Extract and validate description
    description = frontmatter.get('description', '')
    if not isinstance(description, str):
        return False, f"Description must be a string, got {type(description).__name__}"
    description = description.strip()
    if description:
        # Check for angle brackets
        if '<' in description or '>' in description:
            return False, "Description cannot contain angle brackets (< or >)"
        # Check description length (max 1024 characters per spec)
        if len(description) > 1024:
            return False, f"Description is too long ({len(description)} characters). Maximum is 1024 characters."

    # Validate compatibility field if present (optional)
    compatibility = frontmatter.get('compatibility', '')
    if compatibility:
        if not isinstance(compatibility, str):
            return False, f"Compatibility must be a string, got {type(compatibility).__name__}"
        if len(compatibility) > 500:
            return False, f"Compatibility is too long ({len(compatibility)} characters). Maximum is 500 characters."

    # Validate allowed-tools field if present (optional)
    allowed_tools = frontmatter.get('allowed-tools')
    if allowed_tools is not None:
        if not isinstance(allowed_tools, list) or not all(isinstance(t, str) for t in allowed_tools):
            return False, "allowed-tools must be a list of strings"

    # --- Structural files (optional per-skill, but must be internally consistent if present) ---

    skill_yaml = skill_path / 'skill.yaml'
    lifecycle_md = skill_path / 'LIFECYCLE.md'
    permissions_md = skill_path / 'PERMISSIONS.md'
    tests_dir = skill_path / 'tests'

    skill_yaml_data = None
    if skill_yaml.exists():
        try:
            skill_yaml_data = yaml.safe_load(skill_yaml.read_text())
        except yaml.YAMLError as e:
            return False, f"Invalid YAML in skill.yaml: {e}"
        if not isinstance(skill_yaml_data, dict):
            return False, "skill.yaml must be a YAML dictionary"
        if skill_yaml_data.get('name') != name:
            return False, (
                f"skill.yaml name '{skill_yaml_data.get('name')}' does not match "
                f"SKILL.md frontmatter name '{name}'"
            )

    LIFECYCLE_STATES = {'active', 'experimental', 'deprecated', 'archived'}

    if skill_yaml_data and skill_yaml_data.get('lifecycle') is not None:
        yaml_lifecycle = skill_yaml_data.get('lifecycle')
        if yaml_lifecycle not in LIFECYCLE_STATES:
            return False, (
                f"skill.yaml lifecycle '{yaml_lifecycle}' is not one of "
                f"{sorted(LIFECYCLE_STATES)}"
            )

    # skill.yaml and LIFECYCLE.md both declare a lifecycle/status — catch drift
    # between them rather than silently trusting whichever file was read first.
    if skill_yaml_data and lifecycle_md.exists():
        yaml_lifecycle = skill_yaml_data.get('lifecycle')
        lifecycle_text = lifecycle_md.read_text()
        status_match = re.search(r'^status:\s*(\S+)', lifecycle_text, re.MULTILINE)
        md_status = status_match.group(1) if status_match else None
        if md_status and md_status not in LIFECYCLE_STATES:
            return False, (
                f"LIFECYCLE.md status '{md_status}' is not one of {sorted(LIFECYCLE_STATES)}"
            )
        if yaml_lifecycle and md_status and yaml_lifecycle != md_status:
            return False, (
                f"Lifecycle mismatch: skill.yaml says '{yaml_lifecycle}', "
                f"LIFECYCLE.md says '{md_status}'"
            )

    # skill.yaml's dependencies list is hand-maintained — verify every declared
    # path actually exists so a removed/renamed file is caught instead of
    # silently going stale in both skill.yaml and dependency-graph.md.
    if skill_yaml_data and skill_yaml_data.get('dependencies'):
        deps = skill_yaml_data['dependencies']
        if not isinstance(deps, list):
            return False, "skill.yaml dependencies must be a list"
        missing = [d for d in deps if not (skill_path / d).exists()]
        if missing:
            return False, f"skill.yaml declares missing dependencies: {missing}"

    # If PERMISSIONS.md exists, SKILL.md should declare allowed-tools too —
    # otherwise the detailed breakdown has no summary anchor and can't be
    # cross-checked against what the skill actually declares it needs.
    if permissions_md.exists() and allowed_tools is None:
        return False, (
            "PERMISSIONS.md exists but SKILL.md frontmatter has no 'allowed-tools' "
            "summary field — add one so the two stay checkable against each other"
        )

    # tests/ directory, if present, should contain at least one recognized file
    if tests_dir.exists():
        known_test_files = {'should_trigger.yaml', 'should_not_trigger.yaml', 'expected_behavior.yaml'}
        present = {f.name for f in tests_dir.iterdir() if f.is_file()}
        if not present & known_test_files:
            return False, (
                f"tests/ directory exists but contains none of {sorted(known_test_files)}"
            )
        for fname in present & known_test_files:
            try:
                data = yaml.safe_load((tests_dir / fname).read_text())
            except yaml.YAMLError as e:
                return False, f"Invalid YAML in tests/{fname}: {e}"
            if not isinstance(data, list) or len(data) == 0:
                return False, f"tests/{fname} must be a non-empty YAML list"

    return True, "Skill is valid!"

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        sys.exit(1)
    
    valid, message = validate_skill(sys.argv[1])
    print(message)
    sys.exit(0 if valid else 1)