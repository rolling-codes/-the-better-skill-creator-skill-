# Audit Mode — Gates 0, 3, 4, 5

Review an existing SKILL.md without necessarily rewriting it. Report findings even where you make no change — a clean audit still lists what was checked.

## Gate 0 — Evidence
Read the skill at `target_skill` plus every sibling SKILL.md under `skills_root` (already done from the router). Note `target_skill`'s current description, paths, and allowed-tools verbatim before critiquing.

## Gate 3 — Iron Law and Red Flags check

- Run `scripts/lint.py <target>/SKILL.md` first and fold its output into this gate rather than re-deriving the same findings by hand — it directly checks boundary/trigger clauses, unused variables, ungrounded tool grants, and bare MUST/NEVER.
- Run `scripts/dependency_graph.py <target>/` if the target has a `workflows/` or `scripts/` folder; report any broken link or orphan as its own finding — a broken reference is a production failure waiting to happen, not a style note.
- Does the skill state one non-negotiable rule, phrased as reasoning ("X because Y"), not a bare MUST/NEVER? If it's a bare imperative, flag it as fragile and propose the reasoning-based rewrite.
- Does a Red Flags table exist? If missing, run a condensed version of Gate 1: **Have the agent (Claude) introspect:** Ask the agent to identify three ways an agent could rationalize skipping the important steps of this skill. This produces grounded rationalizations from agent self-awareness, not user speculation. Add them to the Red Flags table.
- If a Red Flags table exists, check whether any row is generic/placeholder-sounding rather than grounded in an actual failure — generic rows are close to worthless and should be replaced with agent-introspected rationalizations.

## Gate 4 — Adversarial Self-Critique

Identify the single most likely way this skill misfires in practice: over-triggering, under-triggering, or inconsistent output. State it plainly, with a concrete example scenario, rather than a vague "could be improved."

## Gate 5 — Blast Radius Analysis

Run `scripts/overlap_check.py` comparing `target_skill`'s description against every sibling skill found in Gate 0. Report any pair above the overlap threshold with the specific overlapping phrase or concept. Propose a narrower Boundary clause where overlap is real, not just adjacent-sounding.

## Output

- The description, Iron Law, and Red Flags findings (pass/fail per check, not just a rewrite)
- Gate 4 critique paragraph
- Gate 5 overlap table (pair, overlap score, proposed fix) or "no overlap found"
- If the user asks for a rewrite, use `str_replace` on the existing SKILL.md to apply the specific fixes found above (or `create_file` if the rewrite is substantial enough that a full replacement is clearer than a patch); otherwise stop at findings without touching the file
