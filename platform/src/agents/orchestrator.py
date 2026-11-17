"""
Agent Orchestrator - Runs multiple agents and aggregates results
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from src.core.project_loader import ProjectLoader
from .example_agent import CostAgent
from .planning_agent import PlanningAgent
from .env_agent import EnvAgent
from .traffic_agent import TrafficAgent
from .urban_design_agent import UrbanDesignAgent
from .risk_agent import RiskAgent
from .valuator_agent import ValuatorAgent
from .business_analyst_agent import BusinessAnalystAgent
from .accountant_agent import AccountantAgent


class AgentOrchestrator:
    """
    Orchestrates multiple agents for comprehensive project analysis
    
    Features:
    - Run all agents or selected subset
    - Aggregate results
    - Save outputs
    - Error handling per agent
    - Progress tracking
    - Summary generation
    """
    
    def __init__(self, project_loader: Optional[ProjectLoader] = None):
        """
        Initialize orchestrator
        
        Args:
            project_loader: ProjectLoader instance to use
        """
        self.project_loader = project_loader or ProjectLoader()
        self.logger = logging.getLogger(__name__)
        
        # Register all 9 core agents
        self.agents = {
            "cost": CostAgent,
            "planning": PlanningAgent,
            "environmental": EnvAgent,
            "traffic": TrafficAgent,
            "urban_design": UrbanDesignAgent,
            "risk": RiskAgent,
            "valuator": ValuatorAgent,
            "business_analyst": BusinessAnalystAgent,
            "accountant": AccountantAgent
        }
        
        # Agent descriptions for display
        self.agent_descriptions = {
            "cost": "Financial feasibility and cost analysis",
            "planning": "Planning requirements and approval pathways",
            "environmental": "Environmental constraints and bushfire risk",
            "traffic": "Traffic impact and requirements",
            "urban_design": "Masterplanning and yield analysis",
            "risk": "Risk register and mitigation strategies",
            "valuator": "Property valuation estimates",
            "business_analyst": "Business case and cost-benefit analysis",
            "accountant": "Funding structures and financial strategy"
        }
        
        self.results = {}
        self.execution_times = {}
    
    def run_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Run a single agent by name
        
        Args:
            agent_name: Name of the agent to run
            
        Returns:
            Agent results
        """
        start_time = time.time()
        
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}. Available: {list(self.agents.keys())}")
        
        self.logger.info(f"Running agent: {agent_name}...")
        
        try:
            agent_class = self.agents[agent_name]
            agent = agent_class(self.project_loader)
            result = agent.process()
            self.results[agent_name] = result
            status = "success"
            error_msg = None
        except Exception as e:
            self.logger.error(f"Error running {agent_name}: {e}")
            self.results[agent_name] = {
                "error": str(e),
                "status": "failed"
            }
            status = "failed"
            error_msg = str(e)
        
        execution_time = time.time() - start_time
        self.execution_times[agent_name] = round(execution_time, 2)
        
        # Log completion
        emoji = "✅" if status == "success" else "❌"
        self.logger.info(f"{emoji} {agent_name} completed in {execution_time:.2f}s")
        
        return self.results[agent_name]
    
    def run_all(self) -> Dict[str, Any]:
        """
        Run all registered agents
        
        Returns:
            Dictionary of all agent results
        """
        self.logger.info("=" * 60)
        self.logger.info("STARTING MULTI-AGENT ORCHESTRATION")
        self.logger.info("=" * 60)
        self.logger.info(f"Project: {self.project_loader.current_project_name}")
        self.logger.info(f"Agents to run: {len(self.agents)}")
        self.logger.info("-" * 60)
        
        for agent_name in self.agents:
            self.run_agent(agent_name)
        
        self.logger.info("-" * 60)
        self.logger.info(f"✅ All {len(self.agents)} agents completed")
        self.logger.info("=" * 60)
        
        return self.results
    
    def run_selected(self, agent_names: List[str]) -> Dict[str, Any]:
        """
        Run selected agents
        
        Args:
            agent_names: List of agent names to run
            
        Returns:
            Dictionary of selected agent results
        """
        self.logger.info(f"Running selected agents: {agent_names}")
        
        for agent_name in agent_names:
            if agent_name in self.agents:
                self.run_agent(agent_name)
            else:
                self.logger.warning(f"Agent not found: {agent_name}")
                self.results[agent_name] = {
                    "error": f"Agent '{agent_name}' not found",
                    "status": "not_found"
                }
        
        return self.results
    
    def run_by_category(self, category: str) -> Dict[str, Any]:
        """
        Run agents by category
        
        Categories:
        - financial: cost, valuator, business_analyst, accountant
        - planning: planning, urban_design
        - environmental: environmental, risk
        - infrastructure: traffic
        """
        category_map = {
            "financial": ["cost", "valuator", "business_analyst", "accountant"],
            "planning": ["planning", "urban_design"],
            "environmental": ["environmental", "risk"],
            "infrastructure": ["traffic"],
            "all": list(self.agents.keys())
        }
        
        if category not in category_map:
            raise ValueError(f"Unknown category: {category}. Available: {list(category_map.keys())}")
        
        agent_names = category_map[category]
        self.logger.info(f"Running category: {category} ({len(agent_names)} agents)")
        
        return self.run_selected(agent_names)
    
    def save_results(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save all results to a JSON file
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        if output_dir is None:
            project_name = self.project_loader.current_project_name
            if project_name:
                output_dir = self.project_loader.projects_root / project_name / "outputs"
            else:
                output_dir = Path("outputs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare comprehensive output
        output_data = {
            "project_name": self.project_loader.current_project_name,
            "timestamp": self._get_timestamp(),
            "execution_times": self.execution_times,
            "total_execution_time": sum(self.execution_times.values()),
            "agent_status": self.get_agent_status(),
            "results": self.results,
            "summary": self.get_combined_summary()
        }
        
        filename = output_dir / "all_agents_output.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Saved all results to: {filename}")
        return filename
    
    def save_summary(self, output_dir: Optional[Path] = None) -> Path:
        """
        Save a summary of results to a JSON file
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        if output_dir is None:
            project_name = self.project_loader.current_project_name
            if project_name:
                output_dir = self.project_loader.projects_root / project_name / "outputs"
            else:
                output_dir = Path("outputs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "project_name": self.project_loader.current_project_name,
            "timestamp": self._get_timestamp(),
            "summary": self.get_combined_summary(),
            "agent_descriptions": self.agent_descriptions,
            "execution_times": self.execution_times
        }
        
        filename = output_dir / "agent_summary.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"💾 Saved summary to: {filename}")
        return filename
    
    def get_agent_status(self) -> Dict[str, str]:
        """
        Get a summary of all agent statuses
        
        Returns:
            Dictionary of agent name to status
        """
        status = {}
        for name, result in self.results.items():
            if "error" in result and result.get("status") == "failed":
                status[name] = "failed"
            elif "error" in result:
                status[name] = "error"
            elif "results" in result:
                status[name] = "success"
            else:
                status[name] = "unknown"
        return status
    
    def get_combined_summary(self) -> Dict[str, Any]:
        """
        Get a combined summary of all agents
        
        Returns:
            Combined summary dictionary
        """
        summary = {
            "project": self.project_loader.current_project_name,
            "total_agents_run": len(self.results),
            "successful_agents": sum(1 for s in self.get_agent_status().values() if s == "success"),
            "failed_agents": sum(1 for s in self.get_agent_status().values() if s == "failed"),
            "agent_status": self.get_agent_status(),
            "execution_times": self.execution_times
        }
        
        # Extract key metrics from each agent
        for agent_name, result in self.results.items():
            if "results" in result:
                results_data = result["results"]
                
                # Cost agent metrics
                if agent_name == "cost":
                    costs = results_data.get("cost_breakdown", {})
                    gap = results_data.get("funding_analysis", {}).get("funding_gap")
                    summary["total_cost"] = costs.get("total_cost")
                    summary["funding_gap"] = gap
                    summary["is_feasible"] = None if gap is None else gap <= 0
                
                # Planning agent metrics
                elif agent_name == "planning":
                    planning_summary = results_data.get("planning_summary", {})
                    summary["zoning"] = planning_summary.get("zoning", "Unknown")
                    summary["approval_pathway"] = results_data.get("approval_requirements", {}).get("pathway", "Unknown")
                    summary["planning_timeline_months"] = results_data.get("approval_requirements", {}).get("estimated_timeline_months", 0)
                
                # Environmental agent metrics
                elif agent_name == "environmental":
                    env = results_data.get("environmental_assessment", {})
                    summary["bal_rating"] = env.get("bal_assessment", {}).get("rating", "Unknown")
                    summary["heritage_present"] = results_data.get("significance", {}).get("heritage_present", False)
                    summary["environmental_significance"] = results_data.get("significance", {}).get("environmental_significance", "Unknown")
                    summary["overall_risk_level"] = results_data.get("risk_summary", {}).get("overall_risk_level", "Unknown")
                
                # Traffic agent metrics
                elif agent_name == "traffic":
                    trips = results_data.get("trip_generation", {})
                    summary["daily_trips"] = trips.get("daily_trips", 0)
                    summary["tia_required"] = results_data.get("traffic_requirements", {}).get("tia_required", False)
                
                # Urban design agent metrics
                elif agent_name == "urban_design":
                    yield_data = results_data.get("yield_analysis", {})
                    summary["total_buildings"] = yield_data.get("total_buildings", 0)
                    summary["developable_area_ha"] = yield_data.get("developable_area_ha", 0)
                    summary["density_code"] = results_data.get("density_analysis", {}).get("density_code", "Unknown")
                
                # Risk agent metrics
                elif agent_name == "risk":
                    risk_summary = results_data.get("risk_summary", {})
                    summary["total_risks"] = risk_summary.get("total_risks", 0)
                    summary["overall_risk_level"] = risk_summary.get("overall_risk_level", "Unknown")
                    summary["critical_risks"] = len(results_data.get("critical_risks", []))
                
                # Valuator agent metrics
                elif agent_name == "valuator":
                    completed = results_data.get("completed_valuation", {})
                    summary["total_completed_value"] = completed.get("total_completed_value", 0)
                    summary["value_per_sqm"] = completed.get("value_per_sqm", 0)
                    summary["gross_profit"] = results_data.get("profitability", {}).get("gross_profit")
                
                # Business analyst agent metrics
                elif agent_name == "business_analyst":
                    summary["financial_bcr"] = results_data.get("financial_analysis", {}).get("bcr")
                    summary["social_bcr"] = results_data.get("social_analysis", {}).get("social_bcr")
                    summary["blended_bcr"] = results_data.get("blended_analysis", {}).get("blended_bcr")
                    summary["recommendation"] = results_data.get("blended_analysis", {}).get("recommendation", "Unknown")
                    summary["priority"] = results_data.get("blended_analysis", {}).get("priority", "Unknown")
                
                # Accountant agent metrics
                elif agent_name == "accountant":
                    financial = results_data.get("financial_metrics", {})
                    summary["total_project_cost"] = financial.get("total_project_cost", 0)
                    summary["funding_gap"] = financial.get("funding_gap", 0)
                    summary["debt_to_equity"] = financial.get("debt_to_equity_ratio", 0)
                    summary["sustainability_score"] = results_data.get("sustainability", {}).get("score", 0)
                    summary["sustainability_rating"] = results_data.get("sustainability", {}).get("rating", "Unknown")
                    summary["funding_model"] = results_data.get("funding_structure", {}).get("funding_model", "Unknown")
        
        return summary
    
    def get_agent_output(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the output of a specific agent
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent output or None if not found
        """
        return self.results.get(agent_name)
    
    def get_successful_agents(self) -> List[str]:
        """
        Get list of successfully completed agents
        
        Returns:
            List of agent names
        """
        return [name for name, status in self.get_agent_status().items() if status == "success"]
    
    def get_failed_agents(self) -> List[str]:
        """
        Get list of failed agents
        
        Returns:
            List of agent names
        """
        return [name for name, status in self.get_agent_status().items() if status == "failed"]
    
    def get_agent_descriptions(self) -> Dict[str, str]:
        """
        Get descriptions of all agents
        
        Returns:
            Dictionary of agent name to description
        """
        return self.agent_descriptions
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()

    @staticmethod
    def _fmt_money(value: Optional[float]) -> str:
        """Render money, or an em-dash when the figure is withheld (policy A7)."""
        return f"${value:,.2f}" if isinstance(value, (int, float)) else "—"

    @staticmethod
    def _fmt_bcr(value: Optional[float]) -> str:
        """Render a benefit-cost ratio, or an em-dash when it is Undetermined."""
        return f"{value:.2f}" if isinstance(value, (int, float)) else "—"
    
    def print_summary(self):
        """Print a formatted summary to console"""
        summary = self.get_combined_summary()
        
        print("\n" + "=" * 70)
        print(f"📊 PROJECT SUMMARY - {self.project_loader.current_project_name}")
        print("=" * 70)
        
        # Agent status
        print(f"\n🤖 Agents: {summary['successful_agents']}/{summary['total_agents_run']} successful")
        for agent, status in summary['agent_status'].items():
            emoji = "✅" if status == "success" else "❌"
            desc = self.agent_descriptions.get(agent, "")
            print(f"  {emoji} {agent.title()}: {desc} ({status})")
        
        # Financial metrics
        print(f"\n💰 Financial Metrics:")
        print(f"  Total Cost: {self._fmt_money(summary.get('total_cost'))}")
        print(f"  Funding Gap: {self._fmt_money(summary.get('funding_gap'))}")
        if 'is_feasible' in summary and summary['is_feasible'] is None:
            feasible_label = "Undetermined"
        else:
            feasible_label = '✅ Yes' if summary.get('is_feasible', False) else '❌ No'
        print(f"  Feasible: {feasible_label}")
        
        # Planning metrics
        if 'zoning' in summary:
            print(f"\n📋 Planning:")
            print(f"  Zoning: {summary.get('zoning', 'Unknown')}")
            print(f"  Approval Pathway: {summary.get('approval_pathway', 'Unknown')}")
            print(f"  Timeline: {summary.get('planning_timeline_months', 0)} months")
        
        # Environmental metrics
        if 'bal_rating' in summary:
            print(f"\n🌿 Environmental:")
            print(f"  BAL Rating: {summary.get('bal_rating', 'Unknown')}")
            print(f"  Heritage Present: {'Yes' if summary.get('heritage_present', False) else 'No'}")
            print(f"  Overall Risk: {summary.get('overall_risk_level', 'Unknown')}")
        
        # Traffic metrics
        if 'daily_trips' in summary:
            print(f"\n🚗 Traffic:")
            print(f"  Daily Trips: {summary.get('daily_trips', 0)}")
            print(f"  TIA Required: {'Yes' if summary.get('tia_required', False) else 'No'}")
        
        # Valuation metrics
        if 'total_completed_value' in summary:
            print(f"\n💎 Valuation:")
            print(f"  Completed Value: {self._fmt_money(summary.get('total_completed_value'))}")
            print(f"  Gross Profit: {self._fmt_money(summary.get('gross_profit'))}")
        
        # Business case metrics
        if 'blended_bcr' in summary:
            print(f"\n📈 Business Case:")
            print(f"  Financial BCR: {self._fmt_bcr(summary.get('financial_bcr'))}")
            print(f"  Social BCR: {self._fmt_bcr(summary.get('social_bcr'))}")
            print(f"  Blended BCR: {self._fmt_bcr(summary.get('blended_bcr'))}")
            print(f"  Recommendation: {summary.get('recommendation', 'Unknown')}")
        
        # Sustainability metrics
        if 'sustainability_score' in summary:
            print(f"\n♻️ Sustainability:")
            print(f"  Score: {summary.get('sustainability_score', 0)}/100")
            print(f"  Rating: {summary.get('sustainability_rating', 'Unknown')}")
            print(f"  Funding Model: {summary.get('funding_model', 'Unknown')}")
        
        # Execution times
        print(f"\n⏱️ Execution Times:")
        for agent, time in summary.get('execution_times', {}).items():
            print(f"  {agent}: {time:.2f}s")
        
        print("\n" + "=" * 70)
    
    def export_to_excel(self, output_dir: Optional[Path] = None) -> Path:
        """
        Export results to Excel format (requires pandas)
        
        Args:
            output_dir: Directory to save results
            
        Returns:
            Path to saved file
        """
        try:
            import pandas as pd
        except ImportError:
            self.logger.warning("pandas not installed. Install with: pip install pandas openpyxl")
            return None
        
        if output_dir is None:
            project_name = self.project_loader.current_project_name
            if project_name:
                output_dir = self.project_loader.projects_root / project_name / "outputs"
            else:
                output_dir = Path("outputs")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Excel writer
        filename = output_dir / "agent_results.xlsx"
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Summary sheet
            summary = self.get_combined_summary()
            summary_df = pd.DataFrame([summary])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Agent status sheet
            status_df = pd.DataFrame([
                {"Agent": name, "Status": status, "Description": self.agent_descriptions.get(name, "")}
                for name, status in self.get_agent_status().items()
            ])
            status_df.to_excel(writer, sheet_name='Agent Status', index=False)
            
            # Extract and save key metrics from each agent
            for agent_name, result in self.results.items():
                if "results" in result:
                    # Flatten the results
                    data = result["results"]
                    
                    # Handle different agent outputs
                    if agent_name == "cost":
                        flat_data = {
                            "Total Cost": data.get("cost_breakdown", {}).get("total_cost", 0),
                            "Funding Gap": data.get("funding_analysis", {}).get("funding_gap", 0),
                            "Cost per Dwelling": data.get("unit_metrics", {}).get("cost_per_dwelling", 0),
                        }
                        pd.DataFrame([flat_data]).to_excel(writer, sheet_name=f'{agent_name.title()}', index=False)
            
        self.logger.info(f"📊 Exported to Excel: {filename}")
        return filename