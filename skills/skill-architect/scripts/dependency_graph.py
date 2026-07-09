#!/usr/bin/env python3
"""
dependency_graph.py — maps and checks the reference graph inside one skill.

A skill that's grown past a single SKILL.md can silently accumulate two
failure modes:
  - a file referenced from SKILL.md or a companion .md file that no
    longer exists (broken link — the agent will hit a missing file
    mid-task)
  - a file sitting in a subdirectory that nothing references anymore
    (orphan — dead weight, or a sign a rewrite forgot to wire something
    back in)

IMPORTANT SCOPE NOTE (learned from running this against real skills,
not just skill-architect's own files): plenty of real, legitimate
skills document a directory generically ("scripts/ - executable code
for deterministic tasks") without naming every individual file, and
scripts commonly import each other directly rather than being named in
SKILL.md prose at all. Treating "not individually named in prose" as
equivalent to "orphaned" produces false alarms on exactly that pattern.
So orphan reporting here is two-tier:
  - ORPHAN (high confidence): the file's entire parent top-level
    directory is never mentioned anywhere in SKILL.md or a companion
    .md file. Nothing acknowledges this directory exists at all.
  - UNNAMED (low confidence, informational only): the specific file
    isn't individually named, but its parent directory is mentioned
    generically elsewhere. This is a common, legitimate convention,
    not a defect — flagged as INFO so a human can still glance at it,
    not as a problem to fix.

Broken links remain the trustworthy, high-confidence signal regardless
of convention: if a specific path is named and that exact path doesn't
exist, that's a real bug independent of how the rest of the skill
documents its files.

This is deliberately just a reference-graph checker, not a claim that
skills are "compiled" or have a formal call graph — the actual
triggering/routing decision still happens via a model reading text.

Usage:
    python dependency_graph.py <skill_root>

Exits 0 always; prints the graph and any broken-link / orphan findings.
"""
import re
import sys
import argparse
from pathlib import Path

# top-level directories this treats as "content" dirs worth scanning —
# built dynamically from what's actually on disk, not hardcoded to
# workflows/scripts, so references/, assets/, agents/, etc. all count.
SKIP_DIRS = {".git", "__pycache__", "node_modules"}


def build_ref_pattern(dir_names: set) -> re.Pattern:
    if not dir_names:
        # still match nothing gracefully rather than erroring
        return re.compile(r"(?!x)x")
    alt = "|".join(re.escape(d) for d in sorted(dir_names))
    # require a real file extension at the end so nested paths
    # (e.g. scripts/office/helpers/pptx_chart.py) are captured whole
    # instead of truncating at the first slash — that truncation was
    # the exact bug that produced a phantom "scripts/office MISSING"
    # finding on a real skill.
    return re.compile(rf"\b((?:{alt})/[\w\-./]+\.\w+)\b")


def build_dir_mention_pattern(dir_names: set) -> re.Pattern:
    if not dir_names:
        return re.compile(r"(?!x)x")
    alt = "|".join(re.escape(d) for d in sorted(dir_names))
    return re.compile(rf"\b({alt})/")


def find_references(text: str, ref_pattern: re.Pattern) -> set:
    return set(ref_pattern.findall(text))


def find_mentioned_dirs(text: str, dir_pattern: re.Pattern) -> set:
    return set(dir_pattern.findall(text))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_root", type=str)
    args = ap.parse_args()

    root = Path(args.skill_root)
    main_skill = root / "SKILL.md"
    if not main_skill.exists():
        print(f"No SKILL.md found at {main_skill} — is this a skill root?")
        return 0

    top_level_dirs = {
        p.name for p in root.iterdir()
        if p.is_dir() and p.name not in SKIP_DIRS
    }

    ref_pattern = build_ref_pattern(top_level_dirs)
    dir_pattern = build_dir_mention_pattern(top_level_dirs)

    # every .md file at the skill root or directly inside a top-level
    # dir can plausibly contain references (mirrors the old
    # workflows/*.md assumption, generalized to any dir name)
    referencing_files = [main_skill]
    for d in top_level_dirs:
        referencing_files.extend((root / d).glob("*.md"))

    all_refs = {}       # ref path -> list of files that mention it (specifically, by name)
    mentioned_dirs = set()  # top-level dir names acknowledged anywhere, even generically
    for f in referencing_files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        for ref in find_references(text, ref_pattern):
            all_refs.setdefault(ref, []).append(f.relative_to(root))
        mentioned_dirs |= find_mentioned_dirs(text, dir_pattern)

    # actual files on disk under every top-level content directory
    actual_files = set()
    for d in top_level_dirs:
        for p in (root / d).rglob("*"):
            if p.is_file():
                # as_posix() so Windows backslash paths compare equal to the
                # forward-slash references extracted from markdown
                actual_files.add(p.relative_to(root).as_posix())

    referenced_paths = set(all_refs.keys())

    broken = sorted(referenced_paths - actual_files)
    unnamed_files = sorted(actual_files - referenced_paths)

    # split unnamed files into high-confidence ORPHAN (parent dir never
    # mentioned at all) vs low-confidence UNNAMED (dir mentioned
    # generically, just not this specific file)
    orphans, unnamed_only = [], []
    for f in unnamed_files:
        top_dir = f.split("/", 1)[0]
        if top_dir in mentioned_dirs:
            unnamed_only.append(f)
        else:
            orphans.append(f)

    print(f"=== Reference graph for {root.name} ===\n")
    print(f"Scanned SKILL.md + {len(referencing_files) - 1} companion .md file(s) "
          f"across dirs: {sorted(top_level_dirs) or '(none)'}\n")

    print("Specifically-named references:")
    if not all_refs:
        print("  (none found)")
    for ref, sources in sorted(all_refs.items()):
        src_str = ", ".join(str(s) for s in sources)
        exists = "OK" if ref in actual_files else "MISSING"
        print(f"  {ref}  <- referenced by [{src_str}]  [{exists}]")

    print("\nBroken links (specifically named but file doesn't exist — high confidence, real bug):")
    if not broken:
        print("  None.")
    else:
        for b in broken:
            print(f"  [BROKEN] {b}  referenced by {[str(s) for s in all_refs[b]]}")

    print("\nOrphaned files (parent directory never mentioned anywhere — high confidence dead weight):")
    if not orphans:
        print("  None.")
    else:
        for o in sorted(orphans):
            print(f"  [ORPHAN] {o}  — nothing acknowledges this directory exists; wire it in or remove it")

    if unnamed_only:
        print("\nUnnamed but acknowledged files (directory is documented generically, file just isn't "
              "individually named — common and often fine, not flagged as a problem):")
        for u in sorted(unnamed_only):
            print(f"  [UNNAMED] {u}")

    print()
    if not broken and not orphans:
        print("Graph is clean: no broken links, no unacknowledged directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
