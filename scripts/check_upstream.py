#!/usr/bin/env python3
"""Report drift between this fork and Anthropic's upstream skill-creator.

Downloads the upstream tarball from the anthropics/skills GitHub repo and
compares it against the local skill folder using git blob SHAs (computed
locally, no git required), then reports three lists:

  upstream-only  files Anthropic added that this fork lacks
  local-only     files this fork added (the governance layer — expected)
  changed        shared files whose contents diverged (rebase candidates)

This turns "has upstream moved?" from an archaeology project into a
five-minute check. Run it before each release, or whenever Anthropic
announces a skills update.

Usage:
    python -m scripts.check_upstream [path/to/skill-folder]

Network: one read-only GET to codeload.github.com (the tarball host).
The tarball route is deliberate: the trees API endpoint rejects anonymous
callers from shared IPs with 403s, while codeload serves the same bytes
with no rate-limit drama. No authentication, nothing leaves the machine
beyond the request URL. Declared in PERMISSIONS.md as network.request
(low risk, read-only, pinned host).
"""

import hashlib
import io
import sys
import tarfile
import urllib.request
from pathlib import Path

UPSTREAM_REPO = "anthropics/skills"
UPSTREAM_PATH = "skills/skill-creator"  # path inside the repo, per its layout
UPSTREAM_BRANCH = "main"
TARBALL_URL = (
    f"https://codeload.github.com/{UPSTREAM_REPO}/tar.gz/refs/heads/"
    f"{UPSTREAM_BRANCH}"
)

# Local files that are ours by design — listed here so the report separates
# "expected fork additions" from "accidental drift". Update when the
# governance layer grows.
EXPECTED_LOCAL_ONLY_PREFIXES = (
    "skill.yaml",
    "LIFECYCLE.md",
    "PERMISSIONS.md",
    "tests/",
    "references/environments.md",
    "references/trigger-confidence.md",
    "references/dependency-graph.md",
    "scripts/skill_test.py",
    "scripts/validate_all.sh",
    "scripts/check_upstream.py",
    "scripts/hooks/",
)


def git_blob_sha(path: Path) -> str:
    """SHA-1 the way git hashes a blob, so we can compare against the API."""
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def fetch_upstream_tree() -> dict:
    """Return {relative_path: blob_sha} for upstream skill-creator files."""
    req = urllib.request.Request(
        TARBALL_URL, headers={"User-Agent": "skill-creator-fork-drift-check"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read()
    out = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.isfile():
                continue
            # First path component is "<repo>-<branch>/" — strip it, then
            # keep only files under the skill's path inside the repo.
            rel_repo = member.name.split("/", 1)[1] if "/" in member.name else ""
            prefix = UPSTREAM_PATH + "/"
            if not rel_repo.startswith(prefix):
                continue
            data = tar.extractfile(member).read()
            sha = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            out[rel_repo[len(prefix):]] = sha
    return out


def local_tree(skill_path: Path) -> dict:
    """Return {relative_path: blob_sha} for local files, skipping caches."""
    out = {}
    for f in skill_path.rglob("*"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(skill_path)).replace("\\", "/")
        if "__pycache__" in rel or rel.endswith((".pyc", ".skill")):
            continue
        out[rel] = git_blob_sha(f)
    return out


def main():
    skill_path = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (skill_path / "SKILL.md").exists():
        print(f"No SKILL.md at {skill_path} — pass the skill folder path.")
        sys.exit(1)

    print(f"Fetching upstream tarball ({UPSTREAM_REPO}@{UPSTREAM_BRANCH}, {UPSTREAM_PATH})...")
    try:
        upstream = fetch_upstream_tree()
    except Exception as e:
        print(f"Could not reach GitHub: {e}")
        print("Drift status UNKNOWN — do not treat this as 'no drift'.")
        sys.exit(1)
    if not upstream:
        print("Upstream tree came back empty — the path or branch may have "
              "moved upstream. Drift status UNKNOWN; check the repo layout.")
        sys.exit(1)

    local = local_tree(skill_path)
    upstream_only = sorted(set(upstream) - set(local))
    local_only = sorted(set(local) - set(upstream))
    changed = sorted(p for p in set(local) & set(upstream)
                     if local[p] != upstream[p])

    expected = [p for p in local_only
                if p.startswith(EXPECTED_LOCAL_ONLY_PREFIXES)]
    unexpected = [p for p in local_only if p not in expected]

    print(f"\nShared files unchanged: "
          f"{len(set(local) & set(upstream)) - len(changed)}")

    if upstream_only:
        print(f"\nUPSTREAM-ONLY ({len(upstream_only)}) — Anthropic added these; "
              "review for adoption:")
        for pth in upstream_only:
            print(f"  {pth}")

    if changed:
        print(f"\nCHANGED ({len(changed)}) — shared files that diverged; "
              "each is either your intentional edit or upstream movement:")
        for pth in changed:
            print(f"  {pth}")

    print(f"\nLOCAL-ONLY, expected fork additions: {len(expected)}")
    if unexpected:
        print(f"LOCAL-ONLY, NOT in the expected list ({len(unexpected)}) — "
              "either add to EXPECTED_LOCAL_ONLY_PREFIXES or investigate:")
        for pth in unexpected:
            print(f"  {pth}")

    drift = bool(upstream_only or changed)
    print("\nVerdict:", "DRIFT DETECTED — plan a rebase pass." if drift
          else "In sync with upstream (fork additions aside).")
    sys.exit(2 if drift else 0)


if __name__ == "__main__":
    main()
