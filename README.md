# Skill Creator

A comprehensive Claude skill for creating new skills and iteratively improving them through evaluation-driven development.

## Overview

Skill Creator helps you build high-quality Claude skills through a structured workflow:

1. **Define intent** - Capture what the skill should do and when it should trigger
2. **Interview & research** - Gather requirements, edge cases, and best practices
3. **Write the skill** - Create SKILL.md with clear instructions and examples
4. **Test & evaluate** - Run evals to measure skill performance
5. **Iterate** - Refine based on results and feedback
6. **Optimize** - Improve the skill description for better triggering

## Getting Started

### Basic Workflow

```bash
# Validate a skill
python scripts/validate_all.sh ./my-skill

# Run regression tests
python tests/test_pipeline.py

# Lint skill-creator itself
python scripts/lint.py .
```

### Creating Your First Skill

1. Use Skill Creator to design your skill's intent, trigger conditions, and behavior
2. Run `scripts/validate_all.sh` to check your skill structure
3. Add test cases to `tests/should_trigger.yaml` and `tests/should_not_trigger.yaml`
4. Iterate using the eval framework

## Skill Structure

```
my-skill/
├── SKILL.md           # Skill definition (required)
├── skill.yaml         # Metadata (optional but recommended)
├── LIFECYCLE.md       # Status and history (optional)
├── PERMISSIONS.md     # Detailed permissions (optional)
├── scripts/           # Helper scripts (optional)
├── references/        # Documentation files (optional)
├── agents/            # Agent definitions (optional)
├── assets/            # Images, templates (optional)
└── tests/             # Test cases (optional)
    ├── should_trigger.yaml
    ├── should_not_trigger.yaml
    └── expected_behavior.yaml
```

## Validation

Skill Creator validates itself using:

- **quick_validate.py** - Structural checks (YAML, required fields, naming)
- **lint.py** - Comprehensive linting (documentation, consistency, quality)
- **static_analysis.py** - Deeper structural analysis (dependencies, coverage)
- **skill_test.py** - Regression tests (trigger tests, behavioral validation)

Run all validators:

```bash
bash scripts/validate_all.sh .
```

## Testing

Test your skill before publishing:

```bash
# Run regression test suite
python tests/test_pipeline.py

# Run validation pipeline
python scripts/validate_all.sh .
```

## Continuous Integration

This repo includes GitHub Actions CI that runs on every push and PR:

- Structural validation
- Linting
- Static analysis
- Regression tests
- Security checks

See `.github/workflows/ci.yml` for configuration.

## Documentation

- **[SKILL.md](SKILL.md)** - Full skill documentation
- **[CHANGELOG.md](CHANGELOG.md)** - Release history
- **[LIFECYCLE.md](LIFECYCLE.md)** - Skill status and audit notes
- **[references/](references/)** - Additional documentation

## Requirements

- Python 3.11+
- PyYAML

## License

See [LICENSE.txt](LICENSE.txt) for details.

## Contributing

To improve Skill Creator:

1. Make changes to the skill or tooling
2. Run `bash scripts/validate_all.sh .` to ensure everything passes
3. Update CHANGELOG.md with your changes
4. Submit a pull request

## Support

For issues or questions:

1. Check existing test cases in `tests/`
2. Review the main SKILL.md documentation
3. Run the validation pipeline to catch configuration issues
