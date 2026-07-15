#!/usr/bin/env python3
"""
Regression test suite for skill-creator pipeline.
Validates end-to-end skill creation workflow functionality.
"""

import sys
import tempfile
import subprocess
import json
from pathlib import Path


def test_quick_validate():
    """Test that quick_validate.py properly validates a skill."""
    result = subprocess.run(
        [sys.executable, 'scripts/quick_validate.py', '.'],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"quick_validate failed: {result.stderr}"
    assert "valid" in result.stdout.lower(), "Expected validation message"
    return True


def test_lint_validation():
    """Test that lint.py validates the skill-creator's own SKILL.md."""
    result = subprocess.run(
        [sys.executable, 'scripts/lint.py', '.'],
        capture_output=True,
        text=True
    )
    # Should pass (exit 0) or have only warnings
    assert result.returncode == 0, f"lint.py failed: {result.stderr}"
    return True


def test_static_analysis():
    """Test that static_analysis.py can analyze the skill."""
    result = subprocess.run(
        [sys.executable, 'scripts/static_analysis.py', '.'],
        capture_output=True,
        text=True
    )
    # Static analysis can have issues but should run
    assert "Static Analysis Report" in result.stdout, "Expected analysis report"
    return True


def test_skill_yaml_valid():
    """Test that skill.yaml is valid YAML and has required fields."""
    import yaml
    skill_yaml = Path('skill.yaml')
    assert skill_yaml.exists(), "skill.yaml not found"

    with open(skill_yaml) as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict), "skill.yaml must be a dict"
    assert 'name' in data, "skill.yaml missing 'name'"
    assert 'version' in data, "skill.yaml missing 'version'"
    assert data['name'] == 'skill-creator', "skill.yaml name mismatch"

    # Check version format
    import re
    assert re.match(r'^\d+\.\d+\.\d+', data['version']), \
        f"Version {data['version']} doesn't follow semver"

    return True


def test_skill_md_exists():
    """Test that SKILL.md exists and has valid frontmatter."""
    skill_md = Path('SKILL.md')
    assert skill_md.exists(), "SKILL.md not found"

    content = skill_md.read_text()
    assert content.startswith('---'), "SKILL.md missing YAML frontmatter"

    # Check for required sections
    assert '# Skill Creator' in content or 'Skill Creator' in content, \
        "SKILL.md missing title"

    return True


def test_changelog_exists():
    """Test that CHANGELOG.md exists and documents current version."""
    changelog = Path('CHANGELOG.md')
    assert changelog.exists(), "CHANGELOG.md not found"

    content = changelog.read_text()

    # Check for all documented versions
    assert '[1.4.0]' in content or '1.4.0' in content, "CHANGELOG missing v1.4.0"
    assert '[1.3.0]' in content or '1.3.0' in content, "CHANGELOG missing v1.3.0"
    assert '[1.2.0]' in content or '1.2.0' in content, "CHANGELOG missing v1.2.0"
    assert '[1.0.0]' in content or '1.0.0' in content, "CHANGELOG missing v1.0.0"

    return True


def test_dependencies_exist():
    """Test that all declared dependencies in skill.yaml exist."""
    import yaml
    skill_yaml = Path('skill.yaml')

    with open(skill_yaml) as f:
        data = yaml.safe_load(f)

    deps = data.get('dependencies', [])
    for dep in deps:
        dep_path = Path(dep)
        assert dep_path.exists(), f"Dependency not found: {dep}"

    return True


def test_tests_directory():
    """Test that tests directory has required test files."""
    tests_dir = Path('tests')
    assert tests_dir.exists(), "tests/ directory not found"

    # Check for required test files
    assert (tests_dir / 'should_trigger.yaml').exists(), \
        "tests/should_trigger.yaml not found"
    assert (tests_dir / 'should_not_trigger.yaml').exists(), \
        "tests/should_not_trigger.yaml not found"

    return True


def run_tests():
    """Run all regression tests."""
    tests = [
        ("quick_validate", test_quick_validate),
        ("lint_validation", test_lint_validation),
        ("static_analysis", test_static_analysis),
        ("skill_yaml_valid", test_skill_yaml_valid),
        ("skill_md_exists", test_skill_md_exists),
        ("changelog_exists", test_changelog_exists),
        ("dependencies_exist", test_dependencies_exist),
        ("tests_directory", test_tests_directory),
    ]

    passed = 0
    failed = 0
    results = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
            results.append((test_name, "PASS", None))
            print(f"[PASS] {test_name}")
        except AssertionError as e:
            failed += 1
            results.append((test_name, "FAIL", str(e)))
            print(f"[FAIL] {test_name}: {e}")
        except Exception as e:
            failed += 1
            results.append((test_name, "ERROR", str(e)))
            print(f"[ERROR] {test_name}: ERROR - {e}")

    print(f"\n{passed} passed, {failed} failed")

    for test_name, status, msg in results:
        status_str = "[PASS]" if status == "PASS" else f"[{status}]"
        if msg:
            print(f"  {status_str} {test_name}: {msg}")
        else:
            print(f"  {status_str} {test_name}")

    return failed == 0, results


if __name__ == '__main__':
    success, results = run_tests()
    sys.exit(0 if success else 1)
