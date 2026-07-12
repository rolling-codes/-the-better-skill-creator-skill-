"""
Schema migration registry for skill SKILL.md versions.

Usage pattern:
  from scripts.migrations import migrate
  updated_skill = migrate(skill, to_version=2)

Migration modules register themselves via register():
  from scripts.migrations import register
  def my_migration(skill): ...
  register(1, 2, my_migration)
"""
from __future__ import annotations

from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from scripts.skill_ir import Skill

# { (from_version, to_version): migration_fn }
_registry: dict[tuple[int, int], Callable] = {}


def register(from_v: int, to_v: int, fn: Callable) -> None:
    """Register a migration function from version from_v to to_v."""
    _registry[(from_v, to_v)] = fn


def find_path(from_v: int, to_v: int) -> list[tuple[int, int]]:
    """
    Find a chain of registered migrations from from_v to to_v.
    Uses BFS over registered transitions.
    Returns list of (from, to) steps, or raises ValueError if no path found.
    """
    if from_v == to_v:
        return []
    # BFS
    queue: list[list[tuple[int, int]]] = [[]]
    visited: set[int] = {from_v}
    # seed: all transitions from from_v
    for (f, t) in _registry:
        if f == from_v:
            queue.append([(f, t)])
            visited.add(t)
    while queue:
        path = queue.pop(0)
        if not path:
            continue
        last_to = path[-1][1]
        if last_to == to_v:
            return path
        for (f, t) in _registry:
            if f == last_to and t not in visited:
                visited.add(t)
                queue.append(path + [(f, t)])
    raise ValueError(
        f"No migration path found from schema version {from_v} to {to_v}. "
        f"Available steps: {list(_registry.keys())}"
    )


def migrate(skill: "Skill", to_version: int) -> "Skill":
    """
    Apply the shortest registered migration path from skill.schema_version to
    to_version. Returns a (possibly new) Skill instance with updated schema_version.

    Callers are responsible for importing migration modules before calling this
    so the registry is populated (migrate_skill.py does this automatically).
    """
    current = skill.schema_version
    if current == to_version:
        return skill
    path = find_path(current, to_version)
    result = skill
    for (f, t) in path:
        fn = _registry[(f, t)]
        result = fn(result)
    return result
