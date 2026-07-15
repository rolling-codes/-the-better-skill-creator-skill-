# skill-creator — Lifecycle

status: active
<!-- Canonical value lives in skill.yaml's `lifecycle` field.
     quick_validate.py fails the build if these two disagree — don't
     edit one without the other. -->

## States (reference)
- **active** — current, recommended, safe to trigger normally.
- **experimental** — new, triggers normally, but behavior may still change
  release to release; flag this to the user if asked "is this stable?"
- **deprecated** — still triggers, but every response should surface the
  replacement so usage migrates naturally.
- **archived** — does not trigger. Kept on disk for reference/rollback only.

No prior version of this skill is deprecated or archived — this is the
first tracked lifecycle entry (skill.yaml `last-audit: 2026-07-11` is the
same date this file was introduced).

## Worked example (for future deprecations)

old-python-helper
deprecated

Replacement:
python-development-agent

When a skill enters `deprecated`, `quick_validate.py` should warn on
package/eval runs against it, and `package_skill.py` should refuse to
produce a distributable `.skill` file without an explicit `--force` flag,
so a deprecated skill can't be re-shipped by accident.
