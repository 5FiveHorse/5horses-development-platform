"""
FiveHorses local standalone app.

A thin FastAPI shell around the TESTED backend (ProjectLoader, BaseAgent
subclasses, Orchestrator) built and verified across this project. This does
NOT reimplement any agent logic - it only exposes the existing, tested
Orchestrator over HTTP so the dashboard (static/dashboard.html) can drive it
from a browser.

Run locally:
    pip install fastapi uvicorn --break-system-packages   (or in a venv)
    python app.py
Then open http://localhost:8000 in a browser.

Deliberately NOT included yet (see ARCHITECTURE_ASSESSMENT.md /
DEEPSEEK_SYSTEM_ASSESSMENT for why): no memory/vector store layer, no
Docker, no cloud deployment. Local-only, backend-only wiring first.
"""

from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.core.project_loader import ProjectLoader
from src.orchestrator import Orchestrator, AGENT_REGISTRY
from src.export.project_architect_export import export_to_project_architect

app = FastAPI(title="FiveHorses Platform (local)")

STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class RunRequest(BaseModel):
    project_name: str
    agent_names: Optional[list] = None
    enable_3d_rendering: bool = False
    enable_2d_rendering: bool = False
    prefer_phase_costs: bool = False


@app.get("/")
def root():
    index = STATIC_DIR / "dashboard.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "FiveHorses API running. No dashboard.html found in static/."}


@app.get("/api/projects")
def list_projects() -> Dict[str, Any]:
    """List all projects found under data/projects/."""
    loader = ProjectLoader()
    return {"projects": loader.list_projects()}


@app.get("/api/projects/{project_name}")
def get_project(project_name: str) -> Dict[str, Any]:
    """Return the raw project_data.json for one project."""
    loader = ProjectLoader()
    try:
        data = loader.load_project(project_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return data


@app.get("/api/agents")
def list_agents() -> Dict[str, Any]:
    """List agents currently registered in the Orchestrator."""
    return {"agents": list(AGENT_REGISTRY.keys())}


@app.post("/api/run")
def run_project(req: RunRequest) -> Dict[str, Any]:
    """
    Run the (tested) Orchestrator against a project. This is the same
    Orchestrator used and verified throughout this project - the API layer
    adds nothing to the calculation logic itself.
    """
    overrides = {
        "architect": {
            "enable_2d_rendering": req.enable_2d_rendering,
            "enable_3d_rendering": req.enable_3d_rendering,
        },
        "cost": {"prefer_phase_costs": req.prefer_phase_costs},
    }
    orch = Orchestrator()
    report = orch.run_project(
        req.project_name,
        agent_names=req.agent_names,
        agent_kwargs_overrides=overrides,
    )
    return report


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/projects/{project_name}/export/project-architect")
def export_project_architect(project_name: str) -> Dict[str, Any]:
    """
    Runs planning+cost+architect (if not already cached would need a fresh
    run - always runs fresh here for correctness) and maps the result into
    Project Architect's entity schemas: Project, ProjectPhase, BudgetItem,
    Deliverable, RiskItem, FundingSource, ComplianceItem.

    This is a ONE-TIME SEED export, not a live sync - see
    src/export/project_architect_export.py docstring for details and known
    limitations (risk ratings are a neutral default, cost codes are
    group-level only).
    """
    loader = ProjectLoader()
    try:
        project_data = loader.load_project(project_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    orch = Orchestrator()
    report = orch.run_project(project_name, agent_names=["planning", "cost", "architect"])
    if report.get("status") == "failed":
        raise HTTPException(status_code=500, detail=report.get("error", "Orchestrator run failed"))

    return export_to_project_architect(project_data, report)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
