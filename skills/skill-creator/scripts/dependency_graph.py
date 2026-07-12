#!/usr/bin/env python3
"""
Formal dependency graph — typed node graph over skill.yaml dependencies and
SKILL.md cross-references.

Enables: cycle detection, missing-node audit, impact analysis (what breaks
if I change this file?), and export to JSON or Graphviz DOT.

Usage: python -m scripts.dependency_graph <skill-path> [--format json|dot|summary]
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from scripts.skill_ir import Skill


@dataclass
class SkillGraph:
    skill: Skill
    nodes: set[str] = field(default_factory=set)
    # edges: directed (from_node, to_node)
    edges: list[tuple[str, str]] = field(default_factory=list)
    _adj: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))
    _radj: dict[str, list[str]] = field(default_factory=lambda: defaultdict(list))  # reverse adjacency

    def build(self) -> None:
        """Populate nodes and edges from skill.yaml deps + SKILL.md body."""
        root = "SKILL.md"
        self.nodes.add(root)

        # skill.yaml dependencies
        for dep in self.skill.dependencies:
            self.nodes.add(dep)
            self._add_edge(root, dep)

        # Cross-references parsed from SKILL.md body
        # Match patterns like `agents/grader.md`, `scripts/run_eval.py`, etc.
        ref_pattern = re.compile(
            r"`((?:agents|scripts|references|tests|eval-viewer|generators)/[\w./\-]+\.\w+)`"
        )
        body_lines = self.skill.body.split("\n")
        for line in body_lines:
            for m in ref_pattern.finditer(line):
                dep = m.group(1)
                self.nodes.add(dep)
                if dep != root:
                    self._add_edge(root, dep)

        # Build adjacency for graph algorithms
        self._adj.clear()
        self._radj.clear()
        for frm, to in self.edges:
            self._adj[frm].append(to)
            self._radj[to].append(frm)

    def _add_edge(self, frm: str, to: str) -> None:
        if (frm, to) not in self.edges:
            self.edges.append((frm, to))

    def detect_cycles(self) -> list[list[str]]:
        """Return list of cycles (each cycle is a list of node names). DFS-based."""
        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbour in self._adj.get(node, []):
                if neighbour not in visited:
                    dfs(neighbour, path)
                elif neighbour in rec_stack:
                    cycle_start = path.index(neighbour)
                    cycles.append(path[cycle_start:] + [neighbour])
            path.pop()
            rec_stack.discard(node)

        for node in list(self.nodes):
            if node not in visited:
                dfs(node, [])
        return cycles

    def missing_nodes(self) -> list[str]:
        """Return nodes that are declared but whose paths don't exist on disk."""
        missing = []
        for node in sorted(self.nodes):
            if node == "SKILL.md":
                continue
            if not (self.skill.skill_path / node).exists():
                missing.append(node)
        return missing

    def impact_of(self, node: str) -> list[str]:
        """Return all nodes that depend on `node` (reverse traversal, BFS)."""
        result: list[str] = []
        visited: set[str] = set()
        queue = [node]
        while queue:
            current = queue.pop(0)
            for parent in self._radj.get(current, []):
                if parent not in visited:
                    visited.add(parent)
                    result.append(parent)
                    queue.append(parent)
        return result

    def to_json(self) -> dict:
        return {
            "nodes": sorted(self.nodes),
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "missing": self.missing_nodes(),
            "cycles": self.detect_cycles(),
        }

    def to_dot(self) -> str:
        lines = ['digraph skill_deps {', '  rankdir=LR;']
        for node in sorted(self.nodes):
            exists = node == "SKILL.md" or (self.skill.skill_path / node).exists()
            color = "black" if exists else "red"
            lines.append(f'  "{node}" [color={color}];')
        for frm, to in self.edges:
            lines.append(f'  "{frm}" -> "{to}";')
        lines.append("}")
        return "\n".join(lines)

    def summary(self) -> str:
        missing = self.missing_nodes()
        cycles = self.detect_cycles()
        lines = [
            f"Nodes:   {len(self.nodes)}",
            f"Edges:   {len(self.edges)}",
            f"Missing: {len(missing)}",
            f"Cycles:  {len(cycles)}",
        ]
        if missing:
            lines.append("\nMissing nodes:")
            for m in missing:
                lines.append(f"  - {m}")
        if cycles:
            lines.append("\nCycles detected:")
            for c in cycles:
                lines.append(f"  {' -> '.join(c)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main() -> int:
    args = sys.argv[1:]
    fmt = "summary"
    if "--format" in args:
        idx = args.index("--format")
        fmt = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    if not args:
        print("Usage: python -m scripts.dependency_graph <skill-path> [--format json|dot|summary]", file=sys.stderr)
        return 1

    skill_path = Path(args[0])
    try:
        skill = Skill.from_path(skill_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    g = SkillGraph(skill=skill)
    g.build()

    if fmt == "json":
        print(json.dumps(g.to_json(), indent=2))
    elif fmt == "dot":
        print(g.to_dot())
    else:
        print(g.summary())

    return 0


if __name__ == "__main__":
    sys.exit(_main())
