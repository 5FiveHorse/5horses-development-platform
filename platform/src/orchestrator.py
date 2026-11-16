"""
Orchestrator - runs a set of agents against one project and combines
their output into a single project report.

Design goals:
- New agents plug in via AGENT_REGISTRY - no orchestrator logic changes needed
  as more agents arrive from elsewhere.
- One agent failing does not abort the run - other agents still execute,
  and the failure is recorded per-agent.
- Project-not-found / invalid project data is checked ONCE up front, so you
  get one clear error instead of the same failure repeated per agent.
- Each agent gets its own ProjectLoader instance so agents can't accidentally
  share or mutate each other's loaded state.
- Heavy/optional integrations (rendering) default OFF for batch runs -
  callers opt in per-agent via agent_kwargs_overrides.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Type

from src.core.project_loader import ProjectLoader
from src.agents.base_agent import BaseAgent
from src.agents.architect_agent import ArchitectAgent
from src.agents.planning_agent import PlanningAgent
from src.agents.cost_agent import CostAgent

logger = logging.getLogger("Orchestrator")

# Add new agents here as they arrive - nothing else in this file needs to change.
AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    "planning": PlanningAgent,
    "cost": CostAgent,
    "architect": ArchitectAgent,
}

# Safe defaults for batch/orchestrated runs. Rendering is expensive and
# depends on external services (Replicate, a running Blender instance) that
# may not be available in every environment, so it's off unless requested.
AGENT_DEFAULT_KWARGS: Dict[str, Dict[str, Any]] = {
    "architect": {"enable_2d_rendering": False, "enable_3d_rendering": False},
    "cost": {"prefer_phase_costs": False},
}


class Orchestrator:
    """Runs registered agents against a project and produces a combined report."""

    def __init__(self, projects_root: Optional[Path] = None):
        self.projects_root = projects_root

    def _new_loader(self) -> ProjectLoader:
        return ProjectLoader(self.projects_root) if self.projects_root else ProjectLoader()

    def run_project(
        self,
        project_name: str,
        agent_names: Optional[List[str]] = None,
        agent_kwargs_overrides: Optional[Dict[str, Dict[str, Any]]] = None,
        save: bool = True,
    ) -> Dict[str, Any]:
        """
        Run the given agents (default: all registered agents) against a
        project and return a combined report. Individual agent failures are
        captured, not raised - the run always returns a report.
        """
        agent_names = agent_names or list(AGENT_REGISTRY.keys())
        agent_kwargs_overrides = agent_kwargs_overrides or {}

        # Fail fast, once, if the project itself can't be loaded/validated -
        # no point running N agents just to hit the same error N times.
        try:
            probe_loader = self._new_loader()
            probe_loader.load_project(project_name)
        except Exception as e:
            logger.error(f"Cannot run orchestrator - project load failed: {e}")
            return {
                "project_name": project_name,
                "status": "failed",
                "error": f"Project could not be loaded: {e}",
                "results": {},
                "errors": {},
                "timing_seconds": {},
            }

        run_report: Dict[str, Any] = {
            "project_name": project_name,
            "agents_run": agent_names,
            "results": {},
            "errors": {},
            "timing_seconds": {},
        }

        for name in agent_names:
            if name not in AGENT_REGISTRY:
                msg = f"Unknown agent '{name}' - not in AGENT_REGISTRY"
                run_report["errors"][name] = msg
                logger.warning(msg)
                continue

            agent_cls = AGENT_REGISTRY[name]
            kwargs = {**AGENT_DEFAULT_KWARGS.get(name, {}), **agent_kwargs_overrides.get(name, {})}

            start = time.time()
            try:
                loader = self._new_loader()
                loader.load_project(project_name)
                agent = agent_cls(loader, **kwargs)
                output = agent.process()
                run_report["results"][name] = output
                logger.info(f"[{name}] completed in {time.time() - start:.2f}s")
            except Exception as e:
                run_report["errors"][name] = str(e)
                logger.error(f"[{name}] failed: {e}")
            finally:
                run_report["timing_seconds"][name] = round(time.time() - start, 2)

        if not run_report["errors"]:
            run_report["status"] = "success"
        elif run_report["results"]:
            run_report["status"] = "partial"
        else:
            run_report["status"] = "failed"

        run_report["summary"] = self._build_summary(run_report["results"])

        if save:
            self._save_report(project_name, run_report)

        return run_report

    def _build_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pulls a few headline numbers out of whichever agents actually ran,
        for a quick at-a-glance view. Tolerant of any agent being absent
        (not every project needs every agent, and any agent may have failed).
        """
        summary: Dict[str, Any] = {}

        planning = results.get("planning", {}).get("results")
        if planning:
            summary["approval_pathway"] = planning.get("approval_requirements", {}).get("pathway")
            summary["planning_timeline_months"] = planning.get("approval_requirements", {}).get(
                "estimated_timeline_months"
            )
            summary["rezoning_required"] = planning.get("planning_summary", {}).get("rezoning_required")

        cost = results.get("cost", {}).get("results")
        if cost:
            fp = cost.get("funded_phase", {})
            summary["total_cost_calculated"] = fp.get("cost_breakdown", {}).get("total_cost")
            summary["total_tenancies"] = fp.get("total_tenancies")
            summary["home_sale_units_counted"] = fp.get("revenue", {}).get("homes_counted_for_revenue")
            summary["feasibility_viable"] = fp.get("feasibility", {}).get("is_viable")
            summary["profit_margin_percent"] = fp.get("feasibility", {}).get("profit_margin_percent")
            validation = fp.get("phase_cost_validation", {})
            if validation.get("flagged"):
                summary.setdefault("flags", []).append(
                    f"Cost variance vs phase assumptions: {validation.get('variance_percent')}%"
                )
            sp = cost.get("full_subdivision_potential", {})
            if sp:
                summary["subdivision_potential_yield"] = sp.get("potential_yield")

        architect = results.get("architect", {}).get("results")
        if architect:
            summary["design_style"] = architect.get("design_style")
            summary["building_designs_count"] = len(architect.get("designs", []))
            summary["drawings_count"] = len(architect.get("drawing_register", []))

        return summary

    def _save_report(self, project_name: str, report: Dict[str, Any]) -> Path:
        loader = self._new_loader()
        output_dir = loader.projects_root / project_name / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / "project_report.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"Saved combined report to {path}")
        return path


def run_project(project_name: str, **kwargs) -> Dict[str, Any]:
    """Convenience function: Orchestrator().run_project(project_name, ...)"""
    return Orchestrator().run_project(project_name, **kwargs)


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

    project = sys.argv[1] if len(sys.argv) > 1 else "gnowangerup"
    report = run_project(project)
    print(json.dumps(report["summary"], indent=2))
    print(f"\nStatus: {report['status']}")
    if report["errors"]:
        print(f"Errors: {report['errors']}")
