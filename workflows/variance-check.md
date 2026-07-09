# Variance-Check Mode — Gate 6 in isolation

Use when `target_skill` already exists and the only open question is whether it triggers and outputs reliably.

## Test prompt matrix

Build 2-3 prompts minimum (5-10 for a thorough pass) covering:

1. **Clear trigger case** — an unambiguous request the skill should fire on.
2. **Boundary/edge case** — a request that sits right at the stated Boundary clause; correct behavior is usually to NOT fire, or to fire and explicitly note the boundary.
3. **Clear non-trigger case** — an unrelated request; the skill must stay silent.

For each prompt, run it (or simulate the routing decision if execution isn't available) and record:

- Did the skill activate? (yes/no)
- Was that the correct call given the description's Trigger/Boundary clauses?
- If it activated, was the output structure consistent with a prior run of the same prompt type?

## Reporting

Two separate findings, not a single pass/fail:

- **Triggering accuracy**: N/total correct activations, with the specific prompt(s) that misfired and why (over-trigger vs under-trigger).
- **Output consistency**: whether structure (headers, sections, format) held stable across repeated runs of the trigger case.

Any drift goes back into the description or workflow table as a Gate-5-style fix, not a one-off patch to that single output.
