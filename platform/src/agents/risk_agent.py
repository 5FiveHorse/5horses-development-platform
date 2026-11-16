"""
Risk Agent - Analyzes project risks and creates risk registers
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class RiskAgent(BaseAgent):
    """
    Risk Agent - Analyzes project risks and creates risk registers
    
    Reads from project_data.json to identify:
    - Financial risks
    - Planning risks
    - Environmental risks
    - Construction risks
    - Market risks
    - Risk mitigation strategies
    - Contingency recommendations
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
            "project.site_area_ha",
            "phases.contingency_percent"
        ]
    
    def _identify_financial_risks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify financial risks"""
        risks = []
        
        # Get financial data
        total_cost = 0
        total_funding = 0
        
        phases = project_data.get("phases", {})
        for phase in ["planning", "infrastructure", "construction", "project_management"]:
            total_cost += phases.get(phase, {}).get("cost") or 0
        
        contingency = phases.get("contingency_percent", 10)
        total_cost *= (1 + contingency / 100)
        
        funding_sources = project_data.get("funding", {}).get("sources", [])
        total_funding = sum(s.get("amount") or 0 for s in funding_sources)
        
        funding_gap = total_cost - total_funding
        
        # Financial risk: Funding shortfall
        if funding_gap > 0:
            risks.append({
                "id": "FIN-001",
                "category": "Financial",
                "risk": "Funding Shortfall",
                "description": f"Project has a funding gap of ${funding_gap:,.2f}",
                "likelihood": "High" if funding_gap > total_cost * 0.3 else "Medium",
                "impact": "High",
                "severity": "Critical" if funding_gap > total_cost * 0.3 else "Major",
                "mitigation": [
                    "Secure additional grant funding",
                    "Reduce project scope",
                    "Phased development approach",
                    "Explore alternative funding sources"
                ]
            })
        
        # Financial risk: Cost overrun
        risks.append({
            "id": "FIN-002",
            "category": "Financial",
            "risk": "Cost Overrun",
            "description": "Construction and material costs may exceed estimates",
            "likelihood": "Medium",
            "impact": "High",
            "severity": "Major",
            "mitigation": [
                f"Maintain {contingency}% contingency buffer",
                "Fixed-price contracts with builders",
                "Regular cost monitoring and reporting",
                "Value engineering opportunities"
            ]
        })
        
        # Financial risk: Funding delays
        if len(funding_sources) < 3:
            risks.append({
                "id": "FIN-003",
                "category": "Financial",
                "risk": "Funding Source Dependency",
                "description": f"Project relies on only {len(funding_sources)} funding source(s)",
                "likelihood": "Medium",
                "impact": "High",
                "severity": "Major",
                "mitigation": [
                    "Diversify funding sources",
                    "Secure conditional approvals early",
                    "Maintain reserve funding buffer"
                ]
            })
        
        return risks
    
    def _identify_planning_risks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify planning risks"""
        risks = []
        land_tenure = project_data.get("project", {}).get("land_tenure", "freehold")
        site_description = project_data.get("project", {}).get("site_description", "").lower()
        
        # Planning risk: Rezoning
        if land_tenure in ["peppercorn_lease", "state_reserve"]:
            risks.append({
                "id": "PLN-001",
                "category": "Planning",
                "risk": "Rezoning Required",
                "description": "Land tenure requires rezoning approval",
                "likelihood": "High",
                "impact": "High",
                "severity": "Critical",
                "mitigation": [
                    "Engage planning consultant early",
                    "Prepare comprehensive rezoning application",
                    "Community engagement strategy",
                    "Allow 12-18 months for rezoning process"
                ]
            })
        
        # Planning risk: Heritage
        if "heritage" in site_description or "aboriginal" in site_description:
            risks.append({
                "id": "PLN-002",
                "category": "Planning",
                "risk": "Heritage Constraints",
                "description": "Heritage site identified requiring special approvals",
                "likelihood": "High",
                "impact": "High",
                "severity": "Critical",
                "mitigation": [
                    "Engage heritage consultant",
                    "Prepare heritage impact statement",
                    "Engage with Aboriginal Heritage Group",
                    "Design sensitive to heritage values"
                ]
            })
        
        # Planning risk: Community opposition
        if project_data.get("project", {}).get("type") in ["community_housing", "social_housing"]:
            risks.append({
                "id": "PLN-003",
                "category": "Planning",
                "risk": "Community Opposition",
                "description": "Social/community housing projects may face community resistance",
                "likelihood": "Medium",
                "impact": "Medium",
                "severity": "Moderate",
                "mitigation": [
                    "Early community engagement",
                    "Highlight community benefits",
                    "Address concerns proactively",
                    "Maintain transparent communication"
                ]
            })
        
        return risks
    
    def _identify_environmental_risks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify environmental risks"""
        risks = []
        location = project_data.get("project", {}).get("location", "").lower()
        site_description = project_data.get("project", {}).get("site_description", "").lower()
        
        # Environmental risk: Bushfire
        if location in ["mount_barker", "gnowangerup"] or "bushfire" in site_description:
            risks.append({
                "id": "ENV-001",
                "category": "Environmental",
                "risk": "Bushfire Risk",
                "description": "Site located in bushfire-prone area",
                "likelihood": "Medium",
                "impact": "High",
                "severity": "Major",
                "mitigation": [
                    "Bushfire management plan required",
                    "BAL-rated construction materials",
                    "Defensible space around buildings",
                    "Emergency access and egress planning"
                ]
            })
        
        # Environmental risk: Watercourses
        if "water" in site_description or "creek" in site_description or "river" in site_description:
            risks.append({
                "id": "ENV-002",
                "category": "Environmental",
                "risk": "Watercourse Impact",
                "description": "Site near watercourses requiring environmental assessment",
                "likelihood": "Medium",
                "impact": "Medium",
                "severity": "Moderate",
                "mitigation": [
                    "Environmental impact assessment",
                    "Buffer zones around watercourses",
                    "Sediment control during construction",
                    "Water quality monitoring"
                ]
            })
        
        # Environmental risk: Vegetation clearing
        if "remnant" in site_description or "vegetation" in site_description:
            risks.append({
                "id": "ENV-003",
                "category": "Environmental",
                "risk": "Vegetation Clearing",
                "description": "Remnant vegetation may require clearing permits",
                "likelihood": "Medium",
                "impact": "Medium",
                "severity": "Moderate",
                "mitigation": [
                    "Vegetation management plan",
                    "Retain significant trees",
                    "Offset planting requirements",
                    "Ecological survey"
                ]
            })
        
        return risks
    
    def _identify_construction_risks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify construction risks"""
        risks = []
        total_dwellings = 0
        buildings = project_data.get("buildings", {})
        
        for home in buildings.get("homes", []):
            total_dwellings += home.get("count", 0)
        
        # Construction risk: Scale and complexity
        if total_dwellings > 10:
            risks.append({
                "id": "CON-001",
                "category": "Construction",
                "risk": "Project Scale Complexity",
                "description": f"Large project with {total_dwellings} dwellings requires careful management",
                "likelihood": "Medium",
                "impact": "High",
                "severity": "Major",
                "mitigation": [
                    "Phased construction approach",
                    "Project management plan",
                    "Experienced construction manager",
                    "Regular progress monitoring"
                ]
            })
        
        # Construction risk: Labour and materials
        location = project_data.get("project", {}).get("location", "").lower()
        if location in ["gnowangerup", "mount_barker"]:
            risks.append({
                "id": "CON-002",
                "category": "Construction",
                "risk": "Regional Labour Shortage",
                "description": "Regional location may have limited construction workforce",
                "likelihood": "High",
                "impact": "Medium",
                "severity": "Major",
                "mitigation": [
                    "Engage local contractors",
                    "Staff accommodation planning",
                    "Extend construction timeline",
                    "Consider modular construction"
                ]
            })
        
        # Construction risk: Supply chain
        risks.append({
            "id": "CON-003",
            "category": "Construction",
            "risk": "Supply Chain Disruption",
            "description": "Material delivery delays may impact construction timeline",
            "likelihood": "Medium",
            "impact": "Medium",
            "severity": "Moderate",
            "mitigation": [
                "Early material ordering",
                "Multiple supplier relationships",
                "Buffer stock for critical items",
                "Flexible construction schedule"
            ]
        })
        
        return risks
    
    def _identify_market_risks(self, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify market risks"""
        risks = []
        location = project_data.get("project", {}).get("location", "").lower()
        
        # Market risk: Economic conditions
        risks.append({
            "id": "MKT-001",
            "category": "Market",
            "risk": "Economic Downturn",
            "description": "Market conditions may affect project viability",
            "likelihood": "Low",
            "impact": "High",
            "severity": "Major",
            "mitigation": [
                "Strong business case",
                "Multiple funding sources",
                "Flexible timing",
                "Conservative financial modelling"
            ]
        })
        
        # Market risk: Regional market
        if location not in ["perth", "perth_metro"]:
            risks.append({
                "id": "MKT-002",
                "category": "Market",
                "risk": "Regional Market Volatility",
                "description": "Regional property markets may be more volatile",
                "likelihood": "Medium",
                "impact": "Medium",
                "severity": "Moderate",
                "mitigation": [
                    "Market research",
                    "Staged development",
                    "Multiple exit strategies",
                    "Strong local partnerships"
                ]
            })
        
        return risks
    
    def _calculate_risk_score(self, risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall risk scores"""
        severity_counts = {
            "Critical": 0,
            "Major": 0,
            "Moderate": 0,
            "Low": 0
        }
        
        for risk in risks:
            severity = risk.get("severity", "Low")
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate weighted risk score
        weighted_score = (
            severity_counts["Critical"] * 4 +
            severity_counts["Major"] * 3 +
            severity_counts["Moderate"] * 2 +
            severity_counts["Low"] * 1
        )
        
        total_risks = len(risks)
        average_score = weighted_score / total_risks if total_risks > 0 else 0
        
        if average_score >= 3.5:
            overall_severity = "High"
        elif average_score >= 2.5:
            overall_severity = "Medium"
        else:
            overall_severity = "Low"
        
        return {
            "total_risks": total_risks,
            "severity_counts": severity_counts,
            "weighted_score": weighted_score,
            "average_score": round(average_score, 2),
            "overall_severity": overall_severity
        }
    
    def process(self) -> Dict[str, Any]:
        """Identify and assess project risks"""
        self.logger.info("Starting risk analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for risk analysis")
        
        # Get project data
        project_data = self.project_data
        
        # Identify all risks
        financial_risks = self._identify_financial_risks(project_data)
        planning_risks = self._identify_planning_risks(project_data)
        environmental_risks = self._identify_environmental_risks(project_data)
        construction_risks = self._identify_construction_risks(project_data)
        market_risks = self._identify_market_risks(project_data)
        
        all_risks = (
            financial_risks +
            planning_risks +
            environmental_risks +
            construction_risks +
            market_risks
        )
        
        # Calculate risk scores
        risk_scores = self._calculate_risk_score(all_risks)
        
        # Generate contingency recommendation
        contingency_percent = self.get_project_data("phases.contingency_percent") or 10
        recommended_contingency = min(contingency_percent + 5, 30)
        
        # Get critical risks
        critical_risks = [
            risk for risk in all_risks if risk.get("severity") in ["Critical", "Major"]
        ]
        
        results = {
            "risk_register": {
                "total_risks": len(all_risks),
                "risks": all_risks
            },
            "risk_summary": {
                "total_risks": len(all_risks),
                "by_category": {
                    "Financial": len(financial_risks),
                    "Planning": len(planning_risks),
                    "Environmental": len(environmental_risks),
                    "Construction": len(construction_risks),
                    "Market": len(market_risks)
                },
                "severity_counts": risk_scores["severity_counts"],
                "overall_risk_level": risk_scores["overall_severity"],
                "risk_score": risk_scores["average_score"]
            },
            "risk_mitigation": {
                "recommended_contingency_percent": recommended_contingency,
                "current_contingency_percent": contingency_percent,
                "contingency_gap": max(0, recommended_contingency - contingency_percent),
                "key_mitigations": [
                    risk.get("mitigation", [""])[0] for risk in all_risks[:5] if risk.get("mitigation")
                ]
            },
            "critical_risks": critical_risks
        }
        
        self.logger.info(f"Risk analysis complete. Total risks: {len(all_risks)}")
        self.logger.info(f"Overall risk level: {risk_scores['overall_severity']}")
        
        return self.format_output(results)