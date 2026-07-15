# skill-creator — Environment Adaptations

The core workflow (draft → test → review → improve → repeat) is the same
everywhere. What changes per environment is the mechanics: subagents,
browsers, and the `claude` CLI are not universally available. Read the
section for the environment you're in.

## Claude.ai

**Running test cases**: No subagents means no parallel execution. For each
test case, read the skill's SKILL.md, then follow its instructions to
accomplish the test prompt yourself. Do them one at a time. This is less
rigorous than independent subagents (you wrote the skill and you're also
running it, so you have full context), but it's a useful sanity check — and
the human review step compensates. Skip the baseline runs — just use the
skill to complete the task as requested.

**Reviewing results**: If you can't open a browser (e.g., Claude.ai's VM has
no display, or you're on a remote server), skip the browser reviewer
entirely. Instead, present results directly in the conversation. For each
test case, show the prompt and the output. If the output is a file the user
needs to see (like a .docx or .xlsx), save it to the filesystem and tell
them where it is so they can download and inspect it. Ask for feedback
inline: "How does this look? Anything you'd change?"

**Benchmarking**: Skip the quantitative benchmarking — it relies on baseline
comparisons which aren't meaningful without subagents. Focus on qualitative
feedback from the user.

**The iteration loop**: Same as everywhere — improve the skill, rerun the
test cases, ask for feedback — just without the browser reviewer in the
middle. You can still organize results into iteration directories on the
filesystem if you have one.

**Description optimization**: This section requires the `claude` CLI tool
(specifically `claude -p`) which is only available in Claude Code. Skip it
if you're on Claude.ai.

**Blind comparison**: Requires subagents. Skip it.

**Packaging**: The `package_skill.py` script works anywhere with Python and
a filesystem. On Claude.ai, you can run it and the user can download the
resulting `.skill` file.

**Updating an existing skill**: The user might be asking you to update an
existing skill, not create a new one. See "Updating an existing skill"
below — it applies to every environment.

## Cowork

You have subagents, so the main workflow (spawn test cases in parallel, run
baselines, grade, etc.) all works. If you run into severe problems with
timeouts, it's OK to run the test prompts in series rather than parallel.

After the test runs complete, follow this sequence in order. Step 1 exists
because the human's read on the raw outputs is the most valuable signal in
the whole loop, and it goes stale the moment you start revising — so it has
to reach them before you touch the skill:

1. **Generate the eval viewer first, before doing any of your own
   evaluation or revision.** Use `generate_review.py` (not hand-written
   HTML). You have no browser or display, so pass `--static <output_path>`
   to write a standalone HTML file instead of starting a server, then
   proffer a link the user can click to open it.
2. **Collect feedback from the downloaded file.** With no running server,
   the viewer's "Submit All Reviews" button downloads `feedback.json`. Read
   it from there (you may have to request access first), then copy it into
   the workspace directory so the next iteration picks it up.
3. **Only then revise the skill** based on what the human flagged.

Other Cowork notes:

- Packaging works — `package_skill.py` just needs Python and a filesystem.
- Description optimization (`run_loop.py` / `run_eval.py`) works in Cowork
  since it uses `claude -p` via subprocess, not a browser — but save it
  until the skill is fully finished and the user agrees it's in good shape.
- Add "Create evals JSON and run `eval-viewer/generate_review.py` so human
  can review test cases" to your TodoList so step 1 above doesn't get lost.

## Updating an existing skill (all environments)

The user might be asking you to update an existing skill, not create a new
one. In this case:

- **Preserve the original name.** Note the skill's directory name and
  `name` frontmatter field — use them unchanged. E.g., if the installed
  skill is `research-helper`, output `research-helper.skill` (not
  `research-helper-v2`).
- **Copy to a writeable location before editing.** The installed skill path
  may be read-only. Copy to `/tmp/skill-name/`, edit there, and package
  from the copy.
- **If packaging manually, stage in `/tmp/` first**, then copy to the
  output directory — direct writes may fail due to permissions.
