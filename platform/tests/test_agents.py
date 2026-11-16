"""
Consolidated agent test suite - FiveHorses platform
=====================================================

Supersedes and merges: test_all_9_agents.py, test_all_agents.py, test_architect.py
(three Ox Alpha-era root-level test scripts, retired 2026-11-16 during bring-up
Gate 1 because they addressed a pre-rename project path and defined little or no
pytest-visible test functions).

Coverage preserved from the originals:
  - Each of the 9 registered agents processes the gnowangerup pilot
  - Architect agent processes heritage_sanctuary (rendering disabled)
  - Orchestrator runs selected agents and reports status
  - Both pilots load and run shared agents (dual-project check)

Grounded in the platform's own data/logic separation doctrine (B1/B2): assertions
check structure and completion, never fabricated numbers - the gnownagerup pilot's
figures are redacted (policy A7) and null amounts are legitimate, not failures.

Run with:  python -m pytest tests\\test_agents.py -v
"""
import pytest

from src.core.project_loader import ProjectLoader
from src.agents import (
    AgentOrchestrator,
    CostAgent,
    PlanningAgent,
    EnvAgent,
    TrafficAgent,
    UrbanDesignAgent,
    RiskAgent,
    ValuatorAgent,
    BusinessAnalystAgent,
    AccountantAgent,
)
from src.agents.architect_agent import ArchitectAgent

PILOT_MAIN = "gnowangerup"
PILOT_REDACTED = "heritage_sanctuary"

# (registry key, class) pairs - registry keys per the orchestrator's own
# selected-run interface (e.g. ["cost", "planning", "environmental", "traffic"]).
AGENT_SPECS = [
    ("cost", CostAgent),
    ("planning", PlanningAgent),
    ("environmental", EnvAgent),
    ("traffic", TrafficAgent),
    ("urban_design", UrbanDesignAgent),
    ("risk", RiskAgent),
    ("valuator", ValuatorAgent),
    ("business_analyst", BusinessAnalystAgent),
    ("accountant", AccountantAgent),
]


@pytest.mark.parametrize("key,agent_class", AGENT_SPECS, ids=[k for k, _ in AGENT_SPECS])
def test_single_agent_processes_pilot(key, agent_class):
    """Each registered agent must load the gnowangerup pilot and complete."""
    loader = ProjectLoader()
    loader.load_project(PILOT_MAIN)

    agent = agent_class(loader)
    result = agent.process()

    assert isinstance(result, dict), f"{key} agent returned {type(result)}"
    assert "results" in result, f"{key} agent output missing 'results' block"
    assert result["results"], f"{key} agent produced an empty results block"


def test_architect_agent_processes_redacted_pilot():
    """Architect agent on heritage_sanctuary, rendering disabled (was test_architect.py)."""
    loader = ProjectLoader()
    agent = ArchitectAgent(loader, enable_2d_rendering=False, enable_3d_rendering=False)
    agent.load_project(PILOT_REDACTED)

    output = agent.process()

    assert isinstance(output, dict)
    assert "results" in output
    assert "design_style" in output["results"]
    assert "cultural_elements" in output["results"]


def test_orchestrator_runs_selected_agents():
    """Orchestrator must run every registered agent and return one result per agent."""
    loader = ProjectLoader()
    loader.load_project(PILOT_MAIN)

    orchestrator = AgentOrchestrator(loader)
    keys = [k for k, _ in AGENT_SPECS]
    results = orchestrator.run_selected(keys)

    for key in keys:
        assert key in results, f"orchestrator result missing agent '{key}'"
        assert results[key], f"orchestrator returned empty result for '{key}'"

    statuses = orchestrator.get_agent_status()
    assert statuses, "orchestrator reported no agent statuses"


def test_shared_agents_on_both_pilots():
    """Dual-project check (preserved from test_different_projects): the shared
    agents cost, planning, environmental and traffic must process BOTH pilots -
    including the redacted one, proving null financials do not crash agents."""
    shared_keys = ["cost", "planning", "environmental", "traffic"]

    for project in (PILOT_MAIN, PILOT_REDACTED):
        loader = ProjectLoader()
        loader.load_project(project)

        orchestrator = AgentOrchestrator(loader)
        results = orchestrator.run_selected(shared_keys)

        for key in shared_keys:
            assert key in results, f"project '{project}': missing result for '{key}'"
            assert results[key], f"project '{project}': empty result for '{key}'"
