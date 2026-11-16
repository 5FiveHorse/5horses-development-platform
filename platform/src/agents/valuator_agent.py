"""
Valuator Agent - Provides property valuation estimates
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class ValuatorAgent(BaseAgent):
    """
    Valuator Agent - Provides property valuation estimates
    
    Reads from project_data.json to determine:
    - Land value
    - Completed project value
    - Value per sqm
    - Confidence level
    - Comparable sales analysis
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required inputs are present"""
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
            "project.type",
            "buildings"
        ]
    
    def _get_land_value(self, location: str, site_area_ha: float) -> Dict[str, Any]:
        """Get land value based on location"""
        # Base land rates by region (per sqm)
        land_rates = {
            "perth_metro": 1006,
            "perth": 1006,
            "mount_barker": 300,
            "gnowangerup": 250,
            "great_southern": 350
        }
        
        # Get rate for location
        rate = land_rates.get(location.lower(), 350)  # Default to regional rate
        
        # Calculate total land value
        total_area_sqm = site_area_ha * 10000
        land_value = rate * total_area_sqm
        
        # Adjust for location characteristics
        if location.lower() in ["mount_barker", "gnowangerup"]:
            confidence = "Medium"  # Regional data may be less robust
        else:
            confidence = "High"
        
        return {
            "land_value": land_value,
            "rate_per_sqm": rate,
            "total_area_sqm": total_area_sqm,
            "confidence": confidence
        }
    
    def _get_construction_rate(self, location: str, project_type: str) -> float:
        """Get construction rate per sqm based on location and type"""
        base_rates = {
            "perth_metro": 1100,
            "perth": 1100,
            "mount_barker": 1250,
            "gnowangerup": 1200,
            "great_southern": 1200
        }
        
        rate = base_rates.get(location.lower(), 1200)
        
        # Adjust for project type
        if project_type in ["community_housing", "social_housing"]:
            rate *= 0.95  # Slightly lower cost for social housing
        elif project_type == "commercial":
            rate *= 1.15  # Higher cost for commercial
        
        return rate
    
    def _estimate_completed_value(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate completed project value"""
        buildings = project_data.get("buildings", {})
        location = project_data.get("project", {}).get("location", "unknown")
        project_type = project_data.get("project", {}).get("type", "traditional")
        
        total_area = 0
        total_value = 0
        unit_details = []
        
        # Value homes
        for home in buildings.get("homes", []):
            count = home.get("count", 0)
            area = home.get("area_sqm", 0)
            bedrooms = home.get("bedrooms", 0)
            
            # Estimate sale price based on bedrooms
            if bedrooms >= 3:
                sale_price = 420000
            elif bedrooms >= 2:
                sale_price = 350000
            else:
                sale_price = 280000
            
            # Adjust for location
            if location.lower() in ["perth_metro", "perth"]:
                sale_price *= 1.5
            elif location.lower() in ["mount_barker", "gnowangerup"]:
                sale_price *= 0.9  # Regional discount
            
            total_value += count * sale_price
            total_area += count * area
            unit_details.append({
                "type": home.get("type", "home"),
                "count": count,
                "area_sqm": area,
                "estimated_value": sale_price
            })
        
        # Value commercial
        for building in buildings.get("commercial", []):
            area = building.get("area_sqm", 0)
            
            # Commercial value rates
            if "retail" in building.get("type", "").lower():
                value_per_sqm = 4500
            elif "office" in building.get("type", "").lower():
                value_per_sqm = 4000
            else:
                value_per_sqm = 3500
            
            building_value = area * value_per_sqm
            total_value += building_value
            total_area += area
            unit_details.append({
                "type": building.get("name", "commercial"),
                "count": 1,
                "area_sqm": area,
                "estimated_value": building_value
            })
        
        # Value dorms
        for dorm in buildings.get("dorms", []):
            count = dorm.get("count", 0)
            rooms = dorm.get("rooms", 0)
            area = dorm.get("area_sqm", 0)
            
            dorm_value = rooms * 200000  # Per room valuation
            total_value += count * dorm_value
            total_area += count * area
            unit_details.append({
                "type": "dormitory",
                "count": count,
                "area_sqm": area,
                "estimated_value": dorm_value
            })
        
        return {
            "total_completed_value": total_value,
            "total_area_sqm": total_area,
            "value_per_sqm": total_value / total_area if total_area > 0 else 0,
            "unit_details": unit_details
        }
    
    def process(self) -> Dict[str, Any]:
        """Perform property valuation analysis"""
        self.logger.info("Starting valuation analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for valuation analysis")
        
        # Get project data
        project_data = self.project_data
        location = project_data.get("project", {}).get("location", "unknown")
        site_area_ha = project_data.get("project", {}).get("site_area_ha", 0)
        project_type = project_data.get("project", {}).get("type", "traditional")
        
        # Calculate land value
        land = self._get_land_value(location, site_area_ha)
        
        # Estimate completed value
        completed = self._estimate_completed_value(project_data)
        
        # Calculate gross profit
        construction_rate = self._get_construction_rate(location, project_type)
        construction_cost = completed["total_area_sqm"] * construction_rate if completed["total_area_sqm"] > 0 else 0
        
        gross_profit = completed["total_completed_value"] - land["land_value"] - construction_cost
        
        # Determine confidence level
        if location.lower() in ["perth_metro", "perth"]:
            confidence = "High"
        elif location.lower() in ["mount_barker", "gnowangerup"]:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        results = {
            "land_valuation": {
                "land_value": land["land_value"],
                "rate_per_sqm": land["rate_per_sqm"],
                "total_area_sqm": land["total_area_sqm"],
                "confidence": land["confidence"]
            },
            "completed_valuation": {
                "total_completed_value": completed["total_completed_value"],
                "total_area_sqm": completed["total_area_sqm"],
                "value_per_sqm": completed["value_per_sqm"],
                "unit_details": completed["unit_details"]
            },
            "construction_analysis": {
                "construction_rate_per_sqm": construction_rate,
                "estimated_construction_cost": construction_cost
            },
            "profitability": {
                "gross_profit": gross_profit,
                "profit_margin_percent": (gross_profit / completed["total_completed_value"] * 100) if completed["total_completed_value"] > 0 else 0,
                "is_profitable": gross_profit > 0,
                "confidence_level": confidence
            },
            "valuation_confidence": {
                "overall_confidence": confidence,
                "factors": [
                    f"Location data: {confidence}",
                    f"Valuation methodology: Standard",
                    f"Market data: {confidence}",
                    f"Property type: {confidence}"
                ]
            }
        }
        
        self.logger.info(f"Valuation complete. Total value: ${completed['total_completed_value']:,.2f}")
        self.logger.info(f"Gross profit: ${gross_profit:,.2f}")
        
        return self.format_output(results)