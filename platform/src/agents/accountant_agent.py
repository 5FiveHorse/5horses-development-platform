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

    v1.2 (2026-11-17): aligned with the CostAgent A7 doctrine. A null phase
    cost or funding amount is WITHHELD, not zero - totals, the funding gap,
    the debt/equity ratio and the sustainability score stay None when the
    inputs behind them are withheld, and the funding model / risk level /
    rating report "Undetermined" instead of a fabricated verdict.
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
    
    @staticmethod
    def _sum_known(values: List[Any]):
        """Sum the values that are present. A7: null is withheld, not zero."""
        known = [v for v in values if v is not None]
        return sum(known) if known else None

    @staticmethod
    def _percent(amount, total):
        """Share of the total, or None when either side is withheld."""
        if amount is None or total is None or total <= 0:
            return None
        return amount / total * 100

    @staticmethod
    def _money(value) -> str:
        """Format an amount, naming withheld figures instead of inventing $0.00."""
        return f"${value:,.2f}" if isinstance(value, (int, float)) else "withheld"

    def _analyze_funding_sources(self, funding_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze funding sources and structure"""
        # A null amount is withheld (policy A7) - it is not a $0 contribution.
        total_funding = self._sum_known([s.get("amount") for s in funding_sources])
        
        # Categorize funding types
        grants = []
        loans = []
        equity = []
        government = []
        philanthropic = []
        
        for source in funding_sources:
            name = source.get("source", "").lower()
            amount = source.get("amount")
            
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
        
        # Calculate percentages (None when the underlying amounts are withheld)
        grant_percent = self._percent(self._sum_known([g["amount"] for g in grants]), total_funding)
        loan_percent = self._percent(self._sum_known([l["amount"] for l in loans]), total_funding)
        equity_percent = self._percent(self._sum_known([e["amount"] for e in equity]), total_funding)
        government_percent = self._percent(self._sum_known([g["amount"] for g in government]), total_funding)
        philanthropic_percent = self._percent(self._sum_known([p["amount"] for p in philanthropic]), total_funding)
        
        # Determine funding model (no model can be inferred from withheld amounts)
        if total_funding is None:
            model = "Undetermined"
        elif grant_percent is not None and grant_percent > 50:
            model = "Grant-Dependent"
        elif loan_percent is not None and loan_percent > 50:
            model = "Loan-Financed"
        elif government_percent is not None and government_percent > 50:
            model = "Government-Funded"
        elif philanthropic_percent is not None and philanthropic_percent > 40:
            model = "Philanthropic"
        elif None in (grant_percent, loan_percent, equity_percent, government_percent, philanthropic_percent):
            # No dominant source readable because some shares are withheld
            model = "Undetermined"
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
        # Get total cost. A7: only known phase costs are summed; when every
        # phase is withheld the total itself is unknown (None).
        phases = project_data.get("phases", {})
        phase_costs = [
            phases.get(phase, {}).get("cost")
            for phase in ["planning", "infrastructure", "construction", "project_management"]
        ]
        known_costs = [c for c in phase_costs if c is not None]
        
        contingency = phases.get("contingency_percent") or 10
        total_cost = sum(known_costs) * (1 + contingency / 100) if known_costs else None
        
        total_funding = funding_analysis["total_funding"]
        
        # A funding gap needs both sides; with either withheld it is undetermined.
        funding_gap = (
            total_cost - total_funding
            if total_cost is not None and total_funding is not None
            else None
        )
        
        # Calculate debt-to-equity ratio (None when either side is withheld)
        debt = self._sum_known([l["amount"] for l in funding_analysis["funding_breakdown"]["loans"]])
        equity = self._sum_known([e["amount"] for e in funding_analysis["funding_breakdown"]["equity"]])
        
        if debt is None or equity is None:
            debt_to_equity = None
        elif debt > 0 and equity > 0:
            debt_to_equity = debt / equity
        elif debt > 0:
            debt_to_equity = float('inf')
        else:
            debt_to_equity = 0
        
        # Calculate total interest (assuming 5% interest on loans)
        interest_rate = 0.05
        total_interest = debt * interest_rate if debt is not None else None
        
        # Calculate fees (1-2% of total funding)
        funding_fees = total_funding * 0.015 if total_funding is not None else None
        
        known_financing = [v for v in (total_interest, funding_fees) if v is not None]
        total_financing_cost = sum(known_financing) if known_financing else None
        
        return {
            "total_project_cost": total_cost,
            "total_funding_available": total_funding,
            "funding_gap": funding_gap,
            "debt_to_equity_ratio": debt_to_equity,
            "total_interest": total_interest,
            "funding_fees": funding_fees,
            "total_financing_cost": total_financing_cost,
            "net_funding_available": (
                total_funding - total_financing_cost
                if total_funding is not None and total_financing_cost is not None
                else None
            )
        }
    
    def _analyze_risk(self, financial_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze financial risks"""
        risks = []
        
        funding_gap = financial_metrics["funding_gap"]
        total_cost = financial_metrics["total_project_cost"]
        debt_to_equity = financial_metrics["debt_to_equity_ratio"]
        financing_cost = financial_metrics["total_financing_cost"]
        total_interest = financial_metrics["total_interest"]
        
        # Funding gap risk (a withheld gap is not a zero gap)
        if funding_gap is not None and funding_gap > 0:
            risks.append({
                "risk": "Funding Shortfall",
                "severity": "High" if total_cost is not None and funding_gap > total_cost * 0.3 else "Medium",
                "description": f"Project has a funding gap of ${funding_gap:,.2f}"
            })
        
        # Debt risk
        if debt_to_equity is not None and debt_to_equity > 2:
            risks.append({
                "risk": "High Debt Exposure",
                "severity": "High",
                "description": f"Debt-to-equity ratio of {debt_to_equity:.1f}% exceeds recommended levels"
            })
        
        # Financing cost risk
        if financing_cost is not None and total_cost:
            if financing_cost > total_cost * 0.1:
                risks.append({
                    "risk": "High Financing Costs",
                    "severity": "Medium",
                    "description": f"Financing costs of ${financing_cost:,.2f} are significant"
                })
        
        # Debt service capacity
        if total_interest is not None and total_interest > 0:
            risks.append({
                "risk": "Interest Service Capacity",
                "severity": "Medium",
                "description": "Ongoing interest payments require strong operational revenue"
            })
        
        # A7: no risk level can be asserted when every basis for it is withheld
        undetermined = (
            funding_gap is None and total_cost is None
            and debt_to_equity is None and financing_cost is None
        )
        if undetermined:
            overall = "Undetermined"
        elif len(risks) >= 3:
            overall = "High"
        elif len(risks) >= 1:
            overall = "Medium"
        else:
            overall = "Low"
        
        return {
            "risks": risks,
            "risk_count": len(risks),
            "overall_financial_risk": overall
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
        
        # Determine financial sustainability score (1-100). A7: a withheld
        # funding gap leaves the score undetermined (None), not a fake zero.
        sustainability_score = 0
        
        funding_gap = financial_metrics["funding_gap"]
        total_cost = financial_metrics["total_project_cost"]
        debt_to_equity = financial_metrics["debt_to_equity_ratio"]
        grant_percent = funding_analysis["funding_percentages"]["grants"]
        
        # Score based on funding gap
        if funding_gap is None:
            pass
        elif funding_gap <= 0:
            sustainability_score += 30
        elif total_cost is not None and funding_gap < total_cost * 0.1:
            sustainability_score += 20
        elif total_cost is not None and funding_gap < total_cost * 0.3:
            sustainability_score += 10
        
        # Score based on debt-to-equity
        if debt_to_equity is None:
            pass
        elif debt_to_equity <= 1:
            sustainability_score += 25
        elif debt_to_equity <= 2:
            sustainability_score += 15
        elif debt_to_equity <= 3:
            sustainability_score += 5
        
        # Score based on funding diversity
        if funding_analysis["source_count"] >= 4:
            sustainability_score += 25
        elif funding_analysis["source_count"] >= 2:
            sustainability_score += 15
        elif funding_analysis["source_count"] >= 1:
            sustainability_score += 5
        
        # Score based on grant component
        if grant_percent is None:
            pass
        elif grant_percent > 30:
            sustainability_score += 20
        elif grant_percent > 10:
            sustainability_score += 10
        
        # An undetermined funding picture cannot carry a sustainability rating.
        gap_is_none = funding_gap is None
        score_undetermined = gap_is_none and financial_metrics["total_funding_available"] is None
        
        if gap_is_none:
            funding_recommendation = "Funding data withheld (policy A7) - additional funding need cannot be assessed"
        elif funding_gap > 0:
            funding_recommendation = "Secure additional funding"
        else:
            funding_recommendation = "Funding adequate"
        
        if debt_to_equity is None:
            debt_recommendation = "Debt exposure undetermined (withheld figures)"
        elif debt_to_equity > 2:
            debt_recommendation = "Reduce debt exposure"
        else:
            debt_recommendation = "Debt levels manageable"
        
        if gap_is_none:
            contingency_recommendation = "Contingency levels undetermined (withheld figures)"
        elif funding_gap < 0:
            contingency_recommendation = "Consider contingency funding"
        else:
            contingency_recommendation = "Review contingency levels"
        
        results = {
            "funding_structure": {
                "funding_model": funding_analysis["funding_model"],
                "funding_breakdown": funding_analysis["funding_percentages"],
                "source_count": funding_analysis["source_count"],
                "funding_sources": [
                    f"{s.get('source', 'Unknown')}: {self._money(s.get('amount'))}"
                    for s in funding_analysis["funding_sources"]
                ]
            },
            "financial_metrics": financial_metrics,
            "financial_risk": risk_analysis,
            "sustainability": {
                "score": None if score_undetermined else min(sustainability_score, 100),
                "rating": "Undetermined" if score_undetermined else "Excellent" if sustainability_score >= 80 else "Good" if sustainability_score >= 60 else "Fair" if sustainability_score >= 40 else "Poor",
                "recommendations": [
                    funding_recommendation,
                    debt_recommendation,
                    "Diversify funding sources" if funding_analysis["source_count"] < 3 else "Good funding diversity",
                    contingency_recommendation
                ]
            }
        }
        
        score_text = "undetermined (A7)" if score_undetermined else str(min(sustainability_score, 100))
        self.logger.info(f"Financial analysis complete. Sustainability score: {score_text}")
        self.logger.info(f"Funding model: {funding_analysis['funding_model']}")
        
        return self.format_output(results)