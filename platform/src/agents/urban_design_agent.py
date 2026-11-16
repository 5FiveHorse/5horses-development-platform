"""
Urban Design Agent - Analyzes masterplanning and yield
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class UrbanDesignAgent(BaseAgent):
    """
    Urban Design Agent - Analyzes masterplanning and yield
    
    Reads from project_data.json to determine:
    - Dwelling yield
    - Density analysis
    - Lot sizes
    - Product mix
    - Site layout parameters
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required inputs are present"""
        required_inputs = [
            "project.site_area_ha",
            "project.type"
        ]
        
        for path in required_inputs:
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                return False
        
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "project.site_area_ha",
            "project.type",
            "project.developable_fraction",
            "buildings"
        ]
    
    def process(self) -> Dict[str, Any]:
        """Analyze urban design and yield"""
        self.logger.info("Starting urban design analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for urban design analysis")
        
        # Get project data
        site_area = self.get_project_data("project.site_area_ha") or 0
        project_type = self.get_project_data("project.type") or "traditional"
        developable_fraction = self.get_project_data("project.developable_fraction") or 0.7
        
        # Calculate developable area
        developable_area = site_area * developable_fraction
        
        # Get building data
        buildings = self.get_project_data("buildings") or {}
        
        # Count dwellings
        homes = buildings.get("homes", [])
        total_homes = sum(h.get("count", 0) for h in homes)
        
        commercial = buildings.get("commercial", [])
        total_commercial = len(commercial)
        
        dorms = buildings.get("dorms", [])
        total_dorms = sum(d.get("count", 0) for d in dorms)
        
        total_buildings = total_homes + total_commercial + total_dorms
        
        # Calculate density
        if project_type in ["community_housing", "social_housing"]:
            if developable_area > 0:
                dwellings_per_ha = total_homes / developable_area
                # Round to nearest 10 for density code
                density_code = f"R{int(round(dwellings_per_ha / 10) * 10)}" if dwellings_per_ha > 0 else "R30"
            else:
                dwellings_per_ha = 0
                density_code = "R30"
        else:
            # Commercial density (buildings per ha)
            if site_area > 0:
                buildings_per_ha = total_buildings / site_area
            else:
                buildings_per_ha = 0
            density_code = f"Commercial {total_buildings} buildings on {site_area}ha"
        
        # Calculate product mix
        product_mix = {}
        if homes:
            for home in homes:
                home_type = home.get("type", "Unknown")
                count = home.get("count", 0)
                if home_type in product_mix:
                    product_mix[home_type] += count
                else:
                    product_mix[home_type] = count
        
        # Site layout recommendations
        layout_recommendations = []
        if total_homes > 10:
            layout_recommendations.append("Multiple housing clusters recommended")
        if total_homes > 20:
            layout_recommendations.append("Central open space recommended")
        if total_commercial > 0:
            layout_recommendations.append("Commercial frontage to main road")
        if site_area > 2:
            layout_recommendations.append("Phased development recommended")
        
        results = {
            "yield_analysis": {
                "site_area_ha": site_area,
                "developable_area_ha": round(developable_area, 2),
                "developable_fraction": developable_fraction,
                "total_homes": total_homes,
                "total_commercial_buildings": total_commercial,
                "total_dorms": total_dorms,
                "total_buildings": total_buildings
            },
            "density_analysis": {
                "density_code": density_code,
                "dwelling_density": f"{dwellings_per_ha:.1f}" if homes else "N/A"
            },
            "product_mix": product_mix,
            "site_layout": {
                "recommendations": layout_recommendations if layout_recommendations else ["Standard layout recommended"],
                "site_characteristics": {
                    "is_compact": site_area < 1,
                    "is_large": site_area > 5,
                    "mixed_use": total_homes > 0 and total_commercial > 0
                }
            }
        }
        
        self.logger.info(f"Urban design analysis complete. Homes: {total_homes}, Commercial: {total_commercial}, Total: {total_buildings}")
        
        return self.format_output(results)