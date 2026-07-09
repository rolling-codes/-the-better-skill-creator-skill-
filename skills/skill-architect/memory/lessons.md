# Lessons — skill-architect

Append-only. Never rewrite or delete a past entry — if a lesson turns
out to be wrong or superseded, add a new entry that says so and points
back to the old one. The value of this file is the trail, not a clean
final state.

Log an entry here whenever, in real use (not a hypothetical), one of
these happens:
- A skill built or audited by skill-architect misfired in production
  (over-triggered, under-triggered, or produced inconsistent output).
- A Blast Radius overlap was discovered *after* shipping, meaning
  Gate 5 missed it — that's a bug in the overlap heuristic worth
  recording, not just a one-off fix.
- A Red Flags table row turned out to be wrong or incomplete when a
  real agent found a rationalization nobody listed.
- Any manual fix was applied to a generated skill that skill-architect
  itself should have caught.

Each entry should be short enough to scan in a few seconds. Use this
shape:

```
## YYYY-MM-DD — <short title>

**What happened:** one or two sentences, concrete, no hedging.
**Root cause:** which gate/check should have caught this and didn't.
**Pattern:** is this a one-off, or does it generalize to other skills?
**Fix applied:** what changed as a result (link to a commit/file if useful).
**Feeds back into:** which Red Flags row, lint.py check, or Iron Law
  clause this should strengthen — or "new check needed" if none exists yet.
```

Anything that generalizes across 2+ entries is a candidate to graduate
into `scripts/lint.py` as a real check, or into the Iron Law's Red
Flags table, rather than staying only as a memory entry forever.

---

<!-- Entries go below this line. Delete this comment once the first real entry is added. -->

## 2026-07-09 — dependency_graph.py false orphans on real skills

**What happened:** Ran `lint.py`/`dependency_graph.py` against three real skills (docx, dev-workflow, skill-creator) instead of only skill-architect. `dependency_graph.py` flagged dozens of legitimate internal files (docx's `scripts/office/**`, skill-creator's `scripts/*.py`) as orphans, and truncated a nested path (`scripts/office/pack.py`) into a phantom broken link on `scripts/office`. It also silently ignored dev-workflow's `references/` folder entirely, reporting a false "clean" instead of not-checked. Separately, `lint.py`'s bare-imperative check flagged skill-creator's own prose *warning against* writing ALWAYS/NEVER in caps as if it were an instance of the anti-pattern.

**Root cause:** `dependency_graph.py` assumed every real file is named individually in prose (skill-architect's own convention) and only knew about `workflows/`+`scripts/` by name — neither assumption holds for skills that document a directory generically or use other folder names (`references/`, `agents/`, `assets/`). `lint.py`'s bare-imperative check matched MUST/NEVER anywhere in a sentence with no positional awareness, so discussing the anti-pattern tripped the same check as committing it.

**Pattern:** Generalizes. Any check built and validated against only one example (especially the tool's own output) is unverified against real variety — this is the single-happy-path-run failure mode the framework itself warns about, just caught in the tooling meant to prevent it.

**Fix applied:** `dependency_graph.py` now discovers top-level directories dynamically instead of hardcoding `workflows`/`scripts`, requires a real extension in the reference regex so nested paths aren't truncated, and splits findings into high-confidence ORPHAN (directory never mentioned at all) vs informational UNNAMED (directory acknowledged generically, file just not named — legitimate, not a defect). `lint.py`'s bare-imperative check now requires MUST/NEVER within the first few words of the sentence, since real commands front-load the imperative and meta-discussion usually doesn't. Both fixes verified against a skill-architect baseline (unchanged: 0 broken/orphan, 0 lint issues) before being trusted.

**Feeds back into:** `scripts/lint.py` and `scripts/dependency_graph.py` directly (already applied). Also a standing practice worth keeping: any future change to these scripts should re-run against skill-architect itself as a regression check, plus at least one external skill, before being called done — a clean run against only the tool's own skill is not evidence of correctness.

## 2026-07-09 — dependency_graph.py reported every file broken AND orphaned on Windows

**What happened:** During the dev-workflow-pack rebuild (first production use on Windows), `dependency_graph.py` reported all 11 of dev-workflow's `references/*.md` files as simultaneously BROKEN and ORPHANED. Self-test against skill-architect's own tree showed the same: its own `scripts/lint.py` reported MISSING while sitting on disk.

**Root cause:** `str(Path.relative_to(root))` yields backslash-separated paths on Windows (`references\memory.md`), while the regex extracts forward-slash references from markdown (`references/memory.md`). The set comparison never matched, so every named reference was "missing" and every disk file was "unnamed"; the orphan split's `f.split("/", 1)` then failed on backslash paths, promoting all of them to ORPHAN. The 2026-07-09 fix above was verified only on the platform it was written on — cross-platform behavior was never exercised.

**Pattern:** Generalizes — same failure family as the previous entry: a check validated against too narrow a sample, this time narrow in *platform* rather than in skill variety. The contradiction in the output (a file cannot be both broken and orphaned) was itself the tell; contradictory findings from a checker mean the checker is broken, not the target.

**Fix applied:** `actual_files` now uses `Path.relative_to(root).as_posix()` so disk paths compare equal to markdown references on every platform. Verified: skill-architect self-test returns clean, dev-workflow returns clean with one legitimate UNNAMED.

**Feeds back into:** the standing practice from the previous entry, extended: regression runs for these scripts must include a Windows run (or at minimum, path handling must be posix-normalized at every comparison boundary). If a checker's own output is self-contradictory, treat the checker as the bug first.

## 2026-07-09 — vague-trigger check false-positived on quoted example phrases (two stacked causes)

**What happened:** `lint.py` WARNed that commit-message's trigger was "broad or vague" because the quoted example phrase `"help me commit"` contains the vague-term `help`. First fix (strip quoted spans before scanning) tested clean in isolation but the CLI still WARNed.

**Root cause:** Two stacked bugs. (1) The vague-term scan treated quoted example phrases — the most concrete part of a trigger — as prose. (2) `read_text()` with no encoding uses cp1252 on Windows, misdecoding the UTF-8 em-dash into mojibake whose last character is a stray `”`; that extra quote shifted quote pairing so "help me commit" fell *outside* the stripped spans, keeping the false positive alive even after fix (1).

**Pattern:** Generalizes twice over. A heuristic that penalizes the exact concreteness it exists to encourage is the same shape as the earlier bare-imperative false positive. And implicit platform-default encoding is the same shape as the backslash-path entry — Windows behavior diverging silently from the platform the check was written on.

**Fix applied:** `lint.py` strips quoted spans (ASCII and curly quotes) from the trigger clause before the vague-word scan, and both `lint.py` and `dependency_graph.py` now read files with explicit `encoding="utf-8"`. Verified: commit-message WARN cleared; skill-architect self-lint, dev-workflow, pr-description, code-review all unchanged.

**Feeds back into:** every future file read in these scripts must state `encoding="utf-8"` explicitly — grep for bare `read_text(`/`open(` when touching them. When a fix verified in isolation doesn't change CLI behavior, diff the two execution paths (here: explicit utf-8 in the test vs. default encoding in the CLI) before assuming the fix is wrong.
