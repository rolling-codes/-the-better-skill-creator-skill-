# Design Analysis

Read this before drafting or restructuring a skill. It is the reasoning stage that
keeps the skill-creator from turning a user's wording into a shallow instruction
file. The job is not to transcribe the request — it is to work out what the request
*is really for* and design for that whole problem space.

The literal prompt is almost always one facet of a larger outcome. "Find the crashes
in my logs" is not a request for a log grepper; it is a request for a working app,
which entails detecting, tracing, patching, and verifying. "Build me an RPG skill"
is not one skill — it is a family of very different skills. Your first move is to see
the space, not to start typing.

## The angles

Work these in order. Most take one or two sentences; the point is that none of them
is skipped. Write your conclusions into `spec.yaml` (see the field list below) so the
reasoning is durable and the confidence check can see it.

1. **Real goal / outcome.** Restate what the user is actually trying to achieve, in
   outcome terms, not verb terms. What does "done" look like from their side? If your
   restatement is just their sentence reworded, you have not found the outcome yet.

2. **Valid interpretations.** List the genuinely different readings of the request. A
   request names a category; categories have members that would produce substantially
   different skills. Name them explicitly so you can choose rather than defaulting.

3. **Modes / categories / use-cases.** Within the chosen interpretation, what distinct
   modes must the skill support? (e.g. batch vs interactive, first-run vs update,
   single-file vs whole-project.) Missing a mode is how a skill works in the demo and
   fails in use.

4. **Cross-cutting requirements.** Sweep the dimensions that requests rarely state but
   usually imply: **technical** (performance, data size, environment), **functional**
   (what it must actually do end to end), **creative** (tone, format, style where it
   matters), **accessibility** (headless/no-browser, screen-reader, plain-language),
   **UX** (how a human drives it, what feedback they get). Keep the ones that are real
   for this skill; drop the ones that aren't.

5. **Entailments — tools, files, references, workflows, dependencies.** From the
   outcome, derive what actually has to exist to deliver it: which scripts, which
   reference docs, which MCPs/tools, which ordered workflow steps. This is where
   "generate code" becomes "inspect logs → diagnose → detect syntax errors → trace
   root cause → patch → run tests → verify."

6. **Failure points.** Name the likely errors, edge cases, limitations, and ways the
   skill will misfire. Each one is either something to guard in the workflow or
   something to cover with a test. A design with no named failure points is untested
   thinking.

7. **Self-validation.** Decide how the skill will test, validate, and improve its own
   output — not how *you* test the skill (that's the eval loop), but what the produced
   skill does to check its own work before returning it.

8. **Infer vs. clarify.** Separate what you can safely infer from what genuinely needs
   the user. Default to inferring. See the ask-vs-assume rule below.

9. **Flexibility without vagueness.** Make the skill general enough to handle the real
   space, but no broader. Breadth is not the same as a loose description — a skill that
   supports several modes still needs a tight Boundary clause (Gate 2) and must survive
   the overlap check (Gate 5). "Handles anything" is a design smell, not a feature.

## Compare, decide, architect

Analysis is not a wish list. After enumerating the angles:

- **Compare** the interpretations and modes against the user's real goal.
- **Decide** which are in scope for *this* skill and which are explicitly out. Record
  the out-of-scope calls too — they become the Boundary clause.
- **Architect** from that decision: the chosen modes determine which `references/`
  variants you create (see "Domain organization" in SKILL.md), which `scripts/` the
  skill bundles, and the shape of the main workflow. The design drives the file layout,
  not the reverse.

## Ask vs. assume

Ask a focused question **only when two interpretations would produce substantially
different skills and you cannot choose safely from context.** In that case ask one
sharp question about the deciding axis — not a battery of questions.

Otherwise, make the call and **state the assumption** in `spec.yaml` (`assumptions`)
and to the user, so it is visible and correctable. A stated assumption the user can
veto beats an interview that makes them do the design work. This is the deliberate
inversion of a question-first interview: analyze first, assume by default, ask only on
the decisive fork.

## Worked example — a development skill

Prompt: *"Make a skill that builds a responsive app and watches my logs."*

- **Outcome:** a working, responsive app whose failures the skill can find and fix —
  not a UI generator.
- **Interpretations:** (a) scaffold-only generator; (b) build + observe + self-heal.
  These are very different skills; the word "watches" points hard at (b).
- **Modes:** initial build vs. iterating on an existing app; local vs. CI logs.
- **Entailments:** generate UI → **inspect logs → detect syntax errors → diagnose
  crashes → trace root cause → patch → run tests → verify the app still works.** The
  literal "build" is one step of eight.
- **Failure points:** logs absent/rotated; crash with no stack trace; a "fix" that
  breaks another path (needs a regression test); ambiguous root cause.
- **Self-validation:** the skill re-runs tests and re-checks the logs after patching
  before declaring success.
- **Decision:** build interpretation (b), both modes, bundle a log-parse + test-run
  step. **Assumption stated:** "I'm treating this as build-and-self-heal, not
  scaffold-only, because you said 'watches my logs.'"

## Worked example — an RPG skill

Prompt: *"Build me an RPG skill."*

- **Interpretations / axes:** flat narrative adventure · dynamic simulation ·
  persistent multi-session campaign · character progression · employment/military
  **ranks** and careers · branching consequences · world-state tracking · resolution
  system (dice/stat-check vs. freeform vs. deterministic).
- **Why it matters:** a flat narrative skill and a persistent-campaign-with-world-state
  skill share almost no structure — different files, different workflow, different
  state handling. Defaulting to "flat" silently discards most of the request.
- **Compare / decide:** if context signals persistence or progression, scope for
  state + resolution; if it reads as one-shot storytelling, scope flat and say so.
- **Ask only if decisive:** "Should this remember state across sessions, or run
  self-contained each time?" — because that one axis reshapes the whole skill. If the
  user's earlier messages already answer it, don't ask; state the assumption.

## What lands in `spec.yaml`

The design analysis is captured in these `SkillSpec` fields (see `scripts/spec.py`),
so it persists and `scripts/confidence.py` can flag a flat or unresolved design:

- `outcome` — the real end-state, in outcome terms.
- `interpretations` — the distinct readings considered; mark the chosen one.
- `modes` — the modes/categories/use-cases the skill will support.
- `entailments` — the implied tasks, tools, files, and workflow steps required.
- `failure_points` — the errors, edge cases, and limits to guard or test.
- `validation` — how the produced skill checks its own output.
- `assumptions` — what you inferred and are proceeding on.
- `open_questions` — the decisive forks you still need the user to settle (ideally empty).
