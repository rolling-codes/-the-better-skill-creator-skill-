# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: [SemVer](https://semver.org/).

## [Unreleased]

## [1.4.1] - 2026-07-15

### Fixed

- Variance-check mode now runs `scripts/lint.py` and `scripts/dependency_graph.py`
  after any Gate-5-style file edit — previously the only mode that could ship an
  edit without the deterministic checks firing (RBA-F01).
- Gate 0's frontmatter-only collection command is now normative: the prose no
  longer invites full-file reads of sibling SKILL.md files whose bodies no gate
  consumes (RBA-F10).
- `memory/lessons.md` no longer trips `dependency_graph.py`'s path matcher with
  a described (not referenced) external path, removing a false broken-link finding.
- `plugin.json` version synced with release tags (was stuck at 1.1.0 through
  v1.2.0–v1.4.0).

## Earlier releases

v1.0.0 – v1.4.0 predate this changelog; see the
[release tags](https://github.com/rolling-codes/-the-better-skill-creator-skill-/tags).
