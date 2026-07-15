#!/usr/bin/env python3
"""Run a skill's tests/ regression suite against the real eval machinery.

tests/should_trigger.yaml and tests/should_not_trigger.yaml use
{prompt, expected} pairs. run_eval.py expects a JSON eval-set of
{query, should_trigger} dicts instead — this script converts and
calls it, so the two files that already exist stay the single
source of truth instead of inventing a parallel test runner.

tests/expected_behavior.yaml is not auto-gradable by run_eval.py
(it checks triggering only, not post-trigger behavior). Without a
transcript this script prints it as a checklist for manual review.
With --grade-transcript it feeds the assertions plus the transcript
through agents/grader.md via `claude -p` and writes grading.json in
the viewer's expected format (text/passed/evidence fields).

Usage:
    python scripts/skill_test.py <path/to/skill-folder> [options] [run_eval.py flags...]

Options (consumed here, not passed through):
    --grade-transcript PATH   transcript to grade expected_behavior.yaml against
    --outputs-dir PATH        output files from that run (optional)
    --grade-only              skip the trigger tests, only grade
    --grade-output PATH       where to write grading.json (default: alongside transcript)

Examples:
    python scripts/skill_test.py skill-creator
    python scripts/skill_test.py skill-creator --runs-per-query 5 --timeout 45
    python scripts/skill_test.py skill-creator --grade-transcript ws/iteration-1/eval-0/with_skill/transcript.md --outputs-dir ws/iteration-1/eval-0/with_skill/outputs
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def load_trigger_yaml(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text()) or []
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a YAML list of {{prompt, expected}} entries")
    result = []
    for i, item in enumerate(data):
        if not isinstance(item, dict) or "prompt" not in item or "expected" not in item:
            raise ValueError(
                f"{path} entry {i} is malformed — expected {{prompt: ..., expected: true/false}}, got: {item!r}"
            )
        result.append({"query": item["prompt"], "should_trigger": bool(item["expected"])})
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/skill_test.py <path/to/skill-folder> [options] [run_eval.py flags...]")
        sys.exit(1)

    skill_path = Path(sys.argv[1]).resolve()
    raw_args = sys.argv[2:]

    # Peel off the flags this script owns; everything else passes through.
    grade_transcript = outputs_dir = grade_output = None
    grade_only = False
    passthrough_args = []
    i = 0
    while i < len(raw_args):
        a = raw_args[i]
        if a == "--grade-transcript":
            grade_transcript = raw_args[i + 1]; i += 2
        elif a == "--outputs-dir":
            outputs_dir = raw_args[i + 1]; i += 2
        elif a == "--grade-output":
            grade_output = raw_args[i + 1]; i += 2
        elif a == "--grade-only":
            grade_only = True; i += 1
        else:
            passthrough_args.append(a); i += 1

    tests_dir = skill_path / "tests"

    if not tests_dir.exists():
        print(f"No tests/ directory found at {tests_dir}")
        sys.exit(1)

    rc = 0
    if not grade_only:
        rc = run_trigger_tests(skill_path, tests_dir, passthrough_args)

    if grade_transcript:
        grade_rc = grade_behavior(skill_path, Path(grade_transcript).resolve(), outputs_dir, grade_output)
        rc = rc or grade_rc
    elif not grade_only:
        print_behavior_checklist(tests_dir)

    sys.exit(rc)


def run_trigger_tests(skill_path: Path, tests_dir: Path, passthrough_args: list) -> int:

    try:
        eval_set = load_trigger_yaml(tests_dir / "should_trigger.yaml") + \
            load_trigger_yaml(tests_dir / "should_not_trigger.yaml")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not eval_set:
        print("tests/should_trigger.yaml and tests/should_not_trigger.yaml are both empty or missing.")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(eval_set, f)
        eval_set_path = f.name

    print(f"Running {len(eval_set)} trigger tests via run_eval.py...\n")
    result = subprocess.run(
        [
            sys.executable, "-m", "scripts.run_eval",
            "--eval-set", eval_set_path,
            "--skill-path", str(skill_path),
            *passthrough_args,
        ],
        cwd=str(skill_path),
        capture_output=True,
        text=True,
    )

    # run_eval.py's --runs-per-query already computes a per-query trigger_rate
    # (fraction of repeated runs that triggered) — that rate IS the confidence
    # score described in references/trigger-confidence.md. Surface it here
    # instead of leaving that doc describe a number nothing ever computes.
    try:
        eval_output = json.loads(result.stdout)
        print(f"{'PASS':<6} {'confidence':<12} query")
        for r in eval_output.get("results", []):
            status = "PASS" if r["pass"] else "FAIL"
            print(f"{status:<6} {r['trigger_rate']:<12.2f} {r['query'][:70]}")
        summary = eval_output.get("summary", {})
        print(f"\n{summary.get('passed', '?')}/{summary.get('total', '?')} passed")
    except (json.JSONDecodeError, KeyError):
        # run_eval.py failed before producing JSON (e.g. bad --skill-path) —
        # fall through to raw output rather than hiding the real error.
        print(result.stdout)
        print(result.stderr, file=sys.stderr)

    return result.returncode


def grade_behavior(skill_path: Path, transcript: Path, outputs_dir, grade_output) -> int:
    """Grade tests/expected_behavior.yaml against a real transcript via agents/grader.md.

    Uses the same `claude -p` mechanism as run_eval.py, so it works anywhere
    the description-optimization loop works (Claude Code, Cowork) and fails
    with a clear message elsewhere.
    """
    behavior_path = skill_path / "tests" / "expected_behavior.yaml"
    grader_path = skill_path / "agents" / "grader.md"
    if not behavior_path.exists():
        print("No tests/expected_behavior.yaml to grade.")
        return 1
    if not grader_path.exists():
        print("agents/grader.md not found — cannot grade.")
        return 1

    behavior = yaml.safe_load(behavior_path.read_text()) or []
    expectations = [e for item in behavior for e in item.get("expected_behavior", [])]
    if not expectations:
        print("tests/expected_behavior.yaml contains no expected_behavior entries.")
        return 1

    prompt = f"""{grader_path.read_text()}

---

Grade the following expectations against the transcript and outputs below.
Respond with ONLY a JSON object, no preamble, no markdown fences, shaped as:
{{"expectations": [{{"text": "...", "passed": true, "evidence": "..."}}]}}
Use exactly the field names text, passed, and evidence — the eval viewer
depends on them.

expectations:
{json.dumps(expectations, indent=2)}

transcript_path: {transcript}

transcript contents:
{transcript.read_text()}

outputs_dir: {outputs_dir if outputs_dir else "none provided"}
"""

    import os
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    print(f"Grading {len(expectations)} expectations via claude -p ...")
    try:
        proc = subprocess.run(
            ["claude", "-p", prompt],
            capture_output=True, text=True, env=env, timeout=600,
        )
    except FileNotFoundError:
        print("`claude` CLI not found — grading needs Claude Code or Cowork.")
        print("Fallback: review these manually against the transcript:")
        for e in expectations:
            print(f"  - {e}")
        return 1

    raw = proc.stdout.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        grading = json.loads(raw)
        assert isinstance(grading.get("expectations"), list)
    except (json.JSONDecodeError, AssertionError):
        print("Grader did not return valid grading JSON. Raw output:")
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        return 1

    out_path = Path(grade_output) if grade_output else transcript.parent / "grading.json"
    out_path.write_text(json.dumps(grading, indent=2))
    passed = sum(1 for e in grading["expectations"] if e.get("passed"))
    print(f"{passed}/{len(grading['expectations'])} behavior expectations passed.")
    print(f"Wrote {out_path}")
    for e in grading["expectations"]:
        status = "PASS" if e.get("passed") else "FAIL"
        print(f"{status:<6} {e.get('text', '')[:70]}")
    return 0 if passed == len(grading["expectations"]) else 2


def print_behavior_checklist(tests_dir: Path):
    behavior_path = tests_dir / "expected_behavior.yaml"
    if behavior_path.exists():
        behavior = yaml.safe_load(behavior_path.read_text()) or []
        print(f"\n{len(behavior)} expected_behavior.yaml entries were not graded in this run.")
        print("Rerun with --grade-transcript <path> to grade them, or review manually:")
        for item in behavior:
            print(f"  - {item['prompt'][:70]}")


if __name__ == "__main__":
    main()
