# skill-creator — Dependency Graph

> **Hand-maintained, not generated.** This file describes the graph as of
> 2026-07-11 by reading the imports directly — nothing regenerates it when
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
     +-- scripts/quick_validate.py   (standalone — no internal dependencies)
     |
     +-- scripts/package_skill.py    (standalone — packages a target skill folder,
                                       not skill-creator itself)

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
- **Orphan nodes:** scripts/package_skill.py and scripts/quick_validate.py have
  no incoming edges from the rest of the graph — they're invoked directly by
  the user/Claude, not chained from other scripts. Expected for standalone
  CLI utilities; flagged here only so a future audit doesn't mistake it for
  a missing wire-up.
