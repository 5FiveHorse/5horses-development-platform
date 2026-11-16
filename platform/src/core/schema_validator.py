"""
JSON Schema Validator for FiveHorses Project Data
Handles validation of project data against the defined schema
"""
import json
from jsonschema import validate, ValidationError, Draft7Validator
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class ProjectSchemaValidator:
    """Validates project data against the JSON schema"""

    def __init__(self, schema_path: Optional[Path] = None):
        if schema_path is None:
            schema_path = Path(__file__).parent.parent.parent / "data" / "schemas" / "project_schema.json"
        self.schema = self._load_schema(schema_path)
        self.validator = Draft7Validator(self.schema)

    def _load_schema(self, path: Path) -> Dict[str, Any]:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
        errors = []
        try:
            validate(instance=data, schema=self.schema)
            return True, None
        except ValidationError:
            for error in self.validator.iter_errors(data):
                errors.append({
                    "path": ".".join(str(p) for p in error.path) if error.path else "root",
                    "message": error.message,
                    "instance": error.instance
                })
            return False, {"errors": errors}
        except Exception as e:
            return False, {"errors": [{"path": "root", "message": str(e)}]}

    def get_defaults(self) -> Dict[str, Any]:
        defaults = {}

        def extract_defaults(obj, path=""):
            if isinstance(obj, dict):
                if "default" in obj:
                    defaults[path] = obj["default"]
                for key, value in obj.items():
                    if key != "default":
                        new_path = f"{path}.{key}" if path else key
                        extract_defaults(value, new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    if isinstance(item, dict):
                        extract_defaults(item, f"{path}[{idx}]")

        extract_defaults(self.schema)
        return defaults

    def get_required_fields(self) -> Dict[str, list]:
        required = {}

        def extract_required(obj, path=""):
            if isinstance(obj, dict):
                if "required" in obj:
                    required[path or "root"] = obj["required"]
                for key, value in obj.items():
                    if key not in ["required", "default"]:
                        new_path = f"{path}.{key}" if path else key
                        extract_required(value, new_path)
            elif isinstance(obj, list):
                for idx, item in enumerate(obj):
                    if isinstance(item, dict):
                        extract_required(item, f"{path}[{idx}]")

        extract_required(self.schema)
        return required


def validate_project_data(data_path: Path) -> Tuple[bool, Optional[Dict[str, Any]]]:
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return False, {"errors": [{"path": "root", "message": f"File not found: {data_path}"}]}
    except json.JSONDecodeError as e:
        return False, {"errors": [{"path": "root", "message": f"Invalid JSON: {e}"}]}

    validator = ProjectSchemaValidator()
    return validator.validate(data)
