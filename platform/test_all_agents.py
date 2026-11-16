"""
Test script for all agents
Run with: python test_all_agents.py
"""

import json
from src.core.project_loader import ProjectLoader
from src.agents import AgentOrchestrator
from src.agents import CostAgent, PlanningAgent, EnvAgent, TrafficAgent, UrbanDesignAgent

def test_single_agents():
    """Test each agent individually"""
    print("=" * 60)
    print("TESTING SINGLE AGENTS")
    print("=" * 60)
    
    loader = ProjectLoader()
    loader.load_project("Gnowangerup Community Housing")
    
    # Test each agent
    agents = {
        "Cost": CostAgent,
        "Planning": PlanningAgent,
        "Environmental": EnvAgent,
        "Traffic": TrafficAgent,
        "Urban Design": UrbanDesignAgent
    }
    
    for name, agent_class in agents.items():
        print(f"\n📊 Testing {name} Agent...")
        try:
            agent = agent_class(loader)
            result = agent.process()
            print(f"✅ {name} Agent completed successfully")
            
            # Show a summary
            if name == "Cost":
                costs = result["results"]["cost_breakdown"]
                print(f"   Total Cost: ${costs['total_cost']:,.2f}")
                print(f"   Funding Gap: ${result['results']['funding_analysis']['funding_gap']:,.2f}")
            
            elif name == "Planning":
                reqs = result["results"]["approval_requirements"]
                print(f"   Pathway: {reqs.get('pathway', 'N/A')}")
                print(f"   Timeline: {reqs.get('estimated_timeline_months', 'N/A')} months")
            
            elif name == "Environmental":
                bal = result["results"]["environmental_assessment"]["bal_assessment"]
                print(f"   BAL Rating: {bal['rating']}")
                print(f"   Heritage Present: {result['results']['significance']['heritage_present']}")
            
            elif name == "Traffic":
                trips = result["results"]["trip_generation"]
                print(f"   Daily Trips: {trips['daily_trips']}")
                print(f"   TIA Required: {result['results']['traffic_requirements']['tia_required']}")
            
            elif name == "Urban Design":
                yield_data = result["results"]["yield_analysis"]
                print(f"   Total Buildings: {yield_data['total_buildings']}")
                print(f"   Developable Area: {yield_data['developable_area_ha']} ha")
                
        except Exception as e:
            print(f"❌ {name} Agent failed: {e}")

def test_orchestrator():
    """Test the orchestrator running all agents"""
    print("\n" + "=" * 60)
    print("TESTING ORCHESTRATOR")
    print("=" * 60)
    
    loader = ProjectLoader()
    loader.load_project("Gnowangerup Community Housing")
    
    orchestrator = AgentOrchestrator(loader)
    
    print("\n🚀 Running all agents...")
    results = orchestrator.run_all()
    
    print("\n📊 Results Summary:")
    summary = orchestrator.get_combined_summary()
    
    print(f"  Project: {summary['project']}")
    print(f"  Agents Run: {summary['total_agents_run']}")
    print(f"  Total Cost: ${summary.get('total_cost', 0):,.2f}")
    print(f"  Funding Gap: ${summary.get('funding_gap', 0):,.2f}")
    print(f"  Total Buildings: {summary.get('total_buildings', 0)}")
    print(f"  Daily Trips: {summary.get('daily_trips', 0)}")
    
    print("\n📋 Agent Status:")
    for agent, status in summary['agent_status'].items():
        emoji = "✅" if status == "success" else "❌"
        print(f"  {emoji} {agent}: {status}")
    
    # Save results
    saved_path = orchestrator.save_results()
    print(f"\n💾 Results saved to: {saved_path}")
    
    # Show detailed results for one agent
    print("\n📝 Cost Agent Detail:")
    cost_result = results.get("cost", {})
    if "results" in cost_result:
        costs = cost_result["results"]["cost_breakdown"]
        print(f"  Planning: ${costs['planning_cost']:,.2f}")
        print(f"  Construction: ${costs['construction_cost']:,.2f}")
        print(f"  Total: ${costs['total_cost']:,.2f}")

if __name__ == "__main__":
    # Make sure we have a project loaded
    print("🏇 FIVEHORSES - Multi-Agent Test")
    print("=" * 60)
    
    try:
        test_single_agents()
        test_orchestrator()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETE!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")