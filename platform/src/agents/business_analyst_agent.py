"""
Business Analyst Agent - Analyzes business case and cost-benefit
"""

from typing import Dict, Any, List, Optional, Tuple
from .base_agent import BaseAgent


COST_PHASES = ["planning", "infrastructure", "construction", "project_management"]


class BusinessAnalystAgent(BaseAgent):
    """
    Business Analyst Agent - Analyzes business case and cost-benefit
    
    Reads from project_data.json to determine:
    - Financial BCR (Benefit-Cost Ratio)
    - Social BCR
    - Blended BCR
    - Recommendations
    - Social benefit breakdown
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required inputs are present"""
        required_inputs = [
            "project.name",
            "project.type",
            "project.location"
        ]
        
        for path in required_inputs:
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                return False
        
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "project.name",
            "project.type",
            "project.location",
            "phases",
            "funding"
        ]
    
    def _cost_basis(self, project_data: Dict[str, Any]) -> Tuple[Optional[float], List[str]]:
        """
        Sum the phase costs that are actually known.

        Policy A7: a null phase cost is WITHHELD, not zero. When every phase is
        withheld the cost basis is unknown (None) - no ratio or verdict may be
        derived from nothing. Returns (total_cost_or_None, redacted_paths).
        """
        phases = project_data.get("phases") or {}
        redacted: List[str] = []
        known: List[float] = []

        for phase in COST_PHASES:
            value = (phases.get(phase) or {}).get("cost")
            if value is None:
                redacted.append(f"phases.{phase}.cost")
            else:
                known.append(value)

        if not known:
            return None, redacted

        contingency_percent = phases.get("contingency_percent")
        if contingency_percent is None:
            contingency_percent = 10
        return sum(known) * (1 + contingency_percent / 100), redacted

    @staticmethod
    def _fmt_ratio(value: Optional[float]) -> str:
        """Render a ratio, or the withholding itself - never a fabricated 0.00."""
        return f"{value:.2f}" if value is not None else "withheld (A7)"

    def _calculate_financial_bcr(self, project_data: Dict[str, Any],
                                 total_cost: Optional[float]) -> Dict[str, Any]:
        """Calculate financial Benefit-Cost Ratio against a known (or withheld) cost basis"""
        # Get value (from valuation or estimate)
        buildings = project_data.get("buildings", {})
        total_value = 0
        
        # Estimate value from buildings
        for home in buildings.get("homes", []):
            count = home.get("count", 0)
            bedrooms = home.get("bedrooms", 0)
            value_per_home = 350000 if bedrooms >= 3 else 250000
            total_value += count * value_per_home
        
        for dorm in buildings.get("dorms", []):
            count = dorm.get("count", 0)
            rooms = dorm.get("rooms", 0)
            total_value += count * rooms * 200000
        
        for building in buildings.get("commercial", []):
            area = building.get("area_sqm", 0)
            total_value += area * 3500
        
        # Calculate BCR - only when the cost basis is known. A withheld cost
        # basis makes the ratio Undetermined, never 0.00 and never a verdict.
        if total_cost is not None and total_cost > 0:
            bcr = total_value / total_cost
            roi = (total_value - total_cost) / total_cost * 100
            is_financially_viable = bcr >= 1.0
            assessment = "Strong" if bcr >= 1.5 else "Adequate" if bcr >= 1.0 else "Weak"
        else:
            bcr = None
            roi = None
            is_financially_viable = None
            assessment = "Undetermined"

        return {
            "total_cost": total_cost,
            "total_benefit": total_value,
            "bcr": bcr,
            "roi_percent": roi,
            "is_financially_viable": is_financially_viable,
            "assessment": assessment
        }
    
    def _calculate_social_bcr(self, project_data: Dict[str, Any],
                              total_cost: Optional[float]) -> Dict[str, Any]:
        """Calculate social Benefit-Cost Ratio against a known (or withheld) cost basis"""
        project_type = project_data.get("project", {}).get("type", "traditional")
        location = project_data.get("project", {}).get("location", "").lower()
        total_dwellings = 0
        
        for home in project_data.get("buildings", {}).get("homes", []):
            total_dwellings += home.get("count", 0)
        
        # Social benefits
        social_benefits = []
        total_social_value = 0
        
        # Housing benefit
        if project_type in ["community_housing", "social_housing"]:
            housing_benefit = total_dwellings * 15000  # Annual housing benefit per dwelling
            social_benefits.append({
                "category": "Housing",
                "description": f"Provides {total_dwellings} affordable housing units",
                "annual_value": housing_benefit,
                "type": "Economic + Social"
            })
            total_social_value += housing_benefit
        
        # Social equity benefit
        if project_type in ["community_housing", "social_housing"]:
            equity_benefit = total_dwellings * 5000
            social_benefits.append({
                "category": "Social Equity",
                "description": "Increased housing equity and social inclusion",
                "annual_value": equity_benefit,
                "type": "Social"
            })
            total_social_value += equity_benefit
        
        # Economic development benefit
        if location in ["gnowangerup", "mount_barker"]:
            economic_benefit = 500000  # Regional economic boost
            social_benefits.append({
                "category": "Economic Development",
                "description": "Stimulates local economy and employment",
                "annual_value": economic_benefit,
                "type": "Economic"
            })
            total_social_value += economic_benefit
        
        # Community health benefit
        if total_dwellings > 0:
            health_benefit = total_dwellings * 2000
            social_benefits.append({
                "category": "Community Health",
                "description": "Improved housing quality and community wellbeing",
                "annual_value": health_benefit,
                "type": "Social"
            })
            total_social_value += health_benefit
        
        # Calculate social BCR (assuming a 5-year benefit period). A withheld
        # cost basis leaves the ratio Undetermined - benefits alone can never
        # produce a ratio against a cost that was never disclosed.
        total_social_value_5yr = total_social_value * 5
        
        if total_cost is not None and total_cost > 0:
            social_bcr = total_social_value_5yr / total_cost
            is_socially_viable = social_bcr >= 1.0
            assessment = "Strong" if social_bcr >= 1.5 else "Adequate" if social_bcr >= 1.0 else "Weak"
        else:
            social_bcr = None
            is_socially_viable = None
            assessment = "Undetermined"
        
        return {
            "social_benefits": social_benefits,
            "total_annual_social_value": total_social_value,
            "total_5yr_social_value": total_social_value_5yr,
            "social_bcr": social_bcr,
            "is_socially_viable": is_socially_viable,
            "assessment": assessment
        }
    
    def _calculate_blended_bcr(self, financial: Dict[str, Any], social: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate blended BCR combining financial and social"""
        # Weighted average (60% financial, 40% social for community projects)
        financial_weight = 0.6
        social_weight = 0.4
        
        blended_bcr = None
        recommendation = "Undetermined"
        priority = "Undetermined"

        # A blended ratio needs BOTH components. One withheld component leaves
        # the blend Undetermined - never a "Do Not Recommend" built from a zero.
        if financial["bcr"] is not None and social["social_bcr"] is not None:
            blended_bcr = (financial["bcr"] * financial_weight) + (social["social_bcr"] * social_weight)

            # Determine recommendation
            if blended_bcr >= 1.5:
                recommendation = "Strongly Recommend"
                priority = "High"
            elif blended_bcr >= 1.0:
                recommendation = "Recommend with Conditions"
                priority = "Medium"
            else:
                recommendation = "Do Not Recommend"
                priority = "Low"
        
        return {
            "blended_bcr": blended_bcr,
            "financial_weight": financial_weight,
            "social_weight": social_weight,
            "recommendation": recommendation,
            "priority": priority
        }
    
    def process(self) -> Dict[str, Any]:
        """Perform business case analysis"""
        self.logger.info("Starting business case analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for business case analysis")
        
        # Get project data
        project_data = self.project_data
        project_name = project_data.get("project", {}).get("name", "Unknown")
        project_type = project_data.get("project", {}).get("type", "traditional")
        
        # Cost basis is resolved once: null phase costs are withheld (A7), not zero
        total_cost, redacted_inputs = self._cost_basis(project_data)

        # Calculate financial BCR
        financial = self._calculate_financial_bcr(project_data, total_cost)
        
        # Calculate social BCR
        social = self._calculate_social_bcr(project_data, total_cost)
        
        # Calculate blended BCR
        blended = self._calculate_blended_bcr(financial, social)

        # Data quality / honesty block (A7 doctrine: nothing looks verified that isn't)
        if redacted_inputs:
            data_quality = {
                "redacted_inputs": redacted_inputs,
                "confidence": "partial",
                "note": (
                    "Some phase costs are redacted (confidentiality policy A7). "
                    "Benefit-cost ratios need a known cost basis; where it is "
                    "withheld the ratio and recommendation are reported as "
                    "Undetermined rather than derived from zero."
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
                "name": project_name,
                "type": project_type,
                "analysis_type": "Full Business Case"
            },
            "financial_analysis": financial,
            "social_analysis": social,
            "blended_analysis": blended,
            "recommendations": {
                "overall_recommendation": blended["recommendation"],
                "priority": blended["priority"],
                "key_factors": [
                    f"Financial BCR: {self._fmt_ratio(financial['bcr'])}",
                    f"Social BCR: {self._fmt_ratio(social['social_bcr'])}",
                    f"Blended BCR: {self._fmt_ratio(blended['blended_bcr'])}",
                    f"Project Type: {project_type.title()}"
                ],
                "next_steps": [
                    "Detailed feasibility study" if blended["blended_bcr"] is None or blended["blended_bcr"] < 1.5 else "Proceed with detailed design",
                    "Stakeholder engagement" if project_type in ["community_housing", "social_housing"] else "Continue stakeholder consultation",
                    "Funding strategy development" if financial["is_financially_viable"] is None
                    else ("Funding strategy development" if financial["is_financially_viable"] else "Review funding options")
                ]
            },
            "data_quality": data_quality
        }
        
        self.logger.info(f"Business case analysis complete. Blended BCR: {self._fmt_ratio(blended['blended_bcr'])}")
        self.logger.info(f"Recommendation: {blended['recommendation']}")
        
        return self.format_output(results)