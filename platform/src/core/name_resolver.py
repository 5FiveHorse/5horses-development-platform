"""
Name resolution for FiveHorses projects.
Doctrine (2026-11-17, Gate 2): project identity is born ONCE, at upload, as a
folder slug. Everything downstream may refer to a project by its folder slug
OR its display name; this module is the sole translator between the two.
Display names are presentation, never identity.
Resolution tiers (first match wins):
  1. Exact folder match  -> the segment IS a folder name (slug callers, Gate 1 tests)
  2. Slugified match     -> segment is a human/display name whose slug exists on disk
  3. Display-name scan   -> segment normalizes equal to some project's
                            project.name (catches historical/irregular folders)
Nothing matched -> loud FileNotFoundError (never guess, never fabricate).
"""
import json
import re
from pathlib import Path
from typing import Union
# Characters illegal in Windows folder names
_INVALID_FS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9_]+")
def slugify(name: str) -> str:
    """
    Fold any human-readable project name into a safe folder slug.
    Superset of the upload route's legacy rule (lowercase, spaces->underscore):
    also strips punctuation and filesystem-illegal characters and collapses
    repeats, so "Miller's Row -- Phase 2!" -> "millers_row_phase_2".
    """
    s = (name or "").strip().lower()
    s = _INVALID_FS_CHARS.sub(" ", s)
    s = s.replace("-", "_")
    s = re.sub(r"\s+", "_", s)
    s = _NON_SLUG_CHARS.sub("", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unnamed_project"
def _norm(s: str) -> str:
    """Comparison key: case-folded, all whitespace/_/- collapsed away."""
    return re.sub(r"[_\-\s]+", "", (s or "").lower())
def _looks_unsafe(name: str) -> bool:
    """Reject traversal attempts and hidden/system paths outright."""
    if not name or name in (".", ".."):
        return True
    if "/" in name or "\\" in name or name.startswith("."):
        return True
    drive = re.match(r"^[A-Za-z]:", name)
    return bool(drive)
def resolve_name(name: str, projects_root: Union[str, Path]) -> str:
    """
    Resolve a folder slug or a display name to the on-disk project folder name.
    Args:
        name: URL segment, slug, or display name
        projects_root: the data/projects directory
    Returns:
        The actual folder name on disk (str)
    Raises:
        FileNotFoundError: if no project matches (message names the root).
    """
    root = Path(projects_root)
    if _looks_unsafe(name):
        raise FileNotFoundError(
            f"Project name '{name}' is not a valid project reference"
        )
    # Tier 1: the segment is already a real folder
    if (root / name / "project_data.json").exists():
        return name
    # Tier 2: slugifying the segment lands on a real folder
    slug = slugify(name)
    if (root / slug / "project_data.json").exists():
        return slug
    # Tier 3: scan display names and folder names, normalized comparison
    target = _norm(name)
    if target and root.is_dir():
        for project_dir in sorted(root.iterdir()):
            if not project_dir.is_dir():
                continue
            if _norm(project_dir.name) == target:
                return project_dir.name
            data_file = project_dir / "project_data.json"
            if not data_file.exists():
                continue
            try:
                data = json.loads(data_file.read_text(encoding="utf-8-sig"))
                display = (data.get("project") or {}).get("name") or ""
                if display and _norm(display) == target:
                    return project_dir.name
            except Exception:
                # Unreadable candidate: skip, never fabricate a match
                continue
    raise FileNotFoundError(
        f"No project matches '{name}' "
        f"(looked for folder or slug '{slug}' under {root})"
    )
