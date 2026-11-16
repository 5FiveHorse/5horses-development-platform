"""
Project Data Loader for FiveHorses Platform
"""
import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from .schema_validator import ProjectSchemaValidator


class ProjectLoader:
    """Loads and manages project data from JSON files"""

    def __init__(self, projects_root: Optional[Path] = None):
        if projects_root is None:
            projects_root = Path(__file__).parent.parent.parent / "data" / "projects"
        self.projects_root = Path(projects_root)
        self.projects_root.mkdir(parents=True, exist_ok=True)
        self.validator = ProjectSchemaValidator()
        self.current_project: Optional[Dict[str, Any]] = None
        self.current_project_name: Optional[str] = None

    def load_project(self, project_name: str) -> Dict[str, Any]:
        project_path = self.projects_root / project_name / "project_data.json"
        if not project_path.exists():
            raise FileNotFoundError(f"Project '{project_name}' not found at {project_path}")

        with open(project_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            raise ValueError(f"Invalid project data: {errors}")

        self.current_project = data
        self.current_project_name = project_name
        return data

    def save_project(self, data: Dict[str, Any], project_name: str, overwrite: bool = True) -> Path:
        is_valid, errors = self.validator.validate(data)
        if not is_valid:
            raise ValueError(f"Invalid project data: {errors}")

        if "metadata" not in data:
            data["metadata"] = {}
        now = datetime.now().isoformat()
        if overwrite or "created" not in data["metadata"]:
            data["metadata"]["created"] = now
        data["metadata"]["updated"] = now

        project_dir = self.projects_root / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        project_path = project_dir / "project_data.json"
        with open(project_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.current_project = data
        self.current_project_name = project_name
        return project_path

    def list_projects(self) -> List[Dict[str, Any]]:
        projects = []
        for project_dir in self.projects_root.iterdir():
            if project_dir.is_dir():
                data_path = project_dir / "project_data.json"
                if data_path.exists():
                    try:
                        with open(data_path, 'r') as f:
                            data = json.load(f)
                        projects.append({
                            "name": data.get("project", {}).get("name", project_dir.name),
                            "type": data.get("project", {}).get("type", "unknown"),
                            "location": data.get("project", {}).get("location", "unknown"),
                            "last_updated": data.get("metadata", {}).get("updated", "unknown"),
                            "path": str(project_dir)
                        })
                    except Exception:
                        projects.append({
                            "name": project_dir.name, "type": "invalid",
                            "location": "unknown", "last_updated": "unknown", "path": str(project_dir)
                        })
        return projects

    def delete_project(self, project_name: str) -> bool:
        project_dir = self.projects_root / project_name
        if project_dir.exists():
            shutil.rmtree(project_dir)
            return True
        return False

    def get_project_name(self) -> str:
        return self.current_project_name

    def get_data(self, path: str) -> Any:
        if self.current_project is None:
            raise ValueError("No project loaded")
        parts = path.split(".")
        current = self.current_project
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def get_project_site_area(self) -> float:
        return self.get_data("project.site_area_ha") or 0

    def get_project_type(self) -> str:
        return self.get_data("project.type") or "unknown"

    def get_total_dwellings(self) -> int:
        homes = self.get_data("buildings.homes")
        if not homes:
            return 0
        return sum(h.get("count", 0) for h in homes)

    def validate_current(self) -> bool:
        if self.current_project is None:
            return False
        is_valid, _ = self.validator.validate(self.current_project)
        return is_valid
