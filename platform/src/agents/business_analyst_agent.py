"""
Business Analyst Agent - Analyzes business case and cost-benefit
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


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
    
    def _calculate_financial_bcr(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate financial Benefit-Cost Ratio"""
        # Get costs
        total_cost = 0
        phases = project_data.get("phases", {})
        for phase in ["planning", "infrastructure", "construction", "project_management"]:
            total_cost += phases.get(phase, {}).get("cost", 0)
        
        contingency = phases.get("contingency_percent", 10)
        total_cost *= (1 + contingency / 100)
        
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
        
        # Calculate BCR
        if total_cost > 0:
            bcr = total_value / total_cost
        else:
            bcr = 0
        
        # Calculate ROI
        roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "total_cost": total_cost,
            "total_benefit": total_value,
            "bcr": bcr,
            "roi_percent": roi,
            "is_financially_viable": bcr >= 1.0,
            "assessment": "Strong" if bcr >= 1.5 else "Adequate" if bcr >= 1.0 else "Weak"
        }
    
    def _calculate_social_bcr(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate social Benefit-Cost Ratio"""
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
        
        # Calculate social BCR (assuming a 5-year benefit period)
        total_cost = 0
        phases = project_data.get("phases", {})
        for phase in ["planning", "infrastructure", "construction", "project_management"]:
            total_cost += phases.get(phase, {}).get("cost", 0)
        
        contingency = phases.get("contingency_percent", 10)
        total_cost *= (1 + contingency / 100)
        
        total_social_value_5yr = total_social_value * 5
        
        if total_cost > 0:
            social_bcr = total_social_value_5yr / total_cost
        else:
            social_bcr = 0
        
        return {
            "social_benefits": social_benefits,
            "total_annual_social_value": total_social_value,
            "total_5yr_social_value": total_social_value_5yr,
            "social_bcr": social_bcr,
            "is_socially_viable": social_bcr >= 1.0,
            "assessment": "Strong" if social_bcr >= 1.5 else "Adequate" if social_bcr >= 1.0 else "Weak"
        }
    
    def _calculate_blended_bcr(self, financial: Dict[str, Any], social: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate blended BCR combining financial and social"""
        # Weighted average (60% financial, 40% social for community projects)
        financial_weight = 0.6
        social_weight = 0.4
        
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
        
        # Calculate financial BCR
        financial = self._calculate_financial_bcr(project_data)
        
        # Calculate social BCR
        social = self._calculate_social_bcr(project_data)
        
        # Calculate blended BCR
        blended = self._calculate_blended_bcr(financial, social)
        
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
                    f"Financial BCR: {financial['bcr']:.2f}",
                    f"Social BCR: {social['social_bcr']:.2f}",
                    f"Blended BCR: {blended['blended_bcr']:.2f}",
                    f"Project Type: {project_type.title()}"
                ],
                "next_steps": [
                    "Detailed feasibility study" if blended["blended_bcr"] < 1.5 else "Proceed with detailed design",
                    "Stakeholder engagement" if project_type in ["community_housing", "social_housing"] else "Continue stakeholder consultation",
                    "Funding strategy development" if financial["is_financially_viable"] else "Review funding options"
                ]
            }
        }
        
        self.logger.info(f"Business case analysis complete. Blended BCR: {blended['blended_bcr']:.2f}")
        self.logger.info(f"Recommendation: {blended['recommendation']}")
        
        return self.format_output(results)