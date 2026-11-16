"""
Compare multiple projects side by side
Run with: python compare_projects.py
"""

from src.core.project_loader import ProjectLoader
from src.agents.example_agent import CostAgent

def analyze_project(loader, project_name):
    """Analyze a single project and return key metrics"""
    try:
        loader.load_project(project_name)
        agent = CostAgent(loader)
        output = agent.process()
        results = output["results"]
        
        return {
            "name": loader.get_project_name(),
            "total_cost": results["cost_breakdown"]["total_cost"],
            "funding": results["funding_analysis"]["total_funding_available"],
            "gap": results["funding_analysis"]["funding_gap"],
            "feasible": results["feasibility"]["is_feasible"],
            "dwellings": results["unit_metrics"]["dwelling_count"],
            "cost_per_dwelling": results["unit_metrics"]["cost_per_dwelling"]
        }
    except Exception as e:
        print(f"Error analyzing {project_name}: {e}")
        return None

def main():
    print("=" * 70)
    print("PROJECT COMPARISON DASHBOARD")
    print("=" * 70)
    
    loader = ProjectLoader()
    projects = ["gnowangerup", "heritage_sanctuary"]
    
    results = []
    for project in projects:
        print(f"\n📊 Analyzing {project}...")
        result = analyze_project(loader, project)
        if result:
            results.append(result)
    
    if not results:
        print("No projects analyzed successfully.")
        return
    
    print("\n" + "=" * 70)
    print("PROJECT SUMMARY")
    print("=" * 70)
    
    for r in results:
        print(f"\n🏗️  {r['name']}")
        print("-" * 50)
        print(f"  Total Cost:      ${r['total_cost']:>12,.2f}")
        print(f"  Funding:         ${r['funding']:>12,.2f}")
        print(f"  Funding Gap:     ${r['gap']:>12,.2f}")
        print(f"  Feasible:        {r['feasible']}")
        print(f"  Dwellings:       {r['dwellings']}")
        print(f"  Cost/Dwelling:   ${r['cost_per_dwelling']:>12,.2f}")
    
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    for r in results:
        if not r['feasible']:
            print(f"\n⚠️  {r['name']} needs additional funding of ${r['gap']:,.2f}")
            print(f"   Consider: Reducing scope, finding more grants, or adjusting contingency")

if __name__ == "__main__":
    main()