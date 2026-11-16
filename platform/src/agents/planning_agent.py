"""
Planning Agent - Analyzes planning requirements and approvals
"""

import re
from typing import Dict, Any, Optional
from src.agents.base_agent import BaseAgent


class PlanningAgent(BaseAgent):
    """
    Planning Agent - Analyzes planning requirements and approval pathways
    
    Reads from project_data.json to determine:
    - Zoning and density analysis
    - WAPC approval pathway
    - Required documentation
    - Approval timeline
    - R-Code compliance and permitted subdivision yield (via knowledge/r_codes.json)
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required planning inputs are present"""
        required_inputs = [
            "project.location",
            "project.site_area_ha",
            "project.type"
        ]
        
        for path in required_inputs:
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                return False
        
        return True
    
    def _extract_r_code(self, zoning_string: str) -> Optional[str]:
        """Pulls an 'R30'-style code out of a zoning string like 'R30 - Low Density Residential'."""
        if not zoning_string:
            return None
        match = re.search(r"R\d+(\.\d+)?", zoning_string)
        return match.group(0) if match else None

    def _check_r_code_compliance(self, zoning_string: str, developable_area_ha: float) -> Dict[str, Any]:
        """
        Looks up the project's R-Code in knowledge/r_codes.json and reports
        density, minimum lot size, and the permitted subdivision yield for
        the developable area under that code. Returns an "unavailable" note
        rather than fabricated numbers if the code isn't recognized or the
        knowledge file isn't loaded.
        """
        code = self._extract_r_code(zoning_string)
        if not code:
            return {"available": False, "note": f"No R-Code found in zoning string '{zoning_string}'."}

        r_codes = self.knowledge.get_knowledge("r_codes")
        if not r_codes:
            return {"available": False, "note": "knowledge/r_codes.json not loaded."}

        code_data = r_codes.get("codes", {}).get(code.upper())
        if not code_data:
            return {"available": False, "note": f"R-Code '{code}' not found in knowledge/r_codes.json."}

        permitted_yield = int(developable_area_ha * code_data["density"])

        return {
            "available": True,
            "code": code.upper(),
            "density_dwellings_per_ha": code_data["density"],
            "min_lot_size_sqm": code_data["min_lot_size_sqm"],
            "max_dwellings_per_lot": code_data["max_dwellings"],
            "min_frontage_m": code_data["min_frontage"],
            "description": code_data["description"],
            "permitted_subdivision_yield": permitted_yield,
            "note": (
                f"Under {code.upper()}, the {developable_area_ha:.2f}ha developable area "
                f"could yield up to {permitted_yield} lots at minimum {code_data['min_lot_size_sqm']}sqm each. "
                "This is the maximum PERMITTED yield under current zoning, not what's funded/proposed - "
                "compare against CostAgent's full_subdivision_potential for the matching cost/revenue estimate."
            ),
        }

    def _generate_da_conditions(self, project_type: str, rezoning_required: bool,
                                 is_cultural_project: bool) -> list:
        """
        A starting checklist of standard DA conditions/referrals likely to
        apply, based on project type and known flags. This is a planning
        starting point, not a substitute for a town planner's actual
        conditions assessment - flagged as such in the output.
        """
        conditions = [
            "Compliance with approved site plan and building envelope",
            "Landscaping to be completed prior to occupancy",
        ]
        if rezoning_required:
            conditions.append("Rezoning/structure plan amendment to be finalised prior to DA determination")
        if project_type in ("community_housing", "social_housing"):
            conditions.append("Compliance with Department of Communities social housing design guidelines")
        if project_type == "commercial":
            conditions.append("Traffic Impact Assessment conditions (access, parking, signage)")
        if is_cultural_project:
            conditions.append("Aboriginal Cultural Heritage Survey / Section 18 consent to be obtained prior to any ground disturbance")
            conditions.append("Cultural Heritage Management Plan conditions to be observed during construction")
        return conditions

    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "project.location",
            "project.site_area_ha",
            "project.type",
            "project.land_tenure"
        ]
    
    def _get_planning_requirements(self, project_type: str, location: str) -> Dict[str, Any]:
        """Get planning requirements based on project type and location"""
        # Base requirements for all projects
        requirements = {
            "required_docs": [],
            "referrals": [],
            "estimated_timeline_months": 0,
            "complexity": "standard"
        }
        
        # Type-specific requirements
        if project_type in ["community_housing", "social_housing"]:
            requirements["required_docs"] = [
                "Development Application",
                "Site Plan",
                "Floor Plans",
                "Elevations",
                "Landscape Plan",
                "Community Engagement Report"
            ]
            requirements["referrals"] = [
                "WAPC",
                "Department of Communities",
                "Local Government"
            ]
            requirements["estimated_timeline_months"] = 9
            requirements["complexity"] = "high"
            
        elif project_type == "commercial":
            requirements["required_docs"] = [
                "Development Application",
                "Site Plan",
                "Floor Plans",
                "Elevations",
                "Traffic Impact Assessment",
                "Environmental Assessment"
            ]
            requirements["referrals"] = [
                "WAPC",
                "Main Roads WA",
                "Department of Planning"
            ]
            requirements["estimated_timeline_months"] = 12
            requirements["complexity"] = "high"
            
        else:  # traditional
            requirements["required_docs"] = [
                "Development Application",
                "Site Plan",
                "Floor Plans",
                "Elevations"
            ]
            requirements["referrals"] = ["Local Government"]
            requirements["estimated_timeline_months"] = 6
            requirements["complexity"] = "standard"
        
        # Location-specific requirements
        if location.lower() in ["perth", "perth_metro"]:
            requirements["referrals"].append("Metropolitan Redevelopment Authority")
            requirements["complexity"] = "high"
        
        return requirements
    
    def process(self) -> Dict[str, Any]:
        """Analyze planning requirements and approval pathway"""
        self.logger.info("Starting planning analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for planning analysis")
        
        # Get project data
        project_type = self.get_project_data("project.type") or "traditional"
        location = self.get_project_data("project.location") or "unknown"
        site_area = self.get_project_data("project.site_area_ha") or 0
        land_tenure = self.get_project_data("project.land_tenure") or "freehold"
        
        # Get planning requirements
        requirements = self._get_planning_requirements(project_type, location)
        
        # Determine zoning based on location (simplified) - overridden by
        # explicit project.rezoning.current_zoning when the project data
        # provides one.
        zoning = {
            "gnowangerup": "R30 - Low Density Residential",
            "mount_barker": "R20 - Rural Residential",
            "perth_metro": "R60 - Medium Density Residential"
        }.get(location.lower(), "R30 - General Residential")

        # Determine if rezoning is required. Prefer an explicit
        # project.rezoning.required field when the project data provides
        # one (more accurate than inference) - fall back to the land_tenure
        # proxy only when no explicit rezoning data exists.
        explicit_rezoning = self.get_project_data("project.rezoning")
        proposed_zoning = None
        if explicit_rezoning is not None and "required" in explicit_rezoning:
            rezoning_required = explicit_rezoning["required"]
            if explicit_rezoning.get("current_zoning"):
                zoning = explicit_rezoning["current_zoning"]
            proposed_zoning = explicit_rezoning.get("proposed_zoning")
        else:
            rezoning_required = land_tenure in ["peppercorn_lease", "state_reserve"]
        
        # Calculate developable area
        developable_fraction = self.get_project_data("project.developable_fraction") or 0.7
        developable_area = site_area * developable_fraction
        
        # Determine approval pathway
        if project_type in ["community_housing", "social_housing"]:
            pathway = "WAPC Assessment + Ministerial Approval"
        elif rezoning_required:
            pathway = "Rezoning + WAPC Assessment"
        elif project_type == "commercial":
            pathway = "WAPC Assessment + Local Government"
        else:
            pathway = "Local Government Assessment"
        
        results = {
            "planning_summary": {
                "zoning": zoning,
                "proposed_zoning": proposed_zoning,
                "land_tenure": land_tenure,
                "developable_area_ha": round(developable_area, 2),
                "developable_fraction": developable_fraction,
                "rezoning_required": rezoning_required
            },
            "r_code_compliance": self._check_r_code_compliance(zoning, developable_area),
            "approval_requirements": {
                "pathway": pathway,
                "required_documentation": requirements["required_docs"],
                "referrals": requirements["referrals"],
                "estimated_timeline_months": requirements["estimated_timeline_months"],
                "complexity": requirements["complexity"]
            },
            "likely_da_conditions": self._generate_da_conditions(
                project_type, rezoning_required,
                is_cultural_project=(project_type in ("community_housing", "social_housing")),
            ),
            "risk_factors": {
                "rezoning_risk": "High" if rezoning_required else "Low",
                "complexity_risk": requirements["complexity"],
                "timeline_risk": "High" if requirements["estimated_timeline_months"] > 9 else "Medium"
            }
        }
        
        self.logger.info(f"Planning analysis complete. Pathway: {pathway}")
        
        return self.format_output(results)