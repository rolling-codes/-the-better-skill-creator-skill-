# Frontmatter portability and current models

Read this before writing a skill's frontmatter, or when a skill over- or
undertriggers. Sources: the Claude Code skills docs (code.claude.com/docs/en/skills),
Anthropic's skill authoring best practices, and the Claude prompting best
practices page on platform.claude.com. Re-check those pages when a new model ships;
this file records what they said, not a guarantee they still say it.

## Contents
- Portable frontmatter
- allowed-tools is a grant
- Writing for current models
- Evaluating across models
- Official tooling that overlaps this skill

## Portable frontmatter

claude.ai uploads, the Skills API, and upstream `package_skill.py` accept only six
top-level keys: `name`, `description`, `license`, `compatibility`, `metadata`,
`allowed-tools`. Any other key is a hard error, not a warning. Claude Code accepts
more (`when_to_use`, `disable-model-invocation`, `context`, `model`, `effort`,
`paths`, `hooks`, and others) but silently ignores keys it doesn't recognize.

So: keep custom data under `metadata` (this toolkit stores `schemaVersion` there),
and use Claude Code-only keys only for skills that will never leave Claude Code.
`quick_validate.py` enforces the six-key rule; `python -m scripts.migrate_skill
<skill> --to <current version>` moves a legacy top-level `schemaVersion`.

## allowed-tools is a grant

`allowed-tools` pre-approves tools for the turn that invokes the skill; it does not
declare what the skill needs and does not restrict anything. Entries must be real
tool names: `Read`, `Grep`, `Glob`, `WebFetch`, `WebSearch`, `Bash(pattern *)`, or
`mcp__server__tool`. Anything else is ignored. `lint.py` flags names that don't
have that shape.

Because the field skips the permission prompt, scope it like any grant:

- Prefer `Bash(git log *)` over `Bash`. A broad pattern like `Bash(git tag *)` also
  allows creating tags, not just listing them.
- Leave writes to caller-supplied paths, destructive commands, network calls, and
  anything that spends model budget out of the list so they still prompt.
- Leaving the field out is fine. The scorer no longer penalizes its absence.

## Writing for current models

- Plain phrasing beats emphasis. Current models follow instructions closely, and
  "CRITICAL: you MUST use this when..." makes them overtrigger. Write "Use this
  when..." and explain why.
- Descriptions: third person, key use case first, specific trigger phrases, and
  named near misses. Do not make descriptions "pushy" to fight undertriggering;
  that advice predates current models.
- Don't stack verification. Some current models (Claude Opus 5 per the docs)
  verify their own work well unprompted, and extra "double-check everything"
  instructions add tokens and latency. Keep one real verification step, such as a
  validator script or this skill's review gate.
- Don't over-prescribe delegation. Current models spawn subagents readily; say
  when subagents are and aren't warranted instead of "use subagents for X".
- Don't ask for reasoning in visible `<thinking>` tags. On models with thinking
  always on, that request may be declined; rely on built-in thinking and effort.
- Prefilled assistant turns and `budget_tokens` return 400 errors on recent
  models. Scripts that call the API should use adaptive thinking and `effort`.
- Put the most important instructions near the top of SKILL.md. After context
  compaction, Claude Code keeps only the first 5,000 tokens of an invoked skill.

## Evaluating across models

What works for Opus may be too thin for Haiku. Run trigger evals on each model the
skill targets. Run this command from the repository root:

```bash
python bsc.py eval <skill> --live --models haiku,sonnet,opus
```

Each model gets its own result block in the report, and `--max-calls` counts calls
across all models. Compare per-model pass rates before calling a change an
improvement.

## Official tooling that overlaps this skill

- `claude plugin eval` runs prompts with and without a plugin in isolated sessions,
  scores them, and exits nonzero below a threshold, so it can gate CI. Use it for
  skills shipped in a plugin; its format is not interchangeable with
  `evals/evals.json`.
- `/claude-api prompt-audit` in Claude Code flags instructions written for older
  models in prompts, skills, and tool descriptions and proposes fixes as a diff.
  Run it on a skill after a model upgrade.
- `claude plugin validate <dir>` finds SKILL.md files whose frontmatter does not
  parse.
