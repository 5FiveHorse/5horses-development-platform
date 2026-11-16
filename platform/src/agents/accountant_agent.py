"""
Accountant Agent - Analyzes funding structures and financial strategy
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent


class AccountantAgent(BaseAgent):
    """
    Accountant Agent - Analyzes funding structures and financial strategy
    
    Reads from project_data.json to determine:
    - Funding structure
    - Debt/equity ratio
    - Interest costs
    - Fees
    - Financial sustainability
    """
    
    def validate_inputs(self) -> bool:
        """Validate that required inputs are present"""
        required_inputs = [
            "project.name",
            "funding.sources"
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
            "funding.sources",
            "phases"
        ]
    
    def _analyze_funding_sources(self, funding_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze funding sources and structure"""
        total_funding = sum(s.get("amount", 0) for s in funding_sources)
        
        # Categorize funding types
        grants = []
        loans = []
        equity = []
        government = []
        philanthropic = []
        
        for source in funding_sources:
            name = source.get("source", "").lower()
            amount = source.get("amount", 0)
            
            if "grant" in name:
                grants.append({"source": name, "amount": amount})
            elif "loan" in name:
                loans.append({"source": name, "amount": amount})
            elif "equity" in name or "investment" in name:
                equity.append({"source": name, "amount": amount})
            elif "government" in name:
                government.append({"source": name, "amount": amount})
            elif "philanthropic" in name or "foundation" in name:
                philanthropic.append({"source": name, "amount": amount})
            else:
                # Default to government/grants for unknown sources
                government.append({"source": name, "amount": amount})
        
        # Calculate percentages
        grant_percent = (sum(g["amount"] for g in grants) / total_funding * 100) if total_funding > 0 else 0
        loan_percent = (sum(l["amount"] for l in loans) / total_funding * 100) if total_funding > 0 else 0
        equity_percent = (sum(e["amount"] for e in equity) / total_funding * 100) if total_funding > 0 else 0
        government_percent = (sum(g["amount"] for g in government) / total_funding * 100) if total_funding > 0 else 0
        philanthropic_percent = (sum(p["amount"] for p in philanthropic) / total_funding * 100) if total_funding > 0 else 0
        
        # Determine funding model
        if grant_percent > 50:
            model = "Grant-Dependent"
        elif loan_percent > 50:
            model = "Loan-Financed"
        elif government_percent > 50:
            model = "Government-Funded"
        elif philanthropic_percent > 40:
            model = "Philanthropic"
        else:
            model = "Mixed-Funding"
        
        return {
            "total_funding": total_funding,
            "funding_sources": funding_sources,
            "funding_breakdown": {
                "grants": grants,
                "loans": loans,
                "equity": equity,
                "government": government,
                "philanthropic": philanthropic
            },
            "funding_percentages": {
                "grants": grant_percent,
                "loans": loan_percent,
                "equity": equity_percent,
                "government": government_percent,
                "philanthropic": philanthropic_percent
            },
            "funding_model": model,
            "source_count": len(funding_sources)
        }
    
    def _calculate_financial_metrics(self, project_data: Dict[str, Any], funding_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate key financial metrics"""
        # Get total cost
        total_cost = 0
        phases = project_data.get("phases", {})
        for phase in ["planning", "infrastructure", "construction", "project_management"]:
            total_cost += phases.get(phase, {}).get("cost", 0)
        
        contingency = phases.get("contingency_percent", 10)
        total_cost *= (1 + contingency / 100)
        
        total_funding = funding_analysis["total_funding"]
        funding_gap = total_cost - total_funding
        
        # Calculate debt-to-equity ratio
        debt = sum(l["amount"] for l in funding_analysis["funding_breakdown"]["loans"])
        equity = sum(e["amount"] for e in funding_analysis["funding_breakdown"]["equity"])
        
        if debt > 0 and equity > 0:
            debt_to_equity = debt / equity
        elif debt > 0:
            debt_to_equity = float('inf')
        else:
            debt_to_equity = 0
        
        # Calculate total interest (assuming 5% interest on loans)
        interest_rate = 0.05
        total_interest = debt * interest_rate
        
        # Calculate fees (1-2% of total funding)
        funding_fees = total_funding * 0.015
        
        return {
            "total_project_cost": total_cost,
            "total_funding_available": total_funding,
            "funding_gap": funding_gap,
            "debt_to_equity_ratio": debt_to_equity,
            "total_interest": total_interest,
            "funding_fees": funding_fees,
            "total_financing_cost": total_interest + funding_fees,
            "net_funding_available": total_funding - (total_interest + funding_fees)
        }
    
    def _analyze_risk(self, financial_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial risks"""
        risks = []
        
        # Funding gap risk
        if financial_metrics["funding_gap"] > 0:
            risks.append({
                "risk": "Funding Shortfall",
                "severity": "High" if financial_metrics["funding_gap"] > financial_metrics["total_project_cost"] * 0.3 else "Medium",
                "description": f"Project has a funding gap of ${financial_metrics['funding_gap']:,.2f}"
            })
        
        # Debt risk
        if financial_metrics["debt_to_equity_ratio"] > 2:
            risks.append({
                "risk": "High Debt Exposure",
                "severity": "High",
                "description": f"Debt-to-equity ratio of {financial_metrics['debt_to_equity_ratio']:.1f}% exceeds recommended levels"
            })
        
        # Financing cost risk
        if financial_metrics["total_financing_cost"] > financial_metrics["total_project_cost"] * 0.1:
            risks.append({
                "risk": "High Financing Costs",
                "severity": "Medium",
                "description": f"Financing costs of ${financial_metrics['total_financing_cost']:,.2f} are significant"
            })
        
        # Debt service capacity
        if financial_metrics["total_interest"] > 0:
            risks.append({
                "risk": "Interest Service Capacity",
                "severity": "Medium",
                "description": "Ongoing interest payments require strong operational revenue"
            })
        
        return {
            "risks": risks,
            "risk_count": len(risks),
            "overall_financial_risk": "High" if len(risks) >= 3 else "Medium" if len(risks) >= 1 else "Low"
        }
    
    def process(self) -> Dict[str, Any]:
        """Analyze funding structure and financial strategy"""
        self.logger.info("Starting financial analysis...")
        
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for financial analysis")
        
        # Get project data
        project_data = self.project_data
        funding_sources = project_data.get("funding", {}).get("sources", [])
        project_type = project_data.get("project", {}).get("type", "traditional")
        
        # Analyze funding sources
        funding_analysis = self._analyze_funding_sources(funding_sources)
        
        # Calculate financial metrics
        financial_metrics = self._calculate_financial_metrics(project_data, funding_analysis)
        
        # Analyze financial risks
        risk_analysis = self._analyze_risk(financial_metrics)
        
        # Determine financial sustainability score (1-100)
        sustainability_score = 0
        
        # Score based on funding gap
        if financial_metrics["funding_gap"] <= 0:
            sustainability_score += 30
        elif financial_metrics["funding_gap"] < financial_metrics["total_project_cost"] * 0.1:
            sustainability_score += 20
        elif financial_metrics["funding_gap"] < financial_metrics["total_project_cost"] * 0.3:
            sustainability_score += 10
        
        # Score based on debt-to-equity
        if financial_metrics["debt_to_equity_ratio"] <= 1:
            sustainability_score += 25
        elif financial_metrics["debt_to_equity_ratio"] <= 2:
            sustainability_score += 15
        elif financial_metrics["debt_to_equity_ratio"] <= 3:
            sustainability_score += 5
        
        # Score based on funding diversity
        if funding_analysis["source_count"] >= 4:
            sustainability_score += 25
        elif funding_analysis["source_count"] >= 2:
            sustainability_score += 15
        elif funding_analysis["source_count"] >= 1:
            sustainability_score += 5
        
        # Score based on grant component
        if funding_analysis["funding_percentages"]["grants"] > 30:
            sustainability_score += 20
        elif funding_analysis["funding_percentages"]["grants"] > 10:
            sustainability_score += 10
        
        results = {
            "funding_structure": {
                "funding_model": funding_analysis["funding_model"],
                "funding_breakdown": funding_analysis["funding_percentages"],
                "source_count": funding_analysis["source_count"],
                "funding_sources": [
                    f"{s.get('source', 'Unknown')}: ${s.get('amount', 0):,.2f}" 
                    for s in funding_analysis["funding_sources"]
                ]
            },
            "financial_metrics": financial_metrics,
            "financial_risk": risk_analysis,
            "sustainability": {
                "score": min(sustainability_score, 100),
                "rating": "Excellent" if sustainability_score >= 80 else "Good" if sustainability_score >= 60 else "Fair" if sustainability_score >= 40 else "Poor",
                "recommendations": [
                    "Secure additional funding" if financial_metrics["funding_gap"] > 0 else "Funding adequate",
                    "Reduce debt exposure" if financial_metrics["debt_to_equity_ratio"] > 2 else "Debt levels manageable",
                    "Diversify funding sources" if funding_analysis["source_count"] < 3 else "Good funding diversity",
                    "Consider contingency funding" if financial_metrics["funding_gap"] < 0 else "Review contingency levels"
                ]
            }
        }
        
        self.logger.info(f"Financial analysis complete. Sustainability score: {sustainability_score}")
        self.logger.info(f"Funding model: {funding_analysis['funding_model']}")
        
        return self.format_output(results)