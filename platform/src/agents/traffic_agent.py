"""
Traffic Agent - Analyzes traffic impact and requirements
"""

from typing import Dict, Any
from .base_agent import BaseAgent


class TrafficAgent(BaseAgent):
    """
    Traffic Agent - Analyzes traffic impact and requirements
    
    Reads from project_data.json to determine:
    - Trip generation
    - Traffic impact assessment requirements
    - Intersection upgrades needed
    - Access design requirements
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required traffic inputs are present"""
        # At minimum we need location
        if self.get_project_data("project.location") is None:
            self.logger.warning("Missing required input: project.location")
            return False
        return True
    
    def get_required_inputs(self) -> list:
        """Get list of required input paths"""
        return [
            "project.location",
            "project.type",
            "buildings"
        ]
    
    def _calculate_trip_generation(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trip generation based on building types"""
        total_am_trips = 0
        total_pm_trips = 0
        total_daily_trips = 0
        
        # Home trips (Residential)
        homes = project_data.get("buildings", {}).get("homes", [])
        for home in homes:
            count = home.get("count", 0)
            bedrooms = home.get("bedrooms", 0)
            
            # Trip rates per dwelling based on bedrooms
            if bedrooms >= 3:
                am_trips = 1.2  # morning peak
                pm_trips = 1.5  # afternoon peak
                daily_trips = 8.0
            else:
                am_trips = 0.8
                pm_trips = 1.0
                daily_trips = 6.0
            
            total_am_trips += am_trips * count
            total_pm_trips += pm_trips * count
            total_daily_trips += daily_trips * count
        
        # Commercial trips
        commercial = project_data.get("buildings", {}).get("commercial", [])
        for building in commercial:
            area = building.get("area_sqm", 0)
            # Retail/office trip generation rates
            if "retail" in building.get("type", "").lower():
                daily_trips = area * 0.4  # trips per sqm
                am_trips = daily_trips * 0.2
                pm_trips = daily_trips * 0.3
            else:  # office/other
                daily_trips = area * 0.3
                am_trips = daily_trips * 0.3
                pm_trips = daily_trips * 0.2
            
            total_am_trips += am_trips
            total_pm_trips += pm_trips
            total_daily_trips += daily_trips
        
        # Dorm trips
        dorms = project_data.get("buildings", {}).get("dorms", [])
        for dorm in dorms:
            count = dorm.get("count", 0)
            rooms = dorm.get("rooms", 0)
            total_rooms = count * rooms
            
            # Lower trip generation for dormitory style
            am_trips = total_rooms * 0.3
            pm_trips = total_rooms * 0.4
            daily_trips = total_rooms * 3.0
            
            total_am_trips += am_trips
            total_pm_trips += pm_trips
            total_daily_trips += daily_trips
        
        return {
            "am_peak_trips": round(total_am_trips),
            "pm_peak_trips": round(total_pm_trips),
            "daily_trips": round(total_daily_trips),
            "peak_hour": "AM" if total_am_trips > total_pm_trips else "PM"
        }
    
    def _get_traffic_requirements(self, trip_generation: Dict[str, Any], location: str) -> Dict[str, Any]:
        """Get traffic impact requirements based on trip generation"""
        daily_trips = trip_generation["daily_trips"]
        
        requirements = {
            "tia_required": False,
            "intersection_upgrades": [],
            "access_requirements": [],
            "traffic_mitigation": []
        }
        
        # Traffic Impact Assessment threshold
        if daily_trips > 200:
            requirements["tia_required"] = True
            requirements["traffic_mitigation"].append("Full Traffic Impact Assessment required")
        elif daily_trips > 100:
            requirements["tia_required"] = True
            requirements["traffic_mitigation"].append("Traffic Impact Assessment (simplified) required")
        
        # Intersection upgrades based on trip generation
        if daily_trips > 300:
            requirements["intersection_upgrades"].append("Upgrade site access intersection")
            requirements["intersection_upgrades"].append("Consider traffic signals or roundabout")
        elif daily_trips > 150:
            requirements["intersection_upgrades"].append("Sight distance improvements")
            requirements["intersection_upgrades"].append("Turning lane provision")
        elif daily_trips > 50:
            requirements["intersection_upgrades"].append("Standard site access")
        
        # Access requirements
        requirements["access_requirements"].append("Vehicle crossing to site")
        requirements["access_requirements"].append("Driveway design compliant with local government")
        
        if daily_trips > 100:
            requirements["access_requirements"].append("Separate entry and exit points")
        
        # Location-specific requirements
        if location.lower() in ["mount_barker", "gnowangerup"]:
            requirements["access_requirements"].append("Adequate parking on-site")
            if daily_trips > 100:
                requirements["access_requirements"].append("Heavy vehicle access consideration")
        
        return requirements
    
    def process(self) -> Dict[str, Any]:
        """Analyze traffic impact and requirements"""
        self.logger.info("Starting traffic analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for traffic analysis")
        
        # Get project data
        location = self.get_project_data("project.location") or "unknown"
        project_data = self.project_data
        
        # Calculate trip generation
        trip_generation = self._calculate_trip_generation(project_data)
        
        # Get traffic requirements
        traffic_requirements = self._get_traffic_requirements(trip_generation, location)
        
        # Determine access points needed
        site_area = self.get_project_data("project.site_area_ha") or 0
        if site_area > 2:
            access_points = "Multiple access points recommended"
        else:
            access_points = "Single access point sufficient"
        
        results = {
            "trip_generation": trip_generation,
            "traffic_requirements": traffic_requirements,
            "access_recommendations": {
                "access_points": access_points,
                "parking_requirement": f"Approximately {int(trip_generation['daily_trips'] * 0.8)} parking spaces required",
                "site_vehicle_movements": trip_generation["daily_trips"]
            },
            "traffic_impact_assessment": {
                "required": traffic_requirements["tia_required"],
                "complexity": "High" if trip_generation["daily_trips"] > 200 else "Medium" if trip_generation["daily_trips"] > 100 else "Low"
            }
        }
        
        self.logger.info(f"Traffic analysis complete. Daily trips: {trip_generation['daily_trips']}")
        
        return self.format_output(results)