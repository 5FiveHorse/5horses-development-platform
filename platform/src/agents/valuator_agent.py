"""
Valuator Agent - Provides property valuation estimates
"""

from typing import Dict, Any, List, Optional, Tuple
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
    
    def _get_land_value(self, location: str, site_area_ha: float,
                        land_tenure: str) -> Dict[str, Any]:
        """
        Land value estimate.

        Market land value is only asserted for freehold land. A peppercorn /
        leasehold site is not acquired at market rate, and its leasehold interest
        cannot be valued from lease terms that are withheld (policy A7) - so the
        land value stays None instead of inventing a market parcel value.
        """
        total_area_sqm = site_area_ha * 10000

        if land_tenure != "freehold":
            return {
                "land_value": None,
                "rate_per_sqm": None,
                "total_area_sqm": total_area_sqm,
                "confidence": "Undetermined",
                "basis": (
                    f"Land held on {land_tenure}: market land value not asserted "
                    "(policy A7) - no freehold title, and the leasehold interest "
                    "is not valued from withheld lease terms."
                )
            }

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
            "confidence": confidence,
            "basis": f"Freehold land valued at ${rate}/sqm regional rate"
        }
    
    def _construction_cost_basis(self, project_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[str], List[str]]:
        """
        Resolve a construction cost basis that actually comes from the project.

        Policy A7: a withheld construction cost is unknown, not a cue to insert a
        regional default rate and derive a confident loss. Returns
        (cost_or_None, source_note_or_None, redacted_paths).
        """
        phases = project_data.get("phases") or {}
        phase_cost = (phases.get("construction") or {}).get("cost")
        if phase_cost is not None:
            return phase_cost, "phases.construction.cost", []

        redacted = ["phases.construction.cost"]

        # Real per-unit costs, used only when every building supplies one - a
        # partial set would understate the total, so it is not asserted either.
        buildings = project_data.get("buildings") or {}
        items: List[Tuple[int, Optional[float]]] = []
        for home in buildings.get("homes", []) or []:
            items.append((home.get("count", 0), home.get("cost_per_unit")))
        for dorm in buildings.get("dorms", []) or []:
            items.append((dorm.get("count", 0), dorm.get("cost_per_unit")))
        for commercial in buildings.get("commercial", []) or []:
            items.append((1, commercial.get("cost_per_unit")))

        if items and all(cost is not None for _, cost in items):
            return sum(count * cost for count, cost in items), "buildings.*.cost_per_unit", redacted

        redacted.append("buildings.*.cost_per_unit")
        return None, None, redacted
    
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
        land_tenure = (project_data.get("project", {}).get("land_tenure") or "freehold").lower()
        
        # Calculate land value (market value only asserted on freehold tenure)
        land = self._get_land_value(location, site_area_ha, land_tenure)
        
        # Estimate completed value
        completed = self._estimate_completed_value(project_data)

        # Construction cost comes from project data only - no default rate is
        # inserted to manufacture a cost where the project withheld one.
        construction_cost, construction_source, construction_redacted = self._construction_cost_basis(project_data)
        completed_area = completed["total_area_sqm"]
        construction_rate = (
            construction_cost / completed_area
            if construction_cost is not None and completed_area > 0 else None
        )

        # Gross profit needs BOTH a land value and a construction cost basis;
        # one withheld component leaves profitability Undetermined.
        if land["land_value"] is not None and construction_cost is not None:
            gross_profit = completed["total_completed_value"] - land["land_value"] - construction_cost
            profit_margin = (gross_profit / completed["total_completed_value"] * 100) if completed["total_completed_value"] > 0 else 0
            is_profitable = gross_profit > 0

            # Determine confidence level
            if location.lower() in ["perth_metro", "perth"]:
                confidence = "High"
            elif location.lower() in ["mount_barker", "gnowangerup"]:
                confidence = "Medium"
            else:
                confidence = "Low"
        else:
            gross_profit = None
            profit_margin = None
            is_profitable = None
            confidence = "Undetermined"

        # Data quality / honesty block (A7 doctrine: nothing looks verified that isn't)
        redacted_inputs = list(construction_redacted)
        lease_terms = project_data.get("project", {}).get("lease_terms") or {}
        if land["land_value"] is None and any(v is None for v in lease_terms.values()):
            redacted_inputs.append("project.lease_terms")

        if redacted_inputs:
            data_quality = {
                "redacted_inputs": redacted_inputs,
                "confidence": "partial",
                "note": (
                    "Construction cost and/or lease particulars are redacted "
                    "(confidentiality policy A7). No regional default rate is "
                    "inserted and no gross profit is asserted where the cost "
                    "basis is withheld."
                )
            }
        else:
            data_quality = {
                "redacted_inputs": [],
                "confidence": "full",
                "note": "All required inputs present."
            }
        
        results = {
            "land_valuation": {
                "land_value": land["land_value"],
                "rate_per_sqm": land["rate_per_sqm"],
                "total_area_sqm": land["total_area_sqm"],
                "confidence": land["confidence"],
                "basis": land["basis"]
            },
            "completed_valuation": {
                "total_completed_value": completed["total_completed_value"],
                "total_area_sqm": completed["total_area_sqm"],
                "value_per_sqm": completed["value_per_sqm"],
                "unit_details": completed["unit_details"]
            },
            "construction_analysis": {
                "construction_rate_per_sqm": construction_rate,
                "estimated_construction_cost": construction_cost,
                "source": construction_source or (
                    "withheld (policy A7) - no project construction cost data; "
                    "no regional rate inserted"
                )
            },
            "profitability": {
                "gross_profit": gross_profit,
                "profit_margin_percent": profit_margin,
                "is_profitable": is_profitable,
                "confidence_level": confidence
            },
            "valuation_confidence": {
                "overall_confidence": confidence,
                "factors": [
                    f"Location data: {confidence}",
                    "Valuation methodology: standard (building areas x regional value benchmarks)",
                    "Market data: benchmark table, not verified sales evidence",
                    f"Property type: {project_type}",
                    (
                        "Construction cost: withheld (policy A7) - no default rate inserted"
                        if construction_cost is None else "Construction cost: from project data"
                    )
                ]
            },
            "data_quality": data_quality
        }
        
        self.logger.info(f"Valuation complete. Total value: ${completed['total_completed_value']:,.2f}")
        if gross_profit is not None:
            self.logger.info(f"Gross profit: ${gross_profit:,.2f}")
        else:
            self.logger.info(
                "Gross profit: Undetermined (policy A7) - land and/or construction cost basis withheld"
            )
        
        return self.format_output(results)