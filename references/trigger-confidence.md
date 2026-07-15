# skill-creator — Trigger Confidence

## What's actually implemented

`run_eval.py` already computes a real confidence number: with the default
`--runs-per-query 3`, each test query runs multiple times and `trigger_rate`
(triggers / runs, 0.0–1.0) is returned in its JSON output. `skill_test.py`
now surfaces that number per-query instead of collapsing it to pass/fail:

```
PASS   confidence   query
PASS   1.00         I want to make a new Claude skill for reviewing SQL...
PASS   0.67         The description on my skill isn't triggering reliab...
FAIL   0.33         Explain what a SKILL.md file is
```

A query passing at 0.67 rather than 1.00 is a real signal — the
description triggers inconsistently, worth tightening even though the
test currently counts as a pass at the 0.5 threshold.

## What's aspirational — multi-skill routing confidence

The rest of this doc describes a routing layer that does **not** exist in
this codebase. `run_eval.py` scores one skill's description against a
query; it has no concept of comparing scores across multiple skills to
decide which to load. Treat the example below as a design target, not a
description of current behavior.

```
Prompt:
"My skill's description isn't triggering reliably and I think its
structure has some architectural issues too."

skill-creator:        0.78   # hypothetical — no cross-skill router exists
skill-architect:       0.71   # hypothetical — same

Decision (not implemented):
Load both.
```

If this gets built, `run_eval.py`'s existing per-query `trigger_rate` is
the right primitive to reuse — run the same query against multiple
skills' descriptions and compare rates — rather than inventing a second
scoring mechanism.
