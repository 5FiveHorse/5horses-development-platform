"""
Environmental Agent - Analyzes environmental constraints and bushfire risk

Reads environmental constraints from the knowledge base (environmental_constraints.json)
rather than hardcoded Python conditionals. Location is normalized per the Migration
Playbook bug checklist: location.strip().lower().replace(" ", "_")
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class EnvAgent(BaseAgent):
    """
    Environmental Agent - Analyzes environmental constraints and bushfire risk
    
    Reads from project_data.json and environmental_constraints.json (knowledge base)
    to determine:
    - Environmental constraints (vegetation, watercourses, heritage)
    - BAL (Bushfire Attack Level) assessment
    - Mitigation measures
    - Recommendations for specialist assessments
    """

    def validate_inputs(self) -> bool:
        """Validate that required environmental inputs are present"""
        required_inputs = [
            "project.location",
            "project.site_area_ha"
        ]

        for path in required_inputs:
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                return False

        return True

    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "project.location",
            "project.site_area_ha",
            "project.site_description"
        ]

    # ─── Knowledge Base Helpers ───────────────────────────────────────────

    def _normalize_location(self, location: str) -> str:
        """
        Normalize location string for knowledge base lookup.
        
        Per Migration Playbook bug checklist: schema values are lowercase
        with underscores. Must normalize both sides to prevent silent
        misses on 'Mount Barker' vs 'mount_barker'.
        """
        return location.strip().lower().replace(" ", "_")

    def _get_constraints_from_kb(self, location: str) -> Dict[str, Any]:
        """
        Retrieve environmental constraints from the knowledge base.
        
        Falls back to conservative defaults if location is not found,
        ensuring unknown locations don't silently return zero-constraint output.
        """
        kb = self.knowledge.get_knowledge("environmental_constraints")
        if not kb:
            self.logger.warning("environmental_constraints.json not found in knowledge base")
            return self._get_default_constraints()

        normalized = self._normalize_location(location)
        locations = kb.get("locations", {})
        defaults = kb.get("defaults", {})

        # Try exact normalized match first
        if normalized in locations:
            self.logger.info(f"Found environmental constraints for location: {normalized}")
            return locations[normalized]

        # Try case-insensitive match as fallback
        for key, data in locations.items():
            if key.lower() == normalized:
                self.logger.info(f"Found environmental constraints for location: {key} (case-insensitive match)")
                return data

        # Fall back to defaults
        self.logger.warning(
            f"Location '{location}' (normalized: '{normalized}') not found in "
            f"environmental_constraints.json. Using conservative defaults."
        )
        return defaults

    def _get_default_constraints(self) -> Dict[str, Any]:
        """Return conservative default constraints when knowledge base is unavailable."""
        return {
            "vegetation": ["Unknown - site survey required"],
            "watercourses": ["Unknown - hydrology assessment recommended"],
            "heritage": ["Unknown - desktop heritage assessment recommended"],
            "bushfire_risk": "Unknown",
            "bal_rating": "BAL-Low",
            "bal_description": "Default to low risk pending site assessment",
            "heritage_consultant_required": True,
            "section_18_likely": False,
            "environmental_significance": "Medium",
            "notes": "Knowledge base unavailable. Default to conservative assessments."
        }

    def _get_bal_severity(self, bal_rating: str) -> int:
        """
        Get numeric severity for a BAL rating from the knowledge base scale.
        Higher = more severe. Returns 0 if BAL-Low or unknown.
        """
        kb = self.knowledge.get_knowledge("environmental_constraints")
        if not kb:
            return 0

        scale = kb.get("bal_scale", {})
        return scale.get(bal_rating, {}).get("severity", 0)

    # ─── Analysis Methods ────────────────────────────────────────────────

    def _assess_bal(self, constraints: Dict[str, Any], site_area: float) -> Dict[str, Any]:
        """
        Determine BAL assessment from knowledge base data.
        
        The BAL rating comes from the location's environmental constraints profile.
        For Perth Metro sites > 2ha with no specific constraints, upgrade from
        Low to Moderate (BAL-12.5) as larger sites may border uncleared land.
        """
        bal_rating = constraints.get("bal_rating", "BAL-Low")
        bal_description = constraints.get("bal_description", "Low risk - standard construction")

        # Large urban sites may border uncleared vegetation
        # Only escalate if the KB says Low and the site is substantial
        if bal_rating == "BAL-Low" and site_area > 2.0:
            bal_rating = "BAL-12.5"
            bal_description = "Moderate risk - large site may border uncleared land"
            self.logger.info(
                f"Upgraded BAL from Low to BAL-12.5 due to large site area ({site_area}ha)"
            )

        return {
            "rating": bal_rating,
            "description": bal_description,
            "severity": self._get_bal_severity(bal_rating)
        }

    def _derive_mitigation_measures(
        self, 
        constraints: Dict[str, Any], 
        bal: Dict[str, Any],
        site_description: str
    ) -> List[str]:
        """
        Derive mitigation measures dynamically from constraint data and BAL severity.
        
        Uses the mitigation_rules section of environmental_constraints.json to
        determine which measures apply, supplemented by site_description keyword
        detection for additional context.
        """
        measures: List[str] = []
        site_desc_lower = site_description.lower() if site_description else ""

        # --- Vegetation mitigation ---
        vegetation = constraints.get("vegetation", [])
        if vegetation:
            measures.append("Vegetation management plan required")
            # Check for remnant vegetation
            has_remnant = any("remnant" in v.lower() for v in vegetation)
            if has_remnant:
                measures.append("Retain significant trees and habitat corridors")

        # --- Watercourse mitigation ---
        watercourses = constraints.get("watercourses", [])
        water_present = any(
            w.lower() not in ["none identified", "none", "unknown - hydrology assessment recommended"]
            for w in watercourses
        ) if watercourses else False
        if water_present or "creek" in site_desc_lower or "river" in site_desc_lower:
            measures.append("Buffer zones around watercourses")
            measures.append("Sediment control during construction")

        # --- Heritage mitigation ---
        heritage = constraints.get("heritage", [])
        heritage_present = any(
            h.lower() not in ["none identified", "none", "unknown - desktop heritage assessment recommended"]
            for h in heritage
        ) if heritage else False
        if heritage_present or "heritage" in site_desc_lower or "aboriginal" in site_desc_lower:
            measures.append("Heritage impact assessment required")
            measures.append("Engage with Aboriginal Heritage Group")
            if constraints.get("section_18_likely", False):
                measures.append("Section 18 consent application required (Aboriginal Heritage Act)")

        # --- Bushfire mitigation ---
        bal_severity = bal.get("severity", 0)
        if bal_severity >= 1:
            measures.append("Ember attack protection for buildings")
            measures.append("Defensible space around structures")
            measures.append("Access for emergency vehicles")
            measures.append("Bushfire management plan")

        if bal_severity >= 4:
            measures.append("Special construction materials required")
            measures.append("Independent bushfire consultant engagement mandatory")

        return measures

    # ─── Main Process ────────────────────────────────────────────────────

    def process(self) -> Dict[str, Any]:
        """Analyze environmental constraints and risks"""
        self.logger.info("Starting environmental analysis...")

        if not self.validate_inputs():
            raise ValueError("Missing required inputs for environmental analysis")

        # Get project data
        location = self.get_project_data("project.location") or "unknown"
        site_area = self.get_project_data("project.site_area_ha") or 0
        site_description = self.get_project_data("project.site_description") or ""

        # Get constraints from knowledge base
        constraints = self._get_constraints_from_kb(location)

        # Assess BAL
        bal = self._assess_bal(constraints, site_area)

        # Derive mitigation measures
        mitigation_measures = self._derive_mitigation_measures(
            constraints, bal, site_description
        )

        # Determine environmental significance
        significance = constraints.get("environmental_significance", "Medium")
        has_heritage = any(
            h.lower() not in ["none identified", "none", "unknown - desktop heritage assessment recommended"]
            for h in constraints.get("heritage", [])
        )
        has_water = any(
            w.lower() not in ["none identified", "none", "unknown - hydrology assessment recommended"]
            for w in constraints.get("watercourses", [])
        )

        # Override significance to High if heritage or watercourses present
        if has_heritage or has_water:
            significance = "High"

        # Build recommendations
        recommendations = {
            "heritage_assessment_required": has_heritage or constraints.get("heritage_consultant_required", True),
            "environmental_impact_assessment": significance != "Low",
            "bushfire_management_plan": bal["rating"] != "BAL-Low",
            "section_18_consent": constraints.get("section_18_likely", False),
            "ecological_survey": significance != "Low",
            "hydrology_assessment": has_water or "water" in site_description.lower(),
        }

        results = {
            "environmental_assessment": {
                "constraints": {
                    "vegetation": constraints.get("vegetation", []),
                    "watercourses": constraints.get("watercourses", []),
                    "heritage": constraints.get("heritage", []),
                    "bushfire_risk": constraints.get("bushfire_risk", "Unknown"),
                    "location_notes": constraints.get("notes", "")
                },
                "bal_assessment": {
                    "rating": bal["rating"],
                    "description": bal["description"],
                    "severity_level": bal["severity"]
                },
                "site_description": site_description
            },
            "significance": {
                "heritage_present": has_heritage,
                "watercourses_present": has_water,
                "environmental_significance": significance
            },
            "mitigation_measures": mitigation_measures if mitigation_measures else [
                "Standard environmental controls apply"
            ],
            "recommendations": recommendations,
            "specialist_engagements": {
                "heritage_consultant": recommendations["heritage_assessment_required"],
                "bushfire_consultant": recommendations["bushfire_management_plan"],
                "ecologist": recommendations["ecological_survey"],
                "hydrologist": recommendations["hydrology_assessment"],
                "environmental_consultant": recommendations["environmental_impact_assessment"]
            }
        }

        self.logger.info(
            f"Environmental analysis complete. BAL: {bal['rating']}, "
            f"Significance: {significance}, "
            f"Mitigation measures: {len(mitigation_measures)}"
        )

        return self.format_output(results)