#!/usr/bin/env python3
"""
Schema migration CLI — upgrades a skill's SKILL.md to a target schema version.

Usage:
  python -m scripts.migrate_skill <skill-path> --to <version> [--dry-run]

Example:
  python -m scripts.migrate_skill . --to 2
  python -m scripts.migrate_skill ./skills/my-skill --to 2 --dry-run
"""
from __future__ import annotations

import sys
from pathlib import Path

# Import migration modules to populate the registry before calling migrate()
import scripts.migrations.v1_to_v2  # noqa: F401

from scripts.skill_ir import Skill
from scripts.migrations import migrate, find_path


def _main() -> int:
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    if dry_run:
        args = [a for a in args if a != "--dry-run"]

    if "--to" not in args or len(args) < 3:
        print(
            "Usage: python -m scripts.migrate_skill <skill-path> --to <version> [--dry-run]",
            file=sys.stderr,
        )
        return 1

    to_idx = args.index("--to")
    try:
        to_version = int(args[to_idx + 1])
    except (IndexError, ValueError):
        print("ERROR: --to requires an integer version number", file=sys.stderr)
        return 1

    skill_path = Path(args[0])
    try:
        skill = Skill.from_path(skill_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    current = skill.schema_version
    if current == to_version:
        print(f"Skill '{skill.name}' is already at schema version {current}. Nothing to do.")
        return 0

    try:
        path = find_path(current, to_version)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Migration path: {' → '.join(str(v) for step in path for v in step)}")

    if dry_run:
        print("[dry-run] No files were modified.")
        return 0

    updated = migrate(skill, to_version)
    updated.write_skill_md()
    print(
        f"Migrated '{skill.name}' from schema version {current} → {to_version}. "
        f"SKILL.md updated."
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
