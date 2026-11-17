"""
Project Data Loader for FiveHorses Platform

v1.1 (2026-11-16): Restored methods lost during recovery (get_construction_costs,
get_contingency_percent, get_total_funding, load_from_template), added array-index
support to get_data (e.g. "buildings.homes[0].count"), list_projects again returns
the folder name as "path", and funding summation tolerates null (redacted) amounts
per confidentiality policy A7. Baseline: Ox Alpha delivery record.
"""
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .schema_validator import ProjectSchemaValidator
from .name_resolver import resolve_name, slugify


class ProjectLoader:
    """
    Loads and manages project data from JSON files

    Features:
    - Load project data from JSON
    - Validate against schema
    - Save and update projects
    - Manage multiple projects
    - Data access methods for agents
    """

    def __init__(self, projects_root: Optional[Path] = None):
        """
        Initialize project loader

        Args:
            projects_root: Root directory for project data. If None, uses default.
        """
        if projects_root is None:
            projects_root = Path(__file__).parent.parent.parent / "data" / "projects"

        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)

        self.validator = ProjectSchemaValidator()
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_project_name: Optional[str] = None

    def load_project(self, project_name: str) -> Dict[str, Any]:
        """
        Load a project by name

        Args:
            project_name: Name of the project

        Returns:
            Project data dictionary
        """
        project_name = resolve_name(project_name, self.projects_root)
        project_path = self.projects_root / project_name / "project_data.json"

        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found at {project_path}")

        with open(project_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Validate before loading
        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            raise ValueError(f"Invalid project data: {errors}")

        self.current_project = data
        self.current_project_name = project_name
        return data

    def save_project(self, data: Dict[str, Any], project_name: str, overwrite: bool = True) -> Path:
        """
        Save project data to file

        Args:
            data: Project data dictionary
            project_name: Name of the project
            overwrite: Whether to overwrite existing project

        Returns:
            Path to saved file
        """
        # Validate before saving
        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            raise ValueError(f"Invalid project data: {errors}")

        # Ensure metadata
        if "metadata" not in data:
            data["metadata"] = {}

        now = datetime.now().isoformat()
        if overwrite or "created" not in data["metadata"]:
            data["metadata"]["created"] = now
        data["metadata"]["updated"] = now

        # Create project directory
        project_dir = self.projects_root / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        # Save data
        project_path = project_dir / "project_data.json"
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.current_project = data
        self.current_project_name = project_name
        return project_path

    def load_from_template(self, template_name: str, project_name: str) -> Dict[str, Any]:
        """
        Load project data from a template

        Args:
            template_name: Name of the template to use
            project_name: Name for the new project

        Returns:
            Project data dictionary
        """
        # Load template
        template_path = Path(__file__).parent.parent / "templates" / f"{template_name}.json"
        if not template_path.exists():
            raise FileNotFoundError(f"Template '{template_name}' not found")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)

        # Override project name
        template_data["project"]["name"] = project_name

        # Save as new project
        return self.save_project(template_data, project_name)

    def list_projects(self) -> List[Dict[str, Any]]:
        """
        List all available projects

        Returns:
            List of project metadata dictionaries
        """
        projects = []

        for project_dir in self.projects_root.iterdir():
            if project_dir.is_dir():
                data_path = project_dir / "project_data.json"
                if data_path.exists():
                    try:
                        with open(data_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        projects.append({
                            "name": data.get("project", {}).get("name", project_dir.name),
                            "type": data.get("project", {}).get("type", "unknown"),
                            "location": data.get("project", {}).get("location", "unknown"),
                            "last_updated": data.get("metadata", {}).get("updated", "unknown"),
                            "slug": project_dir.name,
                            "path": project_dir.name
                        })
                    except Exception:
                        # Skip invalid projects
                        projects.append({
                            "name": project_dir.name,
                            "type": "invalid",
                            "location": "unknown",
                            "last_updated": "unknown",
                            "slug": project_dir.name,
                            "path": project_dir.name
                        })

        return projects

    def delete_project(self, project_name: str) -> bool:
        """
        Delete a project

        Args:
            project_name: Name of the project to delete

        Returns:
            True if deleted successfully
        """
        project_name = resolve_name(project_name, self.projects_root)
        project_dir = self.projects_root / project_name
        if project_dir.exists():
            shutil.rmtree(project_dir)
            return True
        return False

    # Data access methods for agents
    def get_project_name(self) -> str:
        """Get current project name"""
        return self.current_project_name

    def get_data(self, path: str) -> Any:
        """
        Get data from current project using dot notation, with optional
        array indexing (e.g. "buildings.homes[0].count").

        Args:
            path: Dot notation path

        Returns:
            Value at the specified path, or None if any step is absent
        """
        if self.current_project is None:
            raise ValueError("No project loaded")

        current: Any = self.current_project

        for part in path.split("."):
            m = re.match(r"^([^\[\]]*)((?:\[\d+\])*)$", part)
            if not m:
                return None
            base, index_part = m.group(1), m.group(2)

            if base:
                if isinstance(current, dict) and base in current:
                    current = current[base]
                else:
                    return None

            for token in re.findall(r"\[(\d+)\]", index_part):
                idx = int(token)
                if isinstance(current, list) and idx < len(current):
                    current = current[idx]
                else:
                    return None

        return current

    def get_project_site_area(self) -> float:
        """Get site area in hectares"""
        return self.get_data("project.site_area_ha") or 0

    def get_project_type(self) -> str:
        """Get project type"""
        return self.get_data("project.type") or "unknown"

    def get_total_dwellings(self) -> int:
        """Get total number of dwellings"""
        homes = self.get_data("buildings.homes")
        if not homes:
            return 0
        return sum(h.get("count", 0) for h in homes)

    def get_construction_costs(self) -> float:
        """Get total construction cost"""
        construction = self.get_data("phases.construction")
        if not construction:
            return 0
        cost = construction.get("cost")
        # None means redacted per policy A7 - treated as 0, never fabricated
        return cost if cost is not None else 0

    def get_contingency_percent(self) -> float:
        """Get contingency percentage"""
        return self.get_data("phases.contingency_percent") or 10

    def get_total_funding(self) -> float:
        """Get total funding amount (redacted/null sources contribute 0)"""
        sources = self.get_data("funding.sources")
        if not sources:
            return 0
        return sum((s.get("amount") or 0) for s in sources)

    def validate_current(self) -> bool:
        """Validate current project data"""
        if self.current_project is None:
            return False

        is_valid, _ = self.validator.validate(self.current_project)
        return is_valid


def load_project_data(project_name: str, projects_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Convenience function to load a project

    Args:
        project_name: Name of the project
        projects_root: Root directory for projects

    Returns:
        Project data dictionary
    """
    loader = ProjectLoader(projects_root)
    return loader.load_project(project_name)