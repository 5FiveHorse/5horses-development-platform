"""
Focused null-safety tests for BusinessAnalystAgent and ValuatorAgent
=====================================================================

Policy A7 doctrine: a withheld financial input is None, never zero, and no
verdict may be derived from it. These tests pin the three states for both
agents:
  - withheld:  every financial input null -> Undetermined outputs, no invented
               rate/valuation, no "Do Not Recommend" built from zeros.
  - partial:   some cost data known -> ratios computed against the known basis,
               withholding still disclosed in data_quality.
  - full:      all inputs present -> the original arithmetic still applies.

Run with:  python -m pytest tests/test_agent_null_safety.py -v
"""
import pytest

from src.core.project_loader import ProjectLoader
from src.agents.business_analyst_agent import BusinessAnalystAgent
from src.agents.valuator_agent import ValuatorAgent


class StubLoader:
    """Minimal ProjectLoader stand-in so agents can run on synthetic data."""

    def __init__(self, data, name="synthetic"):
        self.current_project = data
        self.current_project_name = name
        from pathlib import Path
        self.projects_root = Path(".")

    def get_data(self, path):
        current = self.current_project
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current


BASE_PROJECT = {
    "project": {
        "name": "Nullable Pilot",
        "type": "community_housing",
        "location": "gnowangerup",
        "site_area_ha": 2.0,
    },
    "buildings": {
        "homes": [
            {"count": 10, "bedrooms": 3, "area_sqm": 140, "cost_per_unit": 300000},
        ],
        "dorms": [],
        "commercial": [],
    },
    "funding": {"sources": [{"source": "Grant", "amount": 4000000}]},
}

WITHHELD_DATA = {
    **BASE_PROJECT,
    "project": {
        "name": "Withheld Pilot",
        "type": "community_housing",
        "location": "gnowangerup",
        "site_area_ha": 2.0,
        "land_tenure": "peppercorn_lease",
        "land_cost": 0,
        "lease_terms": {"years_remaining": None, "annual_rent": None},
    },
    "buildings": {
        "homes": [
            {"count": 10, "bedrooms": 3, "area_sqm": 140, "cost_per_unit": None},
        ],
        "dorms": [],
        "commercial": [],
    },
    "phases": {
        "planning": {"cost": None},
        "infrastructure": {"cost": None},
        "construction": {"cost": None},
        "project_management": {"cost": None},
        "contingency_percent": 10,
    },
}

PARTIAL_DATA = {
    **WITHHELD_DATA,
    "project": {**WITHHELD_DATA["project"], "land_tenure": "freehold"},
    "phases": {
        "planning": {"cost": 1000000},
        "infrastructure": {"cost": None},
        "construction": {"cost": None},
        "project_management": {"cost": None},
        "contingency_percent": 10,
    },
}

FULL_DATA = {
    **BASE_PROJECT,
    "project": {**BASE_PROJECT["project"], "land_tenure": "freehold"},
    "phases": {
        "planning": {"cost": 100000},
        "infrastructure": {"cost": 200000},
        "construction": {"cost": 3000000},
        "project_management": {"cost": 150000},
        "contingency_percent": 10,
    },
}


def run_business_analyst(data):
    return BusinessAnalystAgent(StubLoader(data)).process()["results"]


def run_valuator(data):
    return ValuatorAgent(StubLoader(data)).process()["results"]


# ----------------------------------------------------------------------
# BusinessAnalystAgent
# ----------------------------------------------------------------------

def test_business_analyst_withheld_inputs_are_undetermined():
    results = run_business_analyst(WITHHELD_DATA)
    financial = results["financial_analysis"]
    social = results["social_analysis"]
    blended = results["blended_analysis"]

    assert financial["total_cost"] is None
    assert financial["bcr"] is None
    assert financial["is_financially_viable"] is None
    assert financial["assessment"] == "Undetermined"

    assert social["social_bcr"] is None
    assert social["is_socially_viable"] is None

    assert blended["blended_bcr"] is None
    assert blended["recommendation"] == "Undetermined"
    assert blended["priority"] == "Undetermined"

    assert "Do Not Recommend" not in str(results)
    assert "withheld (A7)" in " ".join(results["recommendations"]["key_factors"])
    assert results["data_quality"]["redacted_inputs"]
    assert results["data_quality"]["confidence"] == "partial"


def test_business_analyst_partial_inputs_compute_against_known_basis():
    results = run_business_analyst(PARTIAL_DATA)
    financial = results["financial_analysis"]

    # Only the planning phase is known: 1,000,000 + 10% contingency.
    assert financial["total_cost"] == pytest.approx(1100000)
    assert financial["bcr"] is not None and financial["bcr"] > 0
    assert financial["is_financially_viable"] is True
    assert results["blended_analysis"]["recommendation"] != "Undetermined"
    assert "phases.construction.cost" in results["data_quality"]["redacted_inputs"]


def test_business_analyst_full_inputs_keep_existing_arithmetic():
    results = run_business_analyst(FULL_DATA)
    financial = results["financial_analysis"]
    social = results["social_analysis"]

    assert financial["total_cost"] == pytest.approx(3795000)
    assert financial["bcr"] == pytest.approx(financial["total_benefit"] / 3795000)
    assert isinstance(financial["is_financially_viable"], bool)
    assert isinstance(social["social_bcr"], float)
    assert results["data_quality"]["redacted_inputs"] == []
    assert results["data_quality"]["confidence"] == "full"


# ----------------------------------------------------------------------
# ValuatorAgent
# ----------------------------------------------------------------------

def test_valuator_withheld_construction_and_lease_are_undetermined():
    results = run_valuator(WITHHELD_DATA)
    land = results["land_valuation"]
    construction = results["construction_analysis"]
    profitability = results["profitability"]

    # Peppercorn lease: no market land value is asserted.
    assert land["land_value"] is None
    assert land["rate_per_sqm"] is None

    # No project construction cost: no default rate inserted, no cost invented.
    assert construction["construction_rate_per_sqm"] is None
    assert construction["estimated_construction_cost"] is None

    assert profitability["gross_profit"] is None
    assert profitability["profit_margin_percent"] is None
    assert profitability["is_profitable"] is None
    assert profitability["confidence_level"] == "Undetermined"

    assert "phases.construction.cost" in results["data_quality"]["redacted_inputs"]
    assert "project.lease_terms" in results["data_quality"]["redacted_inputs"]


def test_valuator_partial_inputs_use_real_construction_cost():
    data = {
        **PARTIAL_DATA,
        "phases": {**PARTIAL_DATA["phases"], "construction": {"cost": 3000000}},
    }
    results = run_valuator(data)
    construction = results["construction_analysis"]

    assert construction["estimated_construction_cost"] == pytest.approx(3000000)
    assert construction["source"] == "phases.construction.cost"
    # Freehold land plus a real construction cost: profitability is computable.
    assert results["profitability"]["gross_profit"] is not None
    assert "phases.construction.cost" not in results["data_quality"]["redacted_inputs"]


def test_valuator_full_inputs_keep_existing_arithmetic():
    results = run_valuator(FULL_DATA)
    land = results["land_valuation"]
    construction = results["construction_analysis"]
    profitability = results["profitability"]

    assert land["land_value"] == pytest.approx(250 * 2.0 * 10000)
    assert construction["estimated_construction_cost"] == pytest.approx(3000000)
    assert construction["construction_rate_per_sqm"] is not None

    completed = results["completed_valuation"]["total_completed_value"]
    expected_profit = completed - land["land_value"] - construction["estimated_construction_cost"]
    assert profitability["gross_profit"] == pytest.approx(expected_profit)
    assert isinstance(profitability["is_profitable"], bool)
    assert results["data_quality"]["redacted_inputs"] == []


# ----------------------------------------------------------------------
# Real pilots
# ----------------------------------------------------------------------

@pytest.mark.parametrize("project_name", ["gnowangerup", "heritage_sanctuary"])
def test_pilot_agents_never_fabricate_financial_verdicts(project_name):
    """Both pilots withhold financials under A7; no agent may issue a verdict."""
    loader = ProjectLoader()
    loader.load_project(project_name)

    business = BusinessAnalystAgent(loader).process()["results"]
    valuation = ValuatorAgent(loader).process()["results"]

    assert business["financial_analysis"]["is_financially_viable"] is None
    assert business["blended_analysis"]["recommendation"] == "Undetermined"

    assert valuation["profitability"]["gross_profit"] is None
    assert valuation["profitability"]["is_profitable"] is None
    assert valuation["construction_analysis"]["construction_rate_per_sqm"] is None
