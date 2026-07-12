from __future__ import annotations
import fnmatch
import zipfile
from pathlib import Path
from scripts.compiler_context import CompilerContext

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".pytest_cache"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
# Directories excluded only at the skill root (not when nested deeper).
ROOT_EXCLUDE_DIRS = {"evals"}


def _should_exclude(rel_path: Path) -> bool:
    """Check if a path should be excluded from packaging."""
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    # rel_path is relative to skill_path.parent, so parts[0] is the skill
    # folder name and parts[1] (if present) is the first subdir.
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


class PackageStage:
    name = "package"
    requires = {"skill_spec"}
    provides = {"output_path"}

    def run(self, ctx: CompilerContext) -> None:
        skill_path = ctx.skill_path
        skill_name = skill_path.name
        out_dir = ctx.output_dir if ctx.output_dir else Path.cwd()
        out_dir.mkdir(parents=True, exist_ok=True)
        skill_filename = out_dir / f"{skill_name}.skill"

        with zipfile.ZipFile(skill_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill_path.rglob("*"):
                if not file_path.is_file():
                    continue
                arcname = file_path.relative_to(skill_path.parent)
                if _should_exclude(arcname):
                    print(f"  Skipped: {arcname}")
                    continue
                zipf.write(file_path, arcname)
                print(f"  Added: {arcname}")

        ctx.output_path = skill_filename
