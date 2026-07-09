#!/usr/bin/env python3
"""
overlap_check.py — Blast Radius Analysis heuristic.

Compares SKILL.md description fields pairwise using Jaccard similarity over
normalized token sets, with extra weight on shared nouns/verbs pulled from the
Trigger clause specifically (the part most likely to cause real collisions).

Usage:
    python overlap_check.py <skills_root> [--threshold 0.35]

Exits 0 always; prints a table. A pair above --threshold is a candidate for a
narrower Boundary clause, not an automatic failure — use judgment.
"""
import re
import sys
import argparse
from pathlib import Path
from itertools import combinations

STOPWORDS = {
    "the", "a", "an", "this", "for", "and", "or", "when", "not", "use",
    "to", "of", "in", "on", "with", "is", "are", "be", "it", "that",
    "user", "users", "any", "if", "as", "into", "e.g", "eg",
}


def extract_frontmatter_field(text: str, field: str) -> str:
    m = re.search(rf"^{field}:\s*(.+)$", text, re.MULTILINE)
    if not m:
        return ""
    val = m.group(1).strip().strip('"').strip("'")
    return val


def tokenize(s: str) -> set:
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]+", s.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def split_trigger_clause(description: str) -> str:
    """Best-effort extraction of the 'when ...' trigger clause."""
    m = re.search(r"\bwhen\b(.+?)(;|\.|$)", description, re.IGNORECASE)
    return m.group(1) if m else description


def load_skills(root: Path):
    skills = []
    for path in root.rglob("SKILL.md"):
        text = path.read_text(errors="ignore")
        name = extract_frontmatter_field(text, "name") or path.parent.name
        desc = extract_frontmatter_field(text, "description")
        skills.append({"name": name, "path": str(path), "description": desc})
    return skills


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skills_root", type=str)
    ap.add_argument("--threshold", type=float, default=0.35)
    args = ap.parse_args()

    root = Path(args.skills_root)
    skills = load_skills(root)

    if len(skills) < 2:
        print(f"Found {len(skills)} skill(s) under {root} — nothing to compare.")
        return 0

    print(f"Loaded {len(skills)} skills. Pairwise overlap (Jaccard, threshold={args.threshold}):\n")

    flagged = []
    for a, b in combinations(skills, 2):
        tok_a = tokenize(a["description"])
        tok_b = tokenize(b["description"])
        full_score = jaccard(tok_a, tok_b)

        trig_a = tokenize(split_trigger_clause(a["description"]))
        trig_b = tokenize(split_trigger_clause(b["description"]))
        trig_score = jaccard(trig_a, trig_b)

        # Weighted: trigger-clause overlap counts double since that's what
        # actually causes two skills to both load for one user request.
        combined = (full_score + 2 * trig_score) / 3

        if combined >= args.threshold:
            flagged.append((a["name"], b["name"], combined, tok_a & tok_b))

    if not flagged:
        print("No pairs above threshold. No overlap found.")
        return 0

    for name_a, name_b, score, shared in sorted(flagged, key=lambda x: -x[2]):
        shared_str = ", ".join(sorted(shared)) or "(trigger-clause overlap only)"
        print(f"  {name_a}  <->  {name_b}   score={score:.2f}   shared: {shared_str}")

    print(
        "\nAny pair above threshold is a candidate for a narrower Boundary "
        "clause on one or both skills — a plausible user request could "
        "reasonably match both descriptions, which means both get loaded "
        "into the same session."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
