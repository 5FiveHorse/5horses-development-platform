"""
Example Agent Implementation - Updated to handle multiple building types
Shows how to create a new agent that reads from project data

v1.1 (2026-11-16): Redaction-aware cost analysis, per confidentiality policy
A7. validate_inputs now distinguishes an input that is ABSENT (refuses, as
before) from one that is PRESENT BUT REDACTED (value null) - the latter no
longer blocks analysis; instead every output carries a data_quality block
naming the redacted inputs, and derived figures are labelled as floors, not
verified budgets. Null-tolerant funding summation (redacted amounts count 0,
never fabricated). Replaces the corrupted intermediate copy from the same
session. Baseline: Ox Alpha delivery record (Stage 3).
"""

import re
from typing import Dict, Any, Optional, Tuple

from .base_agent import BaseAgent


class CostAgent(BaseAgent):
    """
    Cost Agent - Analyzes project costs and feasibility

    Reads from project_data.json to calculate:
    - Total project cost
    - Revenue projections
    - Profitability metrics
    - ROI

    Supports:
    - Residential (homes)
    - Commercial
    - Mixed-use
    """

    REQUIRED_INPUTS = [
        "phases.planning.cost",
        "phases.construction.cost",
        "project.site_area_ha"
    ]

    # ------------------------------------------------------------------
    # Redaction-aware input resolution (policy A7)
    # ------------------------------------------------------------------

    def _raw_project_data(self) -> Dict[str, Any]:
        """Return the raw project dict the agent is working on."""
        data = getattr(self, "_project_data", None)
        if isinstance(data, dict) and data:
            return data
        loader = getattr(self, "project_loader", None)
        current = getattr(loader, "current_project", None) if loader is not None else None
        if isinstance(current, dict):
            return current
        return {}

    def _resolve_input(self, path: str) -> Tuple[bool, Any]:
        """
        Resolve a dotted path against the raw project data.

        Returns (present, value):
          present=False -> the key does not exist (data absent)
          present=True  -> the key exists; value may be None (REDACTED, A7)
        """
        current: Any = self._raw_project_data()
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False, None
        return True, current

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def validate_inputs(self) -> bool:
        """
        Validate that required cost inputs are present.

        An input that is absent blocks analysis. An input that exists but is
        null (redacted under policy A7) does NOT block analysis; it is
        recorded on self._redacted_inputs and flagged in the results.
        """
        self._redacted_inputs = []

        # Check if we have at least one building type
        has_homes = self.get_project_data("buildings.homes") is not None
        has_commercial = self.get_project_data("buildings.commercial") is not None
        has_dorms = self.get_project_data("buildings.dorms") is not None

        if not (has_homes or has_commercial or has_dorms):
            self.logger.warning("No building types defined")
            return False

        missing = []
        for path in self.REQUIRED_INPUTS:
            present, value = self._resolve_input(path)
            if not present:
                missing.append(path)
            elif value is None:
                self._redacted_inputs.append(path)

        if missing:
            for path in missing:
                self.logger.warning(f"Missing required input: {path}")
            return False

        if self._redacted_inputs:
            for path in self._redacted_inputs:
                self.logger.warning(
                    f"Input redacted (policy A7), proceeding with flagged partial "
                    f"analysis: {path}"
                )
        return True

    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "phases.planning.cost",
            "phases.infrastructure.cost",
            "phases.construction.cost",
            "phases.project_management.cost",
            "phases.contingency_percent",
            "project.site_area_ha"
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _count_buildings(self, building_data: Dict[str, Any]) -> tuple:
        """
        Count total buildings and calculate total area

        Returns:
            Tuple of (total_count, total_area)
        """
        total_count = 0
        total_area = 0

        # Count homes
        homes = building_data.get("homes", [])
        for home in homes:
            count = home.get("count", 0)
            area = home.get("area_sqm", 0)
            total_count += count
            total_area += count * area

        # Count dorms
        dorms = building_data.get("dorms", [])
        for dorm in dorms:
            count = dorm.get("count", 0)
            area = dorm.get("area_sqm", 0)
            total_count += count
            total_area += count * area

        # Count commercial
        commercial = building_data.get("commercial", [])
        for building in commercial:
            total_count += 1
            total_area += building.get("area_sqm", 0)

        return total_count, total_area

    def _get_building_description(self, building_data: Dict[str, Any]) -> str:
        """Get a human-readable description of buildings"""
        parts = []

        homes = building_data.get("homes", [])
        if homes:
            total_homes = sum(h.get("count", 0) for h in homes)
            parts.append(f"{total_homes} homes")

        dorms = building_data.get("dorms", [])
        if dorms:
            total_dorms = sum(d.get("count", 0) for d in dorms)
            parts.append(f"{total_dorms} dorm buildings")

        commercial = building_data.get("commercial", [])
        if commercial:
            parts.append(f"{len(commercial)} commercial buildings")

        return ", ".join(parts) if parts else "No buildings defined"

    # ------------------------------------------------------------------
    # Main analysis
    # ------------------------------------------------------------------

    def process(self) -> Dict[str, Any]:
        """
        Calculate project costs and feasibility

        Returns:
            Dictionary with cost analysis results, including a data_quality
            block when any inputs were redacted (policy A7)
        """
        self.logger.info("Starting cost analysis...")

        # Validate inputs
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for cost analysis")

        redacted = getattr(self, "_redacted_inputs", [])

        # Get phase costs (redacted/null counts as 0 - never a fabricated figure)
        planning_cost = self.get_project_data("phases.planning.cost") or 0
        infrastructure_cost = self.get_project_data("phases.infrastructure.cost") or 0
        construction_cost = self.get_project_data("phases.construction.cost") or 0
        management_cost = self.get_project_data("phases.project_management.cost") or 0
        contingency_percent = self.get_project_data("phases.contingency_percent") or 10

        # Calculate total direct costs
        direct_costs = planning_cost + infrastructure_cost + construction_cost + management_cost

        # Calculate contingency
        contingency = direct_costs * (contingency_percent / 100)

        # Total project cost
        total_cost = direct_costs + contingency

        # Get funding information (redacted amounts contribute 0)
        funding_sources = self.get_project_data("funding.sources") or []
        total_funding = sum((s.get("amount") or 0) for s in funding_sources)
        funding_gap = total_cost - total_funding

        # Get building data
        building_data = self.get_project_data("buildings") or {}
        total_buildings, total_area = self._count_buildings(building_data)
        building_description = self._get_building_description(building_data)

        # Cost per building
        cost_per_building = total_cost / total_buildings if total_buildings > 0 else 0

        # Cost per sqm
        cost_per_sqm = total_cost / total_area if total_area > 0 else 0

        # Determine project type for feasibility analysis
        project_type = self.get_project_data("project.type") or "unknown"

        # Feasibility: funding adequacy (identical check across project types;
        # redacted data means the gap is a floor, flagged below)
        is_feasible = funding_gap <= 0
        feasibility_reason = "Funding sufficient" if is_feasible else f"Funding shortfall of ${funding_gap:,.2f}"

        if redacted:
            feasibility_reason += (
                " (NOTE: some inputs redacted under policy A7 - figures are "
                "floors, not verified budgets)"
            )

        # Data quality / honesty block (A7 doctrine: nothing looks verified that isn't)
        if redacted:
            data_quality = {
                "redacted_inputs": redacted,
                "confidence": "partial",
                "note": (
                    "Some financial inputs are redacted (confidentiality policy "
                    "A7). Totals derived from them are floors, not verified "
                    "figures."
                )
            }
        else:
            data_quality = {
                "redacted_inputs": [],
                "confidence": "full",
                "note": "All required inputs present."
            }

        results = {
            "project_summary": {
                "project_type": project_type,
                "building_description": building_description,
                "total_buildings": total_buildings,
                "total_area_sqm": total_area
            },
            "cost_breakdown": {
                "planning_cost": planning_cost,
                "infrastructure_cost": infrastructure_cost,
                "construction_cost": construction_cost,
                "management_cost": management_cost,
                "contingency": contingency,
                "contingency_percent": contingency_percent,
                "direct_costs": direct_costs,
                "total_cost": total_cost
            },
            "funding_analysis": {
                "total_funding_available": total_funding,
                "funding_gap": funding_gap,
                "funding_adequacy": "adequate" if funding_gap <= 0 else "shortfall",
                "funding_sources": len(funding_sources)
            },
            "unit_metrics": {
                "building_count": total_buildings,
                "cost_per_building": cost_per_building,
                "total_area_sqm": total_area,
                "cost_per_sqm": cost_per_sqm
            },
            "feasibility": {
                "is_feasible": is_feasible,
                "reason": feasibility_reason
            },
            "data_quality": data_quality
        }

        self.logger.info(f"Cost analysis complete. Total cost: ${total_cost:,.2f}")
        self.logger.info(f"Buildings: {building_description}")
        if redacted:
            self.logger.warning(
                f"Analysis is PARTIAL - redacted inputs: {', '.join(redacted)}"
            )

        return self.format_output(results)
