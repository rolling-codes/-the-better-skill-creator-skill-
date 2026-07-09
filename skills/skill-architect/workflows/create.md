# Create Mode — Gates 0 through 6

Run in order. Do not skip a gate because the skill "seems simple" — that rationalization is itself the first Red Flag entry in the Iron Law table.

## Gate 0 — Evidence
Already run from SKILL.md router. Confirm the table of existing skills (name, description, paths, allowed-tools) is populated before continuing.

## Gate 1 — Adversarial Elicitation

Interview the user one level deeper than standard Q&A:

1. What should this skill enable Claude to do?
2. When should this skill trigger — what phrases, file types, or contexts?
3. What's the expected output format?
4. Give two concrete real examples from this project: one past success, one past failure. Ground the skill in actual trial-and-error, not generic best practice.

After every answer, ask exactly one follow-up "why" or edge-case probe before moving to the next question — don't accept first answers at face value.

Then: **Have the agent introspect.** Ask the agent (Claude): "You are an agent. How would you rationalize skipping the important steps of this skill? Give me three rationalizations you would actually make." Store these three answers verbatim — they become the first three rows of the Red Flags table in Gate 3, not generic placeholders.

**Why this works:** An agent understands agent behavior better than a human can speculate about it. Agents have actual incentive structures, token economy pressures, and pattern-matching blindnesses that humans reason about differently. Self-introspection by the agent produces rationalizations grounded in how agents actually think, not how users imagine they might think.

Escalation if the agent's rationalizations are too generic: Ask the agent to role-play a specific scenario (e.g., "You're under time pressure and have already spent 60% of your context window. How do you rationalize skipping this step?") to make the rationalization concrete.

## Gate 2 — Trigger Contract (YAML frontmatter)

- `name`: kebab-case, short.
- `description`: Capability + Trigger + Boundary, one sentence: "Use this for [capability] when [trigger] occurs; NOT for [boundary]." Reject any draft missing the Boundary clause — this is the single most common cause of activation failure.
- `paths`: glob list scoping exactly which files this skill may read or write (domain locking).
- `allowed-tools`: explicit least-privilege list.
- `variables`: every input the body references, declared as a mini API.

## Gate 3 — Iron Law and Red Flags

One non-negotiable sentence, phrased as "X, because Y" — never a bare MUST/NEVER, since bare imperatives break the moment the agent hits an edge case the author didn't anticipate.

Red Flags table, populated from Gate 1's three rationalization answers (typically 3-6 rows total once edge cases are added):

| Excuse the agent might generate | Why it's wrong | What to do instead |
|---|---|---|
| (from Gate 1 answer 1) | | |
| (from Gate 1 answer 2) | | |
| (from Gate 1 answer 3) | | |

## Gate 3.5 — Procedural core

- One-sentence purpose statement.
- Workflow table routing by user intent, not a single linear script.
- Every rule as "X because Y," never a bare imperative.
- If body exceeds ~500 lines, split into `workflows/*.md` and reference by relative path.
- Anything deterministic (formatting, calculations, scaffolding) goes in `scripts/`, not left for the model to eyeball.
- Documents/plans the skill produces default to HTML-first output for structure, but the skill's own SKILL.md instructions stay in plain prose — these are different artifacts with different rules.
- Apply appendix modules that earn their place: Domain Locking and Fact-vs-Guess labeling as strong defaults for any skill that edits code or data; Zero-Touch Verification and a Notes escape hatch as low-cost near-defaults; Five-Gate structure instead of a workflow table if the skill is investigative/diagnostic rather than constructive.

## Gate 4 — Adversarial Self-Critique

Run `scripts/lint.py <new-skill>/SKILL.md` and, if the skill has a `workflows/` or `scripts/` folder, `scripts/dependency_graph.py <new-skill>/` before writing the critique paragraph — a lint WARN or a broken/orphaned reference is a concrete finding, not something to rediscover by eyeballing. Check `memory/lessons.md` for any prior entry whose "Pattern" field says it generalizes across skills; if this draft repeats one, name it explicitly instead of re-discovering it from scratch.

Before presenting the draft, argue against it: name the single most likely way this skill misfires — over-triggering, under-triggering, or inconsistent output. State this to the user alongside the draft rather than silently patching it; the user may know something about their workflow that changes the right fix.

## Gate 5 — Blast Radius Analysis

Run `scripts/overlap_check.py` against the Gate 0 evidence table. Flag any pair where a plausible user request could reasonably match both descriptions. Where overlap exists, propose a narrower Boundary clause for one or both skills — don't leave it to be discovered in production.

## Gate 6 — Variance Analysis

Test against 2-3 varied prompts: one clear trigger case, one boundary/edge case, one clear non-trigger case. Report two separate findings:
- **Triggering accuracy** — fired when it should, silent when it shouldn't
- **Output consistency** — same input, stable structure across runs

Feed any drift found here back into tightening the description or workflow table, not a post-hoc patch.

## Output

Full SKILL.md, any workflows/scripts stubs, the Gate 4 critique paragraph, Gate 5 findings, Gate 6 results.

Use `create_file` to write the new SKILL.md and any `workflows/*.md` or `scripts/*` stub files — never paste them only into the chat response, since the user needs the actual files on disk. If a later gate requires revising a file already written in this same pass, use `str_replace` rather than recreating it from scratch.
