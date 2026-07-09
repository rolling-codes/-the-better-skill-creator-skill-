# Skill-Architect Setup

Skill-architect has no prerequisites. It's a standalone meta-skill for Claude Code,
packaged as a plugin.

## Install

From a local checkout:

```bash
claude plugin marketplace add /path/to/skill-architect
claude plugin install skill-architect@skill-architect-local
```

Or from GitHub, inside Claude Code:

```
/plugin marketplace add rolling-codes/-the-better-skill-creator-skill-
/plugin install skill-architect
```

Restart Claude Code (or run `/reload-plugins`) — skills register at session start.

## Verify

```
/skill-architect
```

If it prompts for a mode (create / audit / variance-check), it's working.

## That's it

No environment setup, no prerequisites. Python 3.8+ only if you want the optional
lint/overlap/dependency scripts.

## Note on Built Skills

Skills you create or audit with skill-architect may have their own prerequisites (e.g., dev-workflow requires ECC rules to exist). Those are the responsibility of the individual skill, not skill-architect itself.
