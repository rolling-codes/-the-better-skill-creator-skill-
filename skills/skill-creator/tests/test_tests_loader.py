"""Regression tests for scripts/tests_loader.py — the shared trigger-test loader.

Covers both field conventions, legacy string labels, malformed rejection,
dedupe/conflict handling, Unicode, spaces in paths, external target dirs, and
that every generated archetype file loads.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

SKILL_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_PATH))

from scripts.tests_loader import (
    TestCaseError,
    load_trigger_suite,
    load_yaml_cases,
    normalize_cases,
)


def test_bool_labels_both_field_conventions():
    data = [
        {"query": "a", "should_trigger": True},
        {"prompt": "b", "expected": False},
    ]
    assert normalize_cases(data) == [
        {"query": "a", "should_trigger": True},
        {"query": "b", "should_trigger": False},
    ]


def test_legacy_string_labels():
    data = [
        {"query": "a", "expected": "triggered"},
        {"query": "b", "expected": "not_triggered"},
    ]
    out = normalize_cases(data)
    assert [c["should_trigger"] for c in out] == [True, False]


@pytest.mark.parametrize("label,expected", [
    ("yes", True), ("no", False), ("true", True), ("false", False),
    (1, True), (0, False), ("TRIGGERED", True), ("Not_Triggered", False),
])
def test_yesno_numeric_and_case_insensitive_labels(label, expected):
    assert normalize_cases([{"query": "q", "expected": label}])[0]["should_trigger"] is expected


def test_prompt_and_query_aliases_equivalent():
    a = normalize_cases([{"prompt": "x", "expected": True}])
    b = normalize_cases([{"query": "x", "should_trigger": True}])
    assert a == b


def test_dedupe_identical_query():
    data = [
        {"query": "dup", "should_trigger": True},
        {"query": "dup", "should_trigger": True},
    ]
    assert normalize_cases(data) == [{"query": "dup", "should_trigger": True}]


def test_conflicting_duplicate_raises():
    data = [
        {"query": "dup", "should_trigger": True},
        {"query": "dup", "should_trigger": False},
    ]
    with pytest.raises(TestCaseError, match="conflicting"):
        normalize_cases(data)


@pytest.mark.parametrize("bad", [
    [{"should_trigger": True}],             # missing query
    [{"query": "q"}],                       # missing expected
    [{"query": 123, "expected": True}],     # non-string query
    [{"query": "q", "expected": "maybe"}],  # unrecognized label
    ["not a dict"],                         # non-dict entry
])
def test_malformed_entries_raise(bad):
    with pytest.raises(TestCaseError):
        normalize_cases(bad)


def test_empty_prompt_is_a_valid_edge_case():
    # An empty prompt with an explicit label is a deliberate "should not trigger"
    # edge case (generated/edge_cases.yaml), not malformed.
    out = normalize_cases([{"prompt": "", "should_trigger": False}])
    assert out == [{"query": "", "should_trigger": False}]


def test_non_list_raises():
    with pytest.raises(TestCaseError):
        normalize_cases({"query": "q", "should_trigger": True})


def test_unicode_query_preserved():
    q = "créer une compétence — 日本語 — 🎯"
    out = normalize_cases([{"query": q, "should_trigger": True}])
    assert out[0]["query"] == q


def test_load_yaml_from_path_with_spaces(tmp_path):
    d = tmp_path / "dir with spaces"
    d.mkdir()
    f = d / "should_trigger.yaml"
    f.write_text(yaml.safe_dump([{"prompt": "p", "expected": True}]), encoding="utf-8")
    assert load_yaml_cases(f) == [{"query": "p", "should_trigger": True}]


def test_load_trigger_suite_external_dir(tmp_path):
    (tmp_path / "should_trigger.yaml").write_text(
        yaml.safe_dump([{"prompt": "pos", "expected": True}]), encoding="utf-8")
    (tmp_path / "should_not_trigger.yaml").write_text(
        yaml.safe_dump([{"prompt": "neg", "expected": False}]), encoding="utf-8")
    suite = load_trigger_suite(tmp_path)
    assert {c["query"]: c["should_trigger"] for c in suite} == {"pos": True, "neg": False}


def test_suite_dedupes_across_both_files(tmp_path):
    (tmp_path / "should_trigger.yaml").write_text(
        yaml.safe_dump([{"prompt": "same", "expected": True}]), encoding="utf-8")
    (tmp_path / "should_not_trigger.yaml").write_text(
        yaml.safe_dump([{"prompt": "same", "expected": True}]), encoding="utf-8")
    assert len(load_trigger_suite(tmp_path)) == 1


def test_missing_file_is_empty(tmp_path):
    assert load_yaml_cases(tmp_path / "nope.yaml") == []


def test_all_generated_archetypes_load():
    generated = Path(__file__).resolve().parent / "generated"
    files = sorted(generated.glob("*.yaml"))
    assert files, "expected generated archetype fixtures to exist"
    for f in files:
        cases = load_yaml_cases(f)
        assert cases, f"{f.name} produced no cases"
        for c in cases:
            assert isinstance(c["should_trigger"], bool)
            assert isinstance(c["query"], str)  # may be "" for empty-input edge cases
