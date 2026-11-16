"""
Test script for all 9 agents
Run with: python test_all_9_agents.py
"""

import json
from src.core.project_loader import ProjectLoader
from src.agents import (
    AgentOrchestrator,
    CostAgent,
    PlanningAgent,
    EnvAgent,
    TrafficAgent,
    UrbanDesignAgent,
    RiskAgent,
    ValuatorAgent,
    BusinessAnalystAgent,
    AccountantAgent
)


def test_single_agents():
    """Test each agent individually"""
    print("=" * 70)
    print("TESTING SINGLE AGENTS - ALL 9 AGENTS")
    print("=" * 70)
    
    loader = ProjectLoader()
    loader.load_project("Gnowangerup Community Housing")
    
    # Test each agent with descriptions
    agents = {
        "Cost": {
            "class": CostAgent,
            "description": "Financial feasibility and cost analysis"
        },
        "Planning": {
            "class": PlanningAgent,
            "description": "Planning requirements and approval pathways"
        },
        "Environmental": {
            "class": EnvAgent,
            "description": "Environmental constraints and bushfire risk"
        },
        "Traffic": {
            "class": TrafficAgent,
            "description": "Traffic impact and requirements"
        },
        "Urban Design": {
            "class": UrbanDesignAgent,
            "description": "Masterplanning and yield analysis"
        },
        "Risk": {
            "class": RiskAgent,
            "description": "Risk register and mitigation strategies"
        },
        "Valuator": {
            "class": ValuatorAgent,
            "description": "Property valuation estimates"
        },
        "Business Analyst": {
            "class": BusinessAnalystAgent,
            "description": "Business case and cost-benefit analysis"
        },
        "Accountant": {
            "class": AccountantAgent,
            "description": "Funding structures and financial strategy"
        }
    }
    
    successful_agents = 0
    failed_agents = 0
    
    for name, agent_info in agents.items():
        print(f"\n📊 Testing {name} Agent...")
        print(f"   Description: {agent_info['description']}")
        
        try:
            agent_class = agent_info['class']
            agent = agent_class(loader)
            result = agent.process()
            print(f"   ✅ {name} Agent completed successfully")
            successful_agents += 1
            
            # Show a summary based on agent type
            if name == "Cost":
                costs = result["results"]["cost_breakdown"]
                print(f"   📊 Total Cost: ${costs['total_cost']:,.2f}")
                print(f"   📊 Funding Gap: ${result['results']['funding_analysis']['funding_gap']:,.2f}")
                print(f"   📊 Feasible: {'Yes' if result['results']['funding_analysis']['funding_gap'] <= 0 else 'No'}")
            
            elif name == "Planning":
                reqs = result["results"]["approval_requirements"]
                print(f"   📋 Pathway: {reqs.get('pathway', 'N/A')}")
                print(f"   📋 Timeline: {reqs.get('estimated_timeline_months', 'N/A')} months")
                print(f"   📋 Rezoning Required: {'Yes' if result['results']['planning_summary'].get('rezoning_required', False) else 'No'}")
            
            elif name == "Environmental":
                bal = result["results"]["environmental_assessment"]["bal_assessment"]
                env_constraints = result["results"]["environmental_assessment"]["constraints"]
                print(f"   🌿 BAL Rating: {bal['rating']}")
                print(f"   🌿 Bushfire Risk: {env_constraints.get('bushfire_risk', 'Unknown')}")
                print(f"   🌿 Heritage Present: {'Yes' if result['results']['significance']['heritage_present'] else 'No'}")
                print(f"   🌿 Mitigation Measures: {len(result['results']['mitigation_measures'])} identified")
            
            elif name == "Traffic":
                trips = result["results"]["trip_generation"]
                print(f"   🚗 Daily Trips: {trips['daily_trips']}")
                print(f"   🚗 AM Peak: {trips['am_peak_trips']}")
                print(f"   🚗 PM Peak: {trips['pm_peak_trips']}")
                print(f"   🚗 TIA Required: {'Yes' if result['results']['traffic_requirements']['tia_required'] else 'No'}")
            
            elif name == "Urban Design":
                yield_data = result["results"]["yield_analysis"]
                density = result["results"]["density_analysis"]
                print(f"   🏗️ Total Buildings: {yield_data['total_buildings']}")
                print(f"   🏗️ Developable Area: {yield_data['developable_area_ha']} ha")
                print(f"   🏗️ Density Code: {density.get('density_code', 'N/A')}")
                print(f"   🏗️ Product Mix: {len(result['results']['product_mix'])} types")
            
            elif name == "Risk":
                risk_summary = result["results"]["risk_summary"]
                print(f"   ⚠️ Total Risks: {risk_summary['total_risks']}")
                print(f"   ⚠️ Overall Risk Level: {risk_summary['overall_risk_level']}")
                print(f"   ⚠️ Critical Risks: {result['results']['risk_register']['total_risks']}")
                print(f"   ⚠️ Recommended Contingency: {result['results']['risk_mitigation']['recommended_contingency_percent']}%")
            
            elif name == "Valuator":
                land = result["results"]["land_valuation"]
                completed = result["results"]["completed_valuation"]
                profitability = result["results"]["profitability"]
                print(f"   💰 Land Value: ${land['land_value']:,.2f}")
                print(f"   💰 Completed Value: ${completed['total_completed_value']:,.2f}")
                print(f"   💰 Gross Profit: ${profitability['gross_profit']:,.2f}")
                print(f"   💰 Profit Margin: {profitability['profit_margin_percent']:.1f}%")
                print(f"   💰 Confidence Level: {profitability['confidence_level']}")
            
            elif name == "Business Analyst":
                financial = result["results"]["financial_analysis"]
                social = result["results"]["social_analysis"]
                blended = result["results"]["blended_analysis"]
                print(f"   📈 Financial BCR: {financial['bcr']:.2f}")
                print(f"   📈 Social BCR: {social['social_bcr']:.2f}")
                print(f"   📈 Blended BCR: {blended['blended_bcr']:.2f}")
                print(f"   📈 Recommendation: {blended['recommendation']}")
                print(f"   📈 Priority: {blended['priority']}")
            
            elif name == "Accountant":
                financial = result["results"]["financial_metrics"]
                sustainability = result["results"]["sustainability"]
                print(f"   💳 Total Project Cost: ${financial['total_project_cost']:,.2f}")
                print(f"   💳 Funding Gap: ${financial['funding_gap']:,.2f}")
                print(f"   💳 Debt-to-Equity: {financial['debt_to_equity_ratio']:.2f}")
                print(f"   💳 Sustainability Score: {sustainability['score']}/100")
                print(f"   💳 Rating: {sustainability['rating']}")
                print(f"   💳 Funding Model: {result['results']['funding_structure']['funding_model']}")
            
        except Exception as e:
            print(f"   ❌ {name} Agent failed: {e}")
            failed_agents += 1
    
    print("\n" + "-" * 70)
    print(f"📊 SINGLE AGENT TEST SUMMARY:")
    print(f"   ✅ Successful: {successful_agents}")
    print(f"   ❌ Failed: {failed_agents}")
    print(f"   📊 Total: {successful_agents + failed_agents}")
    print("=" * 70)


def test_orchestrator():
    """Test the orchestrator running all 9 agents"""
    print("\n" + "=" * 70)
    print("TESTING ORCHESTRATOR - ALL 9 AGENTS")
    print("=" * 70)
    
    loader = ProjectLoader()
    loader.load_project("Gnowangerup Community Housing")
    
    orchestrator = AgentOrchestrator(loader)
    
    print("\n🚀 Running all 9 agents via orchestrator...")
    results = orchestrator.run_all()
    
    print("\n📊 Orchestrator Results Summary:")
    summary = orchestrator.get_combined_summary()
    
    print(f"  Project: {summary['project']}")
    print(f"  Agents Run: {summary['total_agents_run']}")
    print(f"  Successful: {summary['successful_agents']}")
    print(f"  Failed: {summary['failed_agents']}")
    print("-" * 50)
    
    # Key metrics from all agents
    print("\n💰 FINANCIAL METRICS:")
    print(f"  Total Cost: ${summary.get('total_cost', 0):,.2f}")
    print(f"  Funding Gap: ${summary.get('funding_gap', 0):,.2f}")
    print(f"  Feasible: {'Yes' if summary.get('is_feasible', False) else 'No'}")
    print(f"  Total Completed Value: ${summary.get('total_completed_value', 0):,.2f}")
    print(f"  Gross Profit: ${summary.get('gross_profit', 0):,.2f}")
    print(f"  Sustainability Score: {summary.get('sustainability_score', 0)}/100")
    
    print("\n📋 PLANNING METRICS:")
    print(f"  Zoning: {summary.get('zoning', 'Unknown')}")
    print(f"  Approval Pathway: {summary.get('approval_pathway', 'Unknown')}")
    print(f"  Planning Timeline: {summary.get('planning_timeline_months', 0)} months")
    
    print("\n🌿 ENVIRONMENTAL METRICS:")
    print(f"  BAL Rating: {summary.get('bal_rating', 'Unknown')}")
    print(f"  Heritage Present: {'Yes' if summary.get('heritage_present', False) else 'No'}")
    print(f"  Overall Risk Level: {summary.get('overall_risk_level', 'Unknown')}")
    print(f"  Total Risks Identified: {summary.get('total_risks', 0)}")
    
    print("\n🚗 TRAFFIC METRICS:")
    print(f"  Daily Trips: {summary.get('daily_trips', 0)}")
    print(f"  TIA Required: {'Yes' if summary.get('tia_required', False) else 'No'}")
    
    print("\n📈 BUSINESS CASE METRICS:")
    print(f"  Financial BCR: {summary.get('financial_bcr', 0):.2f}")
    print(f"  Social BCR: {summary.get('social_bcr', 0):.2f}")
    print(f"  Blended BCR: {summary.get('blended_bcr', 0):.2f}")
    print(f"  Recommendation: {summary.get('recommendation', 'Unknown')}")
    
    print("\n📋 Agent Status:")
    for agent, status in summary['agent_status'].items():
        emoji = "✅" if status == "success" else "❌"
        print(f"  {emoji} {agent}: {status}")
    
    print("\n⏱️ Execution Times:")
    for agent, time in summary.get('execution_times', {}).items():
        print(f"  {agent}: {time:.2f}s")
    
    # Save results
    saved_path = orchestrator.save_results()
    print(f"\n💾 Full results saved to: {saved_path}")
    
    # Save summary
    summary_path = orchestrator.save_summary()
    print(f"💾 Summary saved to: {summary_path}")
    
    # Print the formatted summary
    orchestrator.print_summary()


def test_category_runs():
    """Test running agents by category"""
    print("\n" + "=" * 70)
    print("TESTING CATEGORY RUNS")
    print("=" * 70)
    
    loader = ProjectLoader()
    loader.load_project("Gnowangerup Community Housing")
    orchestrator = AgentOrchestrator(loader)
    
    categories = {
        "financial": ["cost", "valuator", "business_analyst", "accountant"],
        "planning": ["planning", "urban_design"],
        "environmental": ["environmental", "risk"],
        "infrastructure": ["traffic"]
    }
    
    for category, agents in categories.items():
        print(f"\n📂 Running {category.upper()} category ({len(agents)} agents)...")
        results = orchestrator.run_selected(agents)
        
        # Show which agents ran
        agent_names = list(results.keys())
        print(f"   Agents: {', '.join(agent_names)}")
        
        # Check if all succeeded
        all_success = all("error" not in r for r in results.values())
        print(f"   Status: {'✅ All successful' if all_success else '❌ Some failed'}")
    
    print("\n" + "=" * 70)


def test_different_projects():
    """Test agents on different project types"""
    print("\n" + "=" * 70)
    print("TESTING DIFFERENT PROJECT TYPES")
    print("=" * 70)
    
    projects = ["Gnowangerup Community Housing", "Heritage Sanctuary - Commercial Precinct"]
    
    for project_name in projects:
        print(f"\n📂 Testing project: {project_name}")
        print("-" * 50)
        
        try:
            loader = ProjectLoader()
            loader.load_project(project_name)
            orchestrator = AgentOrchestrator(loader)
            
            # Run just the key agents
            agents = ["cost", "planning", "environmental", "traffic"]
            results = orchestrator.run_selected(agents)
            
            summary = orchestrator.get_combined_summary()
            
            print(f"   Total Cost: ${summary.get('total_cost', 0):,.2f}")
            print(f"   Feasible: {'Yes' if summary.get('is_feasible', False) else 'No'}")
            print(f"   Total Buildings: {summary.get('total_buildings', 0)}")
            print(f"   Daily Trips: {summary.get('daily_trips', 0)}")
            
            statuses = orchestrator.get_agent_status()
            successful = sum(1 for s in statuses.values() if s == "success")
            total = len(statuses)
            print(f"   Agent Status: {successful}/{total} successful")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 70)


def main():
    """Main test runner"""
    print("🏇 FIVEHORSES - All 9 Agents Test Suite")
    print("=" * 70)
    print("\nThis test will run all 9 agents in multiple configurations:")
    print("  1. Individual agent tests")
    print("  2. Orchestrator running all agents")
    print("  3. Category-based runs")
    print("  4. Different project types")
    print("\n" + "=" * 70)
    
    try:
        # Run all tests
        test_single_agents()
        test_orchestrator()
        test_category_runs()
        test_different_projects()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETE!")
        print("=" * 70)
        print("\n📊 Summary of All 9 Agents:")
        print("  1. Cost Agent - Financial feasibility and cost analysis")
        print("  2. Planning Agent - Planning requirements and approval pathways")
        print("  3. Environmental Agent - Environmental constraints and bushfire risk")
        print("  4. Traffic Agent - Traffic impact and requirements")
        print("  5. Urban Design Agent - Masterplanning and yield analysis")
        print("  6. Risk Agent - Risk register and mitigation strategies")
        print("  7. Valuator Agent - Property valuation estimates")
        print("  8. Business Analyst Agent - Business case and cost-benefit analysis")
        print("  9. Accountant Agent - Funding structures and financial strategy")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error in test suite: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()