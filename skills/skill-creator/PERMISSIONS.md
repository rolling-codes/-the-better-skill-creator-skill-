# skill-creator — Permission Boundaries

The summary `allowed-tools` list is declared in `SKILL.md` frontmatter
(that's the field `quick_validate.py` already recognized) — this file adds
the per-script risk breakdown that a flat list can't express, since
skill-creator's risk profile isn't uniform: `quick_validate.py` only reads,
while `run_eval.py` shells out to a live model.

```yaml
risk:
  level: medium
  reasons:
    - "terminal.execute spawns a live Claude subprocess with the session's own auth — a malformed eval prompt set could burn budget or leak context into eval transcripts"
    - "filesystem.write can overwrite an existing SKILL.md in place with no diff confirmation step by default"
    - "package_skill.py writes a zip archive to disk — path traversal risk is low (single target folder) but not zero if skill_path is attacker-controlled"
```

## Risk rubric

Levels are assigned by this rule, not by feel — apply it to reclassify if
a script's tool list changes:

| Level      | Rule                                                                 |
| ---------- | --------------------------------------------------------------------- |
| **low**    | Only `filesystem.read`, or `filesystem.write`/`filesystem.zip` scoped to files the script itself creates/names — nothing it didn't write can be touched. |
| **medium** | `filesystem.write` to a path supplied by the caller (e.g. an existing `SKILL.md`), OR any `terminal.execute` whose subprocess is bounded (fixed command, no shell interpolation of untrusted input, timeout enforced). |
| **high**   | `network.request` to an unbounded/caller-specified destination, OR `terminal.execute` with unbounded iteration (no max_iterations-style cap) or shell interpolation of untrusted input. |

## Per-script breakdown

| Component                     | Tools needed                          | Risk   |
| ------------------------------ | -------------------------------------- | ------ |
| `quick_validate.py`             | filesystem.read                        | low    |
| `package_skill.py`              | filesystem.read, filesystem.zip        | low    |
| `aggregate_benchmark.py`        | filesystem.read                        | low    |
| `generate_report.py`            | filesystem.read, filesystem.write      | low    |
| `eval-viewer/generate_review.py`| filesystem.read, filesystem.write      | low    |
| `run_eval.py`                   | filesystem.read, terminal.execute      | medium |
| `improve_description.py`        | filesystem.read/write, terminal.execute| medium |
| `run_loop.py`                   | all of the above (orchestrates both)   | medium |

## Audit output (example)

```
skill-creator/scripts/run_loop.py

This skill can modify SKILL.md files and spawn Claude subprocesses
in a loop up to max_iterations times.
Review required before enabling in an unattended/CI context.
```

## Notes

Nothing in skill-creator currently declares `network.*` — `run_eval.py` and
`improve_description.py` reach the model only via the local `claude -p`
subprocess, reusing session auth rather than making direct HTTP calls. If
that changes (e.g. a future version calls the API directly), this file's
`allowed-tools` list needs a `network.request` entry added alongside it.
