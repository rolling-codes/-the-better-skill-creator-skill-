"""
Migration template: schema version 1 → 2.

This is an identity migration demonstrating the registration pattern.
A real v2 migration would transform the Skill dataclass fields here.

Register format:
  register(from_version, to_version, migration_fn)

The migration function receives a Skill instance and returns a (possibly new)
Skill instance with schema_version updated to the target version.
"""
from __future__ import annotations

from scripts.migrations import register


def _migrate_v1_to_v2(skill):
    """Identity migration: copies all fields, bumps schema_version to 2."""
    import dataclasses
    updated = dataclasses.replace(skill, schema_version=2)
    return updated


register(1, 2, _migrate_v1_to_v2)
