#!/usr/bin/env python3
"""
lint.py — semantic linter for SKILL.md files.

Not syntax checking (the YAML frontmatter either parses or it doesn't) —
this checks the things that make a skill fragile in practice, per the
Iron Law / Red Flags criteria in skill-architect's own SKILL.md.

Every check here is a heuristic, not a proof. A skill can pass every
check and still misfire, and can fail a check for a legitimate reason
the author consciously chose. Warnings are prompts for a human or an
audit pass to look closer, not automatic rejections — same posture as
overlap_check.py.

Usage:
    python lint.py <path-to-SKILL.md>
    python lint.py <skills_root> --recursive

Exits 0 always; prints WARN/INFO lines. Use --strict to exit 1 if any
WARN fires, for wiring into a CI-style pre-publish check.
"""
import re
import sys
import argparse
from pathlib import Path


def read_frontmatter(text: str):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm_text, body = m.group(1), m.group(2)
    fields = {}
    # naive line-based parse — good enough for the flat fields we care about
    current_key = None
    for line in fm_text.splitlines():
        if re.match(r"^[a-zA-Z_][\w-]*:", line):
            key, _, rest = line.partition(":")
            current_key = key.strip()
            fields[current_key] = rest.strip()
        elif current_key and line.strip().startswith("-"):
            fields[current_key] = fields.get(current_key, "") + " " + line.strip().lstrip("- ")
        elif current_key and line.strip():
            fields[current_key] += " " + line.strip()
    return fields, body


def check_description(fields: dict, warnings: list):
    desc = fields.get("description", "")
    if not desc:
        warnings.append(("ERROR", "No description field — skill cannot trigger at all."))
        return

    has_boundary = bool(re.search(r"\bnot for\b", desc, re.IGNORECASE))
    if not has_boundary:
        warnings.append((
            "WARN",
            "Description has no boundary clause (no 'NOT for ...'). "
            "This is the single most common cause of activation failure — "
            "add an explicit boundary even if it feels redundant."
        ))

    has_trigger = bool(re.search(r"\bwhen\b|\bif\b", desc, re.IGNORECASE))
    if not has_trigger:
        warnings.append((
            "WARN",
            "Description has no explicit trigger clause ('when ...' / 'if ...'). "
            "A purely topical description ('helps with X') under-fires or "
            "mis-fires because Claude has nothing concrete to match against."
        ))

    # crude broadness check: trigger clause reduced to content words.
    # Quoted spans are concrete example phrases — the opposite of vague —
    # so strip them before scanning, otherwise a trigger containing
    # '"help me commit"' trips the vague-term check on the word "help".
    trig_match = re.search(r"\bwhen\b(.+?)(;|\.|$)", desc, re.IGNORECASE)
    if trig_match:
        trig_prose = re.sub(r"[\"“”‘’'].*?[\"“”‘’']", " ", trig_match.group(1))
        trig_words = [w for w in re.findall(r"[a-zA-Z]+", trig_prose) if len(w) > 2]
        vague_terms = {"any", "general", "various", "different", "stuff", "things", "help", "helps"}
        if len(trig_words) <= 3 or any(w.lower() in vague_terms for w in trig_words):
            warnings.append((
                "WARN",
                f"Trigger clause reads as broad or vague: 'when{trig_match.group(1)}'. "
                "A vague trigger matches too many plausible requests, which is exactly "
                "what causes cross-skill collisions in Blast Radius terms."
            ))

    word_count = len(desc.split())
    if word_count > 60:
        warnings.append((
            "INFO",
            f"Description is {word_count} words — on the long side. The description "
            "is the entire triggering surface but it still has to be scannable; "
            "consider trimming to the essential Capability/Trigger/Boundary clauses."
        ))


def check_variables(fields: dict, body: str, warnings: list):
    var_field = fields.get("variables", "")
    if not var_field:
        return
    # variable names are the tokens right before a colon in the flattened variables field
    names = re.findall(r"(\w+)\s*:", var_field)
    for name in names:
        # look for the variable referenced in the body (bare, backticked, or braced)
        pattern = rf"[`{{]{re.escape(name)}[`}}]|\b{re.escape(name)}\b"
        occurrences = len(re.findall(pattern, body))
        if occurrences == 0:
            warnings.append((
                "WARN",
                f"Variable '{name}' is declared in frontmatter but never referenced "
                "in the body — either the skill doesn't need it, or a step that "
                "should use it was dropped."
            ))


def check_tool_justification(fields: dict, body: str, warnings: list):
    tools_field = fields.get("allowed-tools", "")
    tools = re.findall(r"[a-zA-Z_]+", tools_field)
    risky = {"bash", "create_file", "str_replace"}
    for tool in tools:
        if tool.lower() in risky:
            # heuristic: does the body mention this tool by name anywhere,
            # implying at least one concrete reason it's granted?
            if not re.search(rf"\b{tool}\b", body, re.IGNORECASE):
                warnings.append((
                    "WARN",
                    f"Tool '{tool}' is granted in allowed-tools but never mentioned "
                    "in the body. Per the Prompt-as-Permission guard: don't grant a "
                    "real-effect tool without a concrete, named use for it."
                ))


def check_bare_imperatives(body: str, warnings: list):
    """
    Real bare commands front-load the imperative: "NEVER commit to main
    directly." / "Claude MUST confirm before deleting." Meta-discussion
    of the anti-pattern buries the word mid-sentence instead: "If you
    find yourself writing ALWAYS or NEVER in all caps, ... that's a
    yellow flag." A purely token-based search can't tell these apart,
    which is exactly the bug that fired on skill-creator's own advice
    against bare imperatives. Position is a decent cheap proxy: require
    MUST/NEVER within the first few words of the sentence (after
    stripping bullet markers and a small set of common leading
    subjects), which real commands satisfy and meta-discussion usually
    doesn't.
    """
    sentences = re.split(r"(?<=[.!?])\s+", body)
    bare_count = 0
    examples = []
    leading_subjects = re.compile(
        r"^(?:[-*\d.)\s]*)(?:you|claude|the agent|this skill|it)?\s*",
        re.IGNORECASE,
    )
    for sent in sentences:
        stripped = leading_subjects.sub("", sent.strip(), count=1)
        first_words = stripped.split()[:4]
        window = " ".join(first_words)
        if not re.search(r"\bMUST\b|\bNEVER\b", window):
            continue
        if "because" not in sent.lower():
            bare_count += 1
            if len(examples) < 2:
                examples.append(sent.strip()[:100])
    if bare_count:
        warnings.append((
            "WARN",
            f"{bare_count} bare MUST/NEVER imperative(s) with no 'because' reasoning "
            f"in the same sentence — these break on edge cases the author didn't "
            f"anticipate. Example: \"{examples[0]}...\"" if examples else
            f"{bare_count} bare MUST/NEVER imperative(s) found with no reasoning attached."
        ))


def check_failure_recovery(body: str, warnings: list):
    if not re.search(r"\bfail|\berror|\brecover|\bfallback|\bif.*not\b", body, re.IGNORECASE):
        warnings.append((
            "INFO",
            "No mention of failure/error/recovery handling found in the body. "
            "If this skill runs tools that can error mid-workflow, consider "
            "naming what happens then."
        ))


def check_iron_law_present(body: str, warnings: list):
    if not re.search(r"iron law", body, re.IGNORECASE):
        warnings.append((
            "INFO",
            "No 'Iron Law' section found. Fine for a low-stakes skill; for "
            "anything gate-like or high-stakes, a single non-negotiable "
            "'X because Y' rule is expected."
        ))


def check_red_flags_table(body: str, warnings: list):
    if re.search(r"iron law", body, re.IGNORECASE) and not re.search(r"red flag", body, re.IGNORECASE):
        warnings.append((
            "WARN",
            "Iron Law is present but no Red Flags table found. An Iron Law "
            "without rationalizations named alongside it is easy for an "
            "agent to talk itself past."
        ))


def check_length(body: str, warnings: list):
    line_count = body.count("\n")
    if line_count > 500:
        warnings.append((
            "INFO",
            f"Body is ~{line_count} lines. Past ~500, consider moving procedures "
            "into workflows/*.md referenced by relative path instead of inlining."
        ))


def gather_full_body(path: Path, body: str) -> str:
    """
    A skill that splits procedures into workflows/*.md (the menu pattern)
    will legitimately reference variables and tools only inside those
    files, not in SKILL.md's own body. Checks that ask "is X used
    anywhere this skill actually runs" should search the sibling
    workflow files too, or they produce false positives on every skill
    that correctly followed the menu-pattern advice.
    """
    combined = body
    workflows_dir = path.parent / "workflows"
    if workflows_dir.exists():
        for wf in workflows_dir.glob("*.md"):
            combined += "\n" + wf.read_text(encoding="utf-8", errors="ignore")
    return combined


def lint_file(path: Path) -> list:
    # explicit utf-8: on Windows the platform default (cp1252) misdecodes
    # em-dashes into mojibake ending in a stray curly quote, which shifts
    # quote pairing in the vague-trigger check and corrupts printed output
    text = path.read_text(encoding="utf-8", errors="ignore")
    fields, body = read_frontmatter(text)

    if path.name != "SKILL.md":
        # workflows/*.md and scripts/* are procedure/logic files, not the
        # skill's entry point — they carry no frontmatter and no Iron Law
        # of their own, so checks about description/trigger/boundary and
        # variable declarations don't apply to them. Say so plainly rather
        # than emitting a misleading "no description field" error.
        return [(
            "INFO",
            f"{path.name} has no YAML frontmatter, which is expected — it's a "
            "workflow file, not a skill entry point. lint.py's description/"
            "trigger/boundary/variable/tool checks only apply to SKILL.md "
            "itself. Lint the parent SKILL.md to check this skill's "
            "triggering surface; use dependency_graph.py to check that this "
            "file is actually referenced from somewhere."
        )]

    full_body = gather_full_body(path, body)
    warnings = []
    check_description(fields, warnings)
    # variables and tool usage may legitimately live only in workflows/*.md
    check_variables(fields, full_body, warnings)
    check_tool_justification(fields, full_body, warnings)
    # style/structure checks stay scoped to SKILL.md's own body —
    # the Iron Law, Red Flags table, and length budget are specifically
    # about what SKILL.md itself contains
    check_bare_imperatives(body, warnings)
    check_failure_recovery(full_body, warnings)
    check_iron_law_present(body, warnings)
    check_red_flags_table(body, warnings)
    check_length(body, warnings)
    return warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=str, help="SKILL.md file, or a directory root with --recursive")
    ap.add_argument("--recursive", action="store_true", help="lint every SKILL.md under path")
    ap.add_argument("--strict", action="store_true", help="exit 1 if any WARN or ERROR fired")
    args = ap.parse_args()

    root = Path(args.path)
    targets = list(root.rglob("SKILL.md")) if args.recursive or root.is_dir() else [root]

    if not targets:
        print(f"No SKILL.md found under {root}.")
        return 0

    any_flagged = False
    for target in targets:
        warnings = lint_file(target)
        print(f"\n=== {target} ===")
        if not warnings:
            print("  No issues found.")
            continue
        for level, msg in warnings:
            if level in ("WARN", "ERROR"):
                any_flagged = True
            print(f"  [{level}] {msg}")

    print()
    if args.strict and any_flagged:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
