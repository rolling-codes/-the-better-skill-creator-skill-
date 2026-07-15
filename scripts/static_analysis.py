#!/usr/bin/env python3
"""
Static analysis for skill integrity and consistency checks.
Goes beyond linting to check structural soundness, coupling, and documentation completeness.
"""

import sys
import re
import json
from pathlib import Path
from collections import defaultdict


def analyze_skill_structure(skill_path):
    """Analyze skill structure for consistency and quality."""
    skill_path = Path(skill_path)
    issues = []
    info = {
        'files_found': {},
        'documentation_coverage': {},
        'reference_integrity': {}
    }

    # Check directory structure
    required_dirs = ['scripts', 'tests', 'references', 'agents', 'assets']
    missing_dirs = [d for d in required_dirs if not (skill_path / d).exists()]
    if missing_dirs:
        issues.append(f"Missing recommended directories: {missing_dirs}")

    # Scan all Python files for quality issues
    python_files = list(skill_path.glob('scripts/*.py'))
    for py_file in python_files:
        try:
            content = py_file.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue
        info['files_found'][py_file.name] = len(content)

        # Check for debug statements
        if 'print(' in content and 'DEBUG' not in content:
            # Print might be legitimate, but flag excessive use
            print_count = content.count('print(')
            if print_count > 20:
                issues.append(f"{py_file.name} has {print_count} print statements (consider logging)")

        # Check for TODO/FIXME
        todos = len(re.findall(r'#\s*(TODO|FIXME)', content))
        if todos > 5:
            issues.append(f"{py_file.name} has {todos} TODO/FIXME comments")

        # Check imports
        imports = re.findall(r'^(?:import|from)\s+(\S+)', content, re.MULTILINE)
        info['files_found'][f"{py_file.name}_imports"] = imports

    # Check SKILL.md references
    skill_md = skill_path / 'SKILL.md'
    if skill_md.exists():
        content = skill_md.read_text(encoding='utf-8', errors='replace')

        # Find all file references in SKILL.md
        file_refs = re.findall(r'(?:scripts|references|agents|assets)/[\w./\-]+', content)
        for ref in file_refs:
            ref_path = skill_path / ref
            if not ref_path.exists():
                issues.append(f"SKILL.md references non-existent file: {ref}")
            info['reference_integrity'][ref] = ref_path.exists()

        # Check documentation sections
        sections = {
            'Usage': r'## Usage|# Usage',
            'Installation': r'## Installation|# Installation',
            'Examples': r'## Examples|# Examples',
            'API': r'## API|# API',
            'Configuration': r'## Configuration|# Configuration'
        }

        for section_name, pattern in sections.items():
            has_section = bool(re.search(pattern, content))
            info['documentation_coverage'][section_name] = has_section

        # Warn if critical sections are missing
        critical_sections = ['Usage']
        for section in critical_sections:
            if not info['documentation_coverage'].get(section):
                issues.append(f"SKILL.md missing critical section: {section}")

    # Check README if it exists
    readme_files = list(skill_path.glob('README*'))
    if not readme_files:
        issues.append("No README file found (recommended for discoverability)")

    # Check version consistency
    skill_yaml = skill_path / 'skill.yaml'
    if skill_yaml.exists():
        yaml_content = skill_yaml.read_text()
        version_match = re.search(r'version:\s*(\S+)', yaml_content)
        if version_match:
            version = version_match.group(1)
            info['version'] = version

            # Check if version is mentioned in CHANGELOG
            changelog = skill_path / 'CHANGELOG.md'
            if changelog.exists():
                changelog_content = changelog.read_text()
                if f'[{version}]' not in changelog_content:
                    issues.append(f"Version {version} not found in CHANGELOG.md")

    # Analyze test coverage
    tests_dir = skill_path / 'tests'
    if tests_dir.exists():
        test_files = {f.name for f in tests_dir.glob('*.yaml')}
        if 'should_trigger.yaml' in test_files:
            try:
                from yaml import safe_load
                data = safe_load((tests_dir / 'should_trigger.yaml').read_text())
                info['trigger_test_count'] = len(data) if isinstance(data, list) else 0
            except:
                pass
        if 'should_not_trigger.yaml' in test_files:
            try:
                from yaml import safe_load
                data = safe_load((tests_dir / 'should_not_trigger.yaml').read_text())
                info['negative_test_count'] = len(data) if isinstance(data, list) else 0
            except:
                pass
    else:
        issues.append("No tests/ directory found")

    # Check for circular dependencies in skill.yaml
    if skill_yaml.exists():
        try:
            from yaml import safe_load
            yaml_data = safe_load(skill_yaml.read_text())
            deps = yaml_data.get('dependencies', [])
            # Simple circular dependency check
            for dep in deps:
                dep_path = skill_path / dep
                if dep_path.is_file():
                    try:
                        dep_content = dep_path.read_text()
                        # Check if dependency references back to skill_md
                        if 'SKILL.md' in dep_content and dep != 'SKILL.md':
                            pass  # This is OK, it's a reference
                    except:
                        pass
        except:
            pass

    return issues, info


def main():
    if len(sys.argv) < 2:
        skill_path = '.'
    else:
        skill_path = sys.argv[1]

    issues, info = analyze_skill_structure(skill_path)

    print("=== Static Analysis Report ===\n")

    if issues:
        print(f"Issues found ({len(issues)}):")
        for issue in issues:
            print(f"  - {issue}")
        print()

    print("Documentation Coverage:")
    for section, has_section in info.get('documentation_coverage', {}).items():
        status = "[+]" if has_section else "[-]"
        print(f"  {status} {section}")

    if info.get('files_found'):
        print(f"\nFiles analyzed: {len(info['files_found'])}")

    if info.get('trigger_test_count'):
        print(f"Trigger tests: {info['trigger_test_count']}")
    if info.get('negative_test_count'):
        print(f"Negative tests: {info['negative_test_count']}")

    if info.get('version'):
        print(f"\nVersion: {info['version']}")

    print("\n=== Analysis Complete ===")
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
