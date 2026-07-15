#!/usr/bin/env python3
"""
Comprehensive linter for skill-creator's own SKILL.md and related files.
This meta-skill ensures skill-creator dogfoods its own validation rules.
"""

import sys
import re
import yaml
from pathlib import Path


def lint_skill(skill_path):
    """Run comprehensive linting on a skill directory."""
    skill_path = Path(skill_path)
    errors = []
    warnings = []

    # Check basic structure
    skill_md = skill_path / 'SKILL.md'
    if not skill_md.exists():
        return False, ["SKILL.md not found"]

    content = skill_md.read_text()

    # Parse frontmatter
    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return False, ["Invalid YAML frontmatter"]

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        return False, [f"YAML parse error: {e}"]

    # Required fields
    if not frontmatter.get('name'):
        errors.append("Missing 'name' in frontmatter")
    if not frontmatter.get('description'):
        errors.append("Missing 'description' in frontmatter")

    # Name validation
    name = frontmatter.get('name', '')
    if name:
        if not re.match(r'^[a-z0-9-]+$', name):
            errors.append(f"Name '{name}' should be kebab-case")
        if len(name) > 64:
            errors.append(f"Name exceeds 64 characters ({len(name)})")

    # Description validation
    description = frontmatter.get('description', '')
    if description:
        if len(description) > 1024:
            errors.append(f"Description exceeds 1024 characters ({len(description)})")
        if '<' in description or '>' in description:
            errors.append("Description contains angle brackets")
        if len(description.split()) < 5:
            warnings.append("Description seems too short (less than 5 words)")

    # Check allowed-tools field
    allowed_tools = frontmatter.get('allowed-tools')
    if allowed_tools is None:
        warnings.append("No 'allowed-tools' field in frontmatter (optional but recommended)")
    elif not isinstance(allowed_tools, list):
        errors.append("'allowed-tools' must be a list")
    elif not all(isinstance(t, str) for t in allowed_tools):
        errors.append("All items in 'allowed-tools' must be strings")

    # Check skill.yaml
    skill_yaml = skill_path / 'skill.yaml'
    if skill_yaml.exists():
        try:
            yaml_data = yaml.safe_load(skill_yaml.read_text())
            if not isinstance(yaml_data, dict):
                errors.append("skill.yaml must be a dictionary")
            else:
                # Check version format
                version = yaml_data.get('version', '')
                if version:
                    if not re.match(r'^\d+\.\d+\.\d+', version):
                        errors.append(f"Version '{version}' does not follow semver format")

                # Check dependencies exist
                deps = yaml_data.get('dependencies', [])
                for dep in deps:
                    dep_path = skill_path / dep
                    if not dep_path.exists():
                        errors.append(f"Declared dependency missing: {dep}")
                    elif dep_path.is_file():
                        # Check file is readable
                        try:
                            dep_path.read_text(encoding='utf-8', errors='replace')
                        except (IOError, OSError) as e:
                            warnings.append(f"Dependency file not readable: {dep} ({e})")

                # Check lifecycle
                lifecycle = yaml_data.get('lifecycle')
                if lifecycle and lifecycle not in {'active', 'experimental', 'deprecated', 'archived'}:
                    errors.append(f"Invalid lifecycle '{lifecycle}'")

                # Check audit field
                audit = yaml_data.get('audit')
                if audit and isinstance(audit, dict):
                    if audit.get('status') and audit.get('status') not in {'passing', 'warning', 'failing'}:
                        errors.append(f"Invalid audit status '{audit.get('status')}'")

        except yaml.YAMLError as e:
            errors.append(f"skill.yaml parse error: {e}")

    # Check documentation files
    lifecycle_md = skill_path / 'LIFECYCLE.md'
    permissions_md = skill_path / 'PERMISSIONS.md'

    if permissions_md.exists() and not allowed_tools:
        errors.append("PERMISSIONS.md exists but no 'allowed-tools' in SKILL.md")

    if lifecycle_md.exists():
        lifecycle_text = lifecycle_md.read_text()
        status_match = re.search(r'status:\s*(\S+)', lifecycle_text)
        if not status_match:
            warnings.append("LIFECYCLE.md missing status field")

    # Check test files
    tests_dir = skill_path / 'tests'
    if tests_dir.exists():
        for test_file in ['should_trigger.yaml', 'should_not_trigger.yaml', 'expected_behavior.yaml']:
            test_path = tests_dir / test_file
            if test_path.exists():
                try:
                    data = yaml.safe_load(test_path.read_text())
                    if not isinstance(data, list):
                        errors.append(f"tests/{test_file} must be a YAML list")
                    elif len(data) == 0:
                        errors.append(f"tests/{test_file} is empty")
                    elif test_file != 'expected_behavior.yaml':
                        # Check required fields for trigger tests
                        for i, item in enumerate(data):
                            if not isinstance(item, dict):
                                errors.append(f"tests/{test_file}[{i}] must be a dict")
                            elif 'prompt' not in item or 'expected' not in item:
                                errors.append(f"tests/{test_file}[{i}] missing prompt/expected")
                except yaml.YAMLError as e:
                    errors.append(f"tests/{test_file} parse error: {e}")

    # Check skill.md content quality
    if content.count('TODO') > 0:
        warnings.append(f"SKILL.md contains {content.count('TODO')} TODO comments")

    # Check for common documentation patterns
    if '## Usage' not in content and '# Usage' not in content:
        warnings.append("SKILL.md might be missing usage documentation")

    # Check for excessive line length in sections
    for i, line in enumerate(content.split('\n'), 1):
        if len(line) > 100 and not line.startswith('    '):  # Allow code blocks
            if i > 100:  # Don't warn about intro sections
                warnings.append(f"Line {i} is long ({len(line)} chars) - consider breaking it up")

    return len(errors) == 0, errors + warnings


def main():
    if len(sys.argv) < 2:
        skill_path = '.'
    else:
        skill_path = sys.argv[1]

    valid, messages = lint_skill(skill_path)

    for msg in messages:
        print(msg)

    if not valid:
        print(f"\nLinter FAILED with {len([m for m in messages if 'must' in m or 'missing' in m or 'parse error' in m])} errors")
        sys.exit(1)
    else:
        if messages:
            print(f"\nLinter PASSED with {len(messages)} warnings")
        else:
            print("\nLinter PASSED")
        sys.exit(0)


if __name__ == '__main__':
    main()
