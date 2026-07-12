#!/usr/bin/env python3
"""
Skill Packager - Creates a distributable .skill file of a skill folder

Usage:
    python utils/package_skill.py <path/to/skill-folder> [output-directory]

Example:
    python utils/package_skill.py skills/public/my-skill
    python utils/package_skill.py skills/public/my-skill ./dist
"""

import sys
from pathlib import Path
from scripts.quick_validate import validate_skill
from scripts.compiler_context import CompilerContext
from scripts.stages import LintStage, SemanticStage, RepairStage, ApplyRepairsStage, ScoreStage, PackageStage


def package_skill(skill_path, output_dir=None):
    """
    Package a skill folder into a .skill file.

    Args:
        skill_path: Path to the skill folder
        output_dir: Optional output directory for the .skill file (defaults to current directory)

    Returns:
        Path to the created .skill file, or None if error
    """
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8")

    skill_path = Path(skill_path).resolve()

    # Validate folder structure (unchanged)
    if not skill_path.exists():
        print(f"ERROR: Skill folder not found: {skill_path}")
        return None
    if not skill_path.is_dir():
        print(f"ERROR: Path is not a directory: {skill_path}")
        return None
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"ERROR: SKILL.md not found in {skill_path}")
        return None

    # Quick structural validation (unchanged)
    print("Validating skill...")
    valid, message = validate_skill(skill_path)
    if not valid:
        print(f"ERROR: Validation failed: {message}")
        return None
    print(f"OK: {message}")

    # Build context
    ctx = CompilerContext.create(skill_path, output_dir)

    # Analysis pass
    print("Running analysis...")
    LintStage().run(ctx)
    SemanticStage().run(ctx)

    # Repair pass
    RepairStage().run(ctx)
    ApplyRepairsStage().run(ctx)

    if ctx.applied_fixes:
        print("  Auto-repaired:")
        for fix in ctx.applied_fixes:
            print(f"    {fix}")
        # Re-analyze after in-place repairs
        ctx.diagnostics.clear()
        LintStage().run(ctx)
        SemanticStage().run(ctx)

    # Report findings
    errors = [f for f in ctx.diagnostics if f.severity == "error"]
    if errors:
        for f in errors:
            print(f"  ERROR: {f}")
        print(f"\nERROR: {len(errors)} error(s) could not be auto-repaired. Fix before packaging.")
        return None
    for f in ctx.diagnostics:
        tag = "WARN" if f.severity == "warning" else "INFO"
        print(f"  {tag}: {f}")
    if not ctx.diagnostics and not ctx.applied_fixes:
        print("  No issues found.")
    print()

    # Score
    print("Architecture score...")
    ScoreStage().run(ctx)
    if ctx.score:
        print(str(ctx.score))
        if ctx.score.overall < 70:
            print(f"\nWARN: Score {ctx.score.overall} is below 70. Consider improving before sharing.")
        else:
            print(f"\nOK: Score {ctx.score.overall}")
    print()

    # Package
    print("Packaging...")
    PackageStage().run(ctx)

    if ctx.output_path:
        print(f"\nOK: Successfully packaged skill to: {ctx.output_path}")
        return ctx.output_path
    else:
        print("ERROR: Packaging failed.")
        return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        getattr(sys.stdout, "reconfigure")(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Usage: python utils/package_skill.py <path/to/skill-folder> [output-directory]")
        print("\nExample:")
        print("  python utils/package_skill.py skills/public/my-skill")
        print("  python utils/package_skill.py skills/public/my-skill ./dist")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Packaging skill: {skill_path}")
    if output_dir:
        print(f"   Output directory: {output_dir}")
    print()

    result = package_skill(skill_path, output_dir)

    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
