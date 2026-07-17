# skill-creator — Dependency Graph

> **Hand-maintained, not generated.** This file describes the graph as of
> 2026-07-11 (revised same day after the gap-closing pass) by reading the imports directly — nothing regenerates it when
> a script changes. The one piece that *is* enforced: `quick_validate.py`
> verifies every path listed in `skill.yaml`'s `dependencies` field exists
> on disk. That catches a deleted/renamed file; it does not catch this
> graph's edges going stale. Re-read the scripts before trusting this file
> after a refactor.

skill-creator
     |
     +-- agents/analyzer.md          (post-hoc: explains why a comparator winner won)
     |        depends on --> agents/comparator.md output (blind comparison results)
     |
     +-- agents/comparator.md        (blind A/B comparison of two skill outputs)
     |        depends on --> scripts/run_loop.py (supplies the two outputs to compare)
     |
     +-- agents/grader.md            (evaluates expected_behavior.yaml assertions against a transcript)
     |        depends on --> tests/expected_behavior.yaml
     |
     +-- scripts/run_eval.py         (runs should_trigger.yaml / should_not_trigger.yaml)
     |        depends on --> scripts/utils.py (parse_skill_md)
     |        depends on --> `claude -p` subprocess (external, session auth)
     |
     +-- scripts/improve_description.py
     |        depends on --> scripts/run_eval.py output (eval results JSON)
     |        depends on --> `claude -p` subprocess (external, session auth)
     |
     +-- scripts/run_loop.py         (orchestrates eval + improve in a loop)
     |        depends on --> scripts/run_eval.py
     |        depends on --> scripts/improve_description.py
     |
     +-- scripts/aggregate_benchmark.py
     |        depends on --> grading.json files produced by scripts/run_loop.py runs
     |
     +-- scripts/generate_report.py
     |        depends on --> scripts/run_loop.py JSON output
     |
     +-- eval-viewer/generate_review.py
     |        depends on --> scripts/aggregate_benchmark.py output
     |        renders  --> eval-viewer/viewer.html, assets/eval_review.html
     |
     +-- scripts/skill_test.py       (runs tests/*.yaml through the eval machinery)
     |        depends on --> tests/should_trigger.yaml, tests/should_not_trigger.yaml
     |        depends on --> scripts/run_eval.py (subprocess, -m from skill dir)
     |        depends on --> agents/grader.md + tests/expected_behavior.yaml
     |                       (--grade-transcript mode, via `claude -p`)
     |
     +-- scripts/validate_all.sh     (gate: chains the two checks below)
     |        depends on --> scripts/quick_validate.py
     |        depends on --> scripts/skill_test.py
     |
     +-- scripts/quick_validate.py   (no internal dependencies; enforces the
     |                                reachability invariant, audit freshness,
     |                                and removal detection in three directions:
     |                                dangling doc pointers, unregistered files,
     |                                and PERMISSIONS rows <-> scripts sync)
     |
     +-- scripts/package_skill.py    (imports quick_validate.validate_skill;
                                       run as `python -m scripts.package_skill`
                                       from the skill directory)

     +-- scripts/check_upstream.py   (network: codeload.github.com tarball;
     |                                no internal script dependencies)
     |
     scripts/ci/validate.yml         (CI node — invokes validate_all.sh and
                                       check_upstream.py inside GitHub Actions;
                                       installed by copying to .github/workflows/)

     references/environments.md      (doc node — consumed by SKILL.md pointer,
                                       no script dependencies)

     tests/meta/test_validators.py   (meta-test node — subprocesses
                                       quick_validate.py against mutated
                                       copies; imports skill_test.py for
                                       probe, quote, and Wilson unit tests)

     tests/baseline.json             (data node — written by skill_test.py
                                       --update-baseline, read on every
                                       trigger-test run for regression checks)

## Detected issues (run against the graph above)

- **Cycles:** none. run_loop.py -> {run_eval.py, improve_description.py} is a
  fan-out, not a cycle; neither script calls back into run_loop.py.
- **Duplicate responsibilities:** aggregate_benchmark.py and generate_report.py
  both consume run_loop.py output and both produce a summary view. They don't
  overlap in format (stats table vs. pass/fail HTML) but should be documented
  as siblings, not merged, to avoid a future contributor collapsing them.
- **Missing dependencies:** scripts/run_eval.py and scripts/improve_description.py
  both shell out to `claude -p` as an external subprocess dependency that isn't
  declared anywhere in SKILL.md frontmatter — added to `skill.yaml` under
  `compatibility` as part of Gap 1's fix.
- **Orphan nodes:** none remaining. quick_validate.py and skill_test.py gained
  incoming edges from validate_all.sh, and package_skill.py imports
  quick_validate. Every script is now reachable from either SKILL.md
  instructions or the validate_all.sh gate.
