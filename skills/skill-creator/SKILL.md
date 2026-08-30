---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill
  performance. Use when users want to create a skill from scratch, edit, or optimize
  an existing skill, run evals to test a skill, benchmark skill performance with variance
  analysis, or optimize a skill's description for better triggering accuracy. Not
  for tasks outside this skill's scope.
schemaVersion: 1
allowed-tools:
- filesystem.read
- filesystem.write
- filesystem.zip
- terminal.execute
---

# Skill Creator

A skill for creating new skills and iteratively improving them.

At a high level: decide what the skill should do and roughly how, write a draft, create a few test prompts and run claude-with-access-to-the-skill on them, and help the user evaluate qualitatively and quantitatively — while the runs happen, draft quantitative evals if there aren't any and explain them, and use `eval-viewer/generate_review.py` to show results and metrics. Then rewrite from the user's feedback (and any glaring benchmark flaws), repeat until satisfied, and expand the test set to try at larger scale.

Your job is to figure out where the user is in this process and jump in — narrow down a vague "I want a skill for X", write the draft and test cases, run the prompts, and iterate; if they already have a draft, go straight to the eval/iterate loop. Stay flexible (if they say "just vibe with me", do that), and after the skill is done you can run the description improver — a separate script — to optimize triggering.

## Communicating with the user

Users range from non-coders to experienced engineers. Read context cues and match your
phrasing: "evaluation" and "benchmark" are usually fine; only use "JSON" or "assertion"
unexplained when the user clearly knows them. When in doubt, briefly define a term.

---

## The iron law, and the red flags around it

**Iron law: never tell the user a skill is better without a baseline run from the same iteration, because with-skill output that looks good on its own tells you nothing about whether the skill caused it.** A model reading its own polished output will conclude the skill worked, every time. The baseline is the only thing that separates a real improvement from Claude being competent anyway.

Most of the ways this loop fails are not misunderstandings, they are plausible-sounding shortcuts taken under time pressure. If you catch yourself thinking one of the things on the left, the thing on the right is what the situation actually calls for.

| Rationalization | What to do instead |
|---|---|
| "The baseline is obviously going to be worse, I can skip it." | Spawn with-skill and baseline in the same turn. If the baseline wins, that is the single most useful result you can get. |
| "I'll collect the timing numbers once everything finishes." | `total_tokens` and `duration_ms` arrive only in the task notification. Write `timing.json` as each run completes or the data is gone. |
| "I'll just summarize the results for the user, the viewer is a detour." | Run `eval-viewer/generate_review.py`. Your summary is filtered through your own judgment of your own work, which is exactly what the review step exists to check. |
| "This assertion is a bit subjective but a number is better than nothing." | Drop it and evaluate that dimension qualitatively. An assertion that passes for both configurations measures nothing and inflates the pass rate. |
| "The fix worked on eval-2, that is enough." | Two or three examples cannot show generalization. Ask what the fix does on a prompt you have not tried. |
| "There is a testing skill available, I'll use that instead." | Use this loop. `/skill-test` and similar do not produce the baseline pairing or the workspace layout the viewer and aggregation scripts expect. |
| "The score is 68, close enough to 70." | Fix it first. The threshold exists because the gap between 68 and 70 is usually one unwired reference or one missing test file, which is cheap now and expensive later. |
| "The user literally asked for X, so I'll build X." | The literal request is usually one facet of the outcome. Work the angles in `references/design-analysis.md`, build for the problem space, and state the assumptions you made — breadth still needs a tight Boundary (Gate 2), not vagueness. |
| "Completing this entails patching/deploying, so I'll do it." | Entailment is not authorization. Discovering that work is needed doesn't permit it — classify it required-but-unauthorized and ask, and never fold a permissioned or destructive action into the build silently. |
| "The files exist and validation passed, so the skill is complete." | Passing scripts and polished output are not completeness. For a complex skill, run `agents/completion-adversary.md` on the finished result with fresh context and let it try to prove the skill incomplete; only `completion_gate_status: passed` counts as done. |
| "A reviewer suggested this feature, so I'll add it." | A subagent recommendation is not authorization. Run it through the same required/authorized classification — recommendations can be declined, and they never justify expanding scope or performing an external mutation. |

---

## Creating a skill

### Design analysis: scope the outcome from multiple angles

Don't convert the user's wording into an instruction file. The literal prompt is
usually one facet of a larger outcome — "find the crashes in my logs" is really "keep
my app working," which entails detect → diagnose → patch → verify. Before drafting,
design for the whole problem space, not the sentence.

If the conversation already contains the workflow the user wants to capture (e.g.
"turn this into a skill"), mine it first — the tools used, the step sequence,
corrections the user made, input/output formats observed — then analyze.

Use **adaptive lenses**, not a fixed checklist — read `references/design-analysis.md`
for the full doctrine. Always evaluate the core: the real **outcome**; the material
**interpretations** (and which you chose); the necessary **entailments** (tools, files,
references, workflow steps the outcome needs); **boundaries & authorization**; and
**validation**. Reach for other lenses — accessibility, security, performance,
persistence, creative direction, integration, multi-user, error recovery — only when
the request makes them relevant, and say why. An unused lens is focus, not omission;
filling every field mechanically is how scoping turns into scope creep. Record the
conclusions as a design brief in `spec.yaml`.

**Entailment is not permission.** Recognizing that the outcome entails patching,
deleting, or deploying does not authorize those actions. Classify each piece of
discovered work as required-and-authorized (do it), required-but-unauthorized (identify
and ask), optional (recommend, never add silently), or out-of-scope (exclude) — and
record it in `authorization_boundaries`. Bake the same discipline into any produced
skill that takes destructive or outward-facing actions.

Then **compare, decide, architect**: score surviving interpretations (goal fit,
evidence, complexity, reversibility, risk, clarification need), choose, record what is
out (it becomes the Boundary clause), and let that shape the file layout. When
requirements conflict, **explicit user constraints win** — record the compromise.

**Analyze first, ask only on the decisive fork**, and *state* assumptions when intent
is safe to infer. Ask one sharp question only when a material interpretation would
produce a substantially different skill and the matrix can't settle it (low
reversibility or real risk with thin evidence). **Stop** once the outcome, resolved
interpretations, entailments, authorization, and testability are settled — if another
lens wouldn't change what you build, you're done. Breadth still needs a tight Boundary
(Gate 2), not vagueness.

From that analysis you can answer the four things a draft needs — what the skill
enables Claude to do, when it should trigger (what phrases/contexts), its expected
output format, and whether it needs test cases (skills with objectively verifiable
outputs benefit; subjective ones like writing style or art often don't — suggest a
default, let the user decide). Check available MCPs and research in parallel via
subagents where useful, so you arrive with context instead of making the user fill
gaps.

### Independent review & adversarial completion (complex skills)

You don't get to decide by yourself that a complex skill is done — a model reading its
own output always concludes it worked. For a substantial new skill or change (new
architecture/scope, multiple modes, external/permissioned/destructive actions,
materially different interpretations, or when you're about to call it complete), run the
process in `references/independent-review.md` and record why you activated or skipped it.
Before drafting, spawn `agents/outcome-analyst.md`, `agents/scope-adversary.md`, and
`agents/architecture-reviewer.md` in one turn with fresh context — give them the request,
files, constraints, and evidence, **never** your proposed solution — then synthesise
**without majority voting** (resolve by evidence: request > conversation > source >
constraints > tests). Before declaring completion, spawn a fresh
`agents/completion-adversary.md` with the finished skill, the decision, and the test
results but **not** the implementation history, and let it try to prove the skill
incomplete; fix, document as a limitation, or return each material finding, and re-run
after fixes. `review.yaml` records it and `scripts/review_gate.py` enforces it; a
subagent recommendation does not authorize expanding scope or an external mutation.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: Skill identifier
- **description**: When to trigger, what it does. This is the primary triggering mechanism - include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Note: currently Claude has a tendency to "undertrigger" skills -- to not use them when they'd be useful. To combat this, please make the skill descriptions a little bit "pushy". So for instance, instead of "How to build a simple fast dashboard to display internal Anthropic data.", you might write "How to build a simple fast dashboard to display internal Anthropic data. Make sure to use this skill whenever the user mentions dashboards, data visualization, internal metrics, or wants to display any kind of company data, even if they don't explicitly ask for a 'dashboard.'"
- **compatibility**: Required tools, dependencies (optional, rarely needed)
- **the rest of the skill :)**

### Skill Writing Guide

#### Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

**Scaffolding a skeleton:** rather than hand-building this layout, generate it with the archetype generators, which pre-fill sensible tools and stub files so you start from a working shell instead of a blank file:
```bash
python -m generators --list                                       # default, python-skill, research
python -m generators --archetype python-skill --name my-skill --output ./skills/
```
Add a new archetype by subclassing the `Generator` base in `generators/base.py`.

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) - Always in context (~100 words)
2. **SKILL.md body** - In context whenever skill triggers (<500 lines ideal)
3. **Bundled resources** - As needed (unlimited, scripts can execute without loading)

These word counts are approximate and you can feel free to go longer if needed.

**Key patterns:**
- Keep SKILL.md under 500 lines; if you're approaching this limit, add an additional layer of hierarchy along with clear pointers about where the model using the skill should go next to follow up.
- Reference files clearly from SKILL.md with guidance on when to read them
- For large reference files (>300 lines), include a table of contents

**Domain organization**: When a skill supports multiple domains/frameworks, organize by variant:
```
cloud-deploy/
├── SKILL.md (workflow + selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```
Claude reads only the relevant reference file.

#### Principle of Lack of Surprise

This goes without saying, but skills must not contain malware, exploit code, or any content that could compromise system security. A skill's contents should not surprise the user in their intent if described. Don't go along with requests to create misleading skills or skills designed to facilitate unauthorized access, data exfiltration, or other malicious activities. Things like a "roleplay as an XYZ" are OK though.

#### Writing Patterns

Prefer using the imperative form in instructions.

**Defining output formats** - You can do it like this:
```markdown
## Report structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Examples pattern** - It's useful to include examples. You can format them like this (but if "Input" and "Output" are in the examples you might want to deviate a little):
```markdown
## Commit message format
**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Writing Style

Try to explain to the model why things are important in lieu of heavy-handed musty MUSTs. Use theory of mind and try to make the skill general and not super-narrow to specific examples. Start by writing a draft and then look at it with fresh eyes and improve it.

### Validation Pipeline

After drafting, run the compiler pipeline before iterating with the user:

```bash
cd skills/skill-creator
python -m scripts.confidence <skill-path>          # coverage + ambiguity
python -m scripts.semantic_analysis <skill-path>   # contradictions, duplicates
python -m scripts.lint <skill-path>                # content quality + reference-wiring completeness
python -m scripts.static_analysis <skill-path>     # wiring: dead refs, orphaned files, unused tools
python -m scripts.repair <skill-path>              # auto-fix known errors
python -m scripts.score <skill-path>               # quality rubric (7 dimensions)
```

Or it all runs automatically as part of `package_skill.py`. Fix any score below 70
before sharing the skill with the user.

To generate structured edge-case and environment test scenarios:
```bash
python -m scripts.generate_tests <skill-path>      # writes to tests/generated/
```

### Test Cases

After writing the skill draft, come up with 2-3 realistic test prompts — the kind of thing a real user would actually say. Share them with the user: [you don't have to use this exact language] "Here are a few test cases I'd like to try. Do these look right, or do you want to add more?" Then run them.

Save test cases to `evals/evals.json`. Don't write assertions yet — just the prompts. You'll draft assertions in the next step while the runs are in progress.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": []
    }
  ]
}
```

See `references/schemas.md` for the full schema (including the `assertions` field, which you'll add later).

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through. Do NOT use `/skill-test` or any other testing skill.

Put results in `<skill-name>-workspace/` as a sibling to the skill directory. Within the workspace, organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.). Don't create all of this upfront — just create directories as you go.

### Step 1: Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't spawn the with-skill runs first and then come back for baselines later. Launch everything at once so it all finishes around the same time.

**With-skill run:**

```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about — e.g., "the .docx file", "the final CSV">
```

**Baseline run** (same prompt, but the baseline depends on context):
- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing — not just "eval-0". Use this name for the directory too. If this iteration uses new or modified eval prompts, create these files for each new eval directory — don't assume they carry over from previous iterations.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### Step 2: While runs are in progress, draft assertions

Don't just wait for the runs to finish — you can use this time productively. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names — they should read clearly in the benchmark viewer so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see in the viewer — both the qualitative outputs and the quantitative benchmark.

### Step 3: As runs complete, capture timing data

When each subagent task completes, you receive a notification containing `total_tokens` and `duration_ms`. Save this data immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — it comes through the task notification and isn't persisted elsewhere. Process each notification as it arrives rather than trying to batch them.

### Step 4: Grade, aggregate, and launch the viewer

Once all runs are done:

1. **Grade each run** — spawn a grader subagent (or grade inline) that reads `agents/grader.md` and evaluates each assertion against the outputs. Save results to `grading.json` in each run directory. The grading.json expectations array must use the fields `text`, `passed`, and `evidence` (not `name`/`met`/`details` or other variants) — the viewer depends on these exact field names. For assertions that can be checked programmatically, write and run a script rather than eyeballing it — scripts are faster, more reliable, and can be reused across iterations.

2. **Aggregate into benchmark** — run the aggregation script from the skill-creator directory:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <name>
   ```
   This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. If generating benchmark.json manually, see `references/schemas.md` for the exact schema the viewer expects.
Put each with_skill version before its baseline counterpart.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. See `agents/analyzer.md` (the "Analyzing Benchmark Results" section) for what to look for — things like assertions that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs.

4. **Launch the viewer** with both qualitative outputs and quantitative data:
   ```bash
   nohup python <skill-creator-path>/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "my-skill" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, also pass `--previous-workspace <workspace>/iteration-<N-1>`.

   **Cowork / headless environments:** If `webbrowser.open()` is not available or the environment has no display, use `--static <output_path>` to write a standalone HTML file instead of starting a server. Feedback will be downloaded as a `feedback.json` file when the user clicks "Submit All Reviews". After download, copy `feedback.json` into the workspace directory for the next iteration to pick up.

Note: please use generate_review.py to create the viewer; there's no need to write custom HTML.

5. **Tell the user** something like: "I've opened the results in your browser. There are two tabs — 'Outputs' lets you click through each test case and leave feedback, 'Benchmark' shows the quantitative comparison. When you're done, come back here and let me know."

### What the user sees in the viewer

The "Outputs" tab shows one test case at a time — prompt, output (rendered inline where
possible), previous output and previous feedback on iteration 2+, formal grades if
grading ran, and an auto-saving feedback box. The "Benchmark" tab shows pass rates,
timing, and token usage per configuration with per-eval breakdowns and analyst
observations. Navigation is prev/next or arrow keys; "Submit All Reviews" writes
`feedback.json`.

### Step 5: Read the feedback

When the user tells you they're done, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

Kill the viewer server when you're done with it:

```bash
kill $VIEWER_PID 2>/dev/null
```

---

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### How to think about improvements

1. **Generalize from the feedback.** A skill is meant to run across countless prompts, but you and the user are iterating on only a few examples because it's fast. If the skill works only for those examples it's useless — so avoid fiddly overfitting and constrictive MUSTs; for a stubborn issue, try a different metaphor or pattern of working. It's cheap to try.

2. **Keep the prompt lean.** Remove what isn't pulling its weight. Read the transcripts, not just the outputs — if the skill is making the model waste time, cut the part causing that and see what happens.

3. **Explain the why.** Explain the reasoning behind everything you ask the model to do — today's LLMs have good theory of mind and go beyond rote instructions when given a good harness. Understand what the user actually needs behind terse or frustrated feedback and transmit that into the instructions. All-caps ALWAYS/NEVER and rigid structures are a yellow flag; reframe as reasoning instead.

4. **Look for repeated work across test cases.** If all the test runs independently wrote a similar helper (a `create_docx.py`, a `build_chart.py`), that's a signal to bundle it: write it once in `scripts/` and tell the skill to use it, so future invocations don't reinvent it.

Your thinking time is not the blocker here, so take your time. Write a draft revision, then look at it again with fresh eyes and improve it, working from what the user actually needs rather than what they literally typed.

### The iteration loop

After improving the skill:

1. Apply your improvements to the skill
2. Rerun all test cases into a new `iteration-<N+1>/` directory, including baseline runs. If you're creating a new skill, the baseline is always `without_skill` (no skill) — that stays the same across iterations. If you're improving an existing skill, use your judgment on what makes sense as the baseline: the original version the user came in with, or the previous iteration.
3. Launch the reviewer with `--previous-workspace` pointing at the previous iteration
4. Wait for the user to review and tell you they're done
5. Read the new feedback, improve again, repeat

Keep going until:
- The user says they're happy
- The feedback is all empty (everything looks good)
- You're not making meaningful progress

---

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. Read `agents/comparator.md` and `agents/analyzer.md` for the details. The basic idea is: give two outputs to an independent agent without telling it which is which, and let it judge quality. Then analyze why the winner won.

This is optional, requires subagents, and most users won't need it. The human review loop is usually sufficient.

---

## Description Optimization

The `description` field decides whether Claude invokes the skill at all, so
after creating or improving a skill, offer to optimize it for triggering
accuracy. There is a full automated loop for this (generate trigger evals,
review them with the user, run `scripts/run_loop.py` — or `scripts/improve_description.py`
for a one-off rewrite — apply the winning description). Read
`references/description-optimization.md` before starting it.

---

### Package and Present (only if `present_files` tool is available)

Check whether you have access to the `present_files` tool. If you don't, skip this step. If you do, package the skill and present the .skill file to the user:

```bash
python -m scripts.package_skill <path/to/skill-folder>
```

`package_skill.py` uses the `filesystem.zip` tool to write the archive. After
packaging, direct the user to the resulting `.skill` file path so they can install it.

---

## Environment adaptations (Claude.ai, Cowork)

The core loop is the same everywhere, but Claude.ai has no subagents and Cowork has no browser, so several mechanics change (how test cases run, how the viewer is delivered, whether description optimization is possible). If you are in Claude.ai or Cowork, read `references/environments.md` before running test cases — it also covers updating an existing installed skill, which applies in every environment.

---

## Reference files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another
- `agents/outcome-analyst.md` — Independent pre-draft: the real outcome, interpretations, and what "complete" means
- `agents/scope-adversary.md` — Independent pre-draft: attacks the scope for under- and over-scoping
- `agents/architecture-reviewer.md` — Independent pre-draft: whether the architecture can deliver the outcome
- `agents/completion-adversary.md` — The pre-completion gate: tries to prove the finished skill incomplete

The references/ directory has additional documentation:
- `references/design-analysis.md` — the multi-angle scoping doctrine: read it at the start of creating or restructuring a skill, before drafting, to scope the outcome instead of the literal wording.
- `references/independent-review.md` — the independent multi-agent review + adversarial completion gate: read it for a substantial new skill or change, before spawning the review subagents.
- `references/schemas.md` — JSON structures for evals.json, grading.json, etc.
- `references/environments.md` — Claude.ai and Cowork adaptations, plus how to update an existing installed skill. Read before running test cases outside Claude Code.
- `references/description-optimization.md` — the full trigger-eval and description-tuning loop. Read before optimizing a skill's description.
- `references/trigger-confidence.md` — How the per-query trigger_rate from run_eval.py works and how to read it. Read when interpreting flaky trigger results.
- `references/dependency-graph.md` — Hand-maintained map of which scripts and agents depend on which. Read before refactoring or removing a script.

Compiler pipeline scripts (for building and quality-gating skills):
- `scripts/spec.py` — pre-generation SkillSpec intent IR; writes spec.yaml before files are created
- `scripts/confidence.py` — requirement coverage + ambiguity score for a skill or spec
- `scripts/semantic_analysis.py` — content-semantic checks: contradictions, duplicate sections, inconsistent terminology
- `scripts/lint.py` — content-quality lint: description trigger/boundary clauses, token budget, and reference-wiring completeness (every skill.yaml dependency is linked from SKILL.md); also runs via `scripts/hooks/pre-commit`
- `scripts/static_analysis.py` — wiring checks: dead references, orphaned files (on disk or declared but never referenced here), unused tools, unreachable sections, recursive self-calls
- `scripts/dependency_graph.py` — optional. Build and inspect the dependency graph (cycle detection, missing-node audit, impact analysis); `--format json|dot|summary`. The workflow and packaging pipeline do not depend on it or on any external graph tooling — reach for it only when you want to inspect a skill's structure by hand.
- `scripts/review.py` — `ReviewRecord` IR for the independent-review process; reads/writes `review.yaml` (findings, completion-adversary report, dispositions, completion-gate status).
- `scripts/review_gate.py` — deterministic gate over `review.yaml`: fails on missing reports, undisposed high-severity findings, unresolved decisive questions, missing completion-adversary reports, unwired review agents, or a completion claim before `completion_gate_status: passed`. Runs in the package pipeline via `ReviewStage`.
- `scripts/repair.py` — auto-fix known lint and analysis errors before they block packaging
- `scripts/score.py` — architecture scoring rubric across 7 dimensions (0–100 each)
- `scripts/generate_tests.py` — generate edge-case, malformed-input, and environment test scenarios
- `scripts/generate_report.py` — render aggregated `benchmark.json` into human-readable markdown
- `generators/` — archetype scaffolding for new skills; `generators/default.py`, `generators/python_skill.py`, and `generators/research_skill.py` implement the `default`, `python-skill`, and `research` archetypes (see the "Scaffolding a skeleton" note under Anatomy of a Skill). Extend via the `Generator` base in `generators/base.py`

Compiler pipeline architecture (v1.3.0):
- `scripts/compiler_context.py` — shared IR (`CompilerContext`, `RepairProposal`) passed through all stages
- `scripts/pipeline.py` — `PipelineStage` Protocol + `StageRegistry`; call `run_all(ctx)` to execute the full pipeline
- `scripts/stages/` — seven concrete stage wrappers: `LintStage`, `SemanticStage`, `DependencyStage`, `RepairStage`, `ApplyRepairsStage`, `ScoreStage`, `PackageStage`

Governance and maintenance files (for working on this skill itself):
- `LIFECYCLE.md` — lifecycle states; the canonical status lives in `skill.yaml`.
- `PERMISSIONS.md` — per-script risk breakdown behind the frontmatter `allowed-tools` list. Read before adding a script that writes files or shells out.
- `scripts/skill_test.py` — runs the tests/ regression suite through run_eval.py; with `--grade-transcript <path>` it also grades `tests/expected_behavior.yaml` via the grader agent.
- `scripts/validate_all.sh` — runs quick_validate.py plus the regression suite in one shot; run it before packaging or committing changes to this skill.
- `scripts/migrate_skill.py` + `scripts/migrations/` — upgrade a skill across `schemaVersion` bumps (`--to <n> [--dry-run]`); `v1_to_v2.py` is the migration template.

---

Please add these steps to your TodoList if you have one, so the eval viewer step doesn't get skipped.
