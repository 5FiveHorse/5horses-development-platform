"""
Simple test script to demonstrate the FiveHorses platform
Run this with: python test_usage.py
"""

import json
from pathlib import Path
from src.core.project_loader import ProjectLoader
from src.agents.example_agent import CostAgent

def main():
    print("=" * 60)
    print("FIVEHORSES PROPERTY DEVELOPMENT PLATFORM")
    print("Data-Driven Analysis System")
    print("=" * 60)
    
    # STEP 1: Initialize the Project Loader
    print("\n📁 STEP 1: Initializing Project Loader...")
    loader = ProjectLoader()
    print("✅ Project Loader ready!")
    
    # STEP 2: Load the Gnowangerup project
    print("\n📂 STEP 2: Loading the Gnowangerup Community Housing Project...")
    try:
        loader.load_project("gnowangerup")
        print(f"✅ Project loaded: {loader.get_project_name()}")
    except FileNotFoundError:
        print("❌ Project not found! Creating it from scratch...")
        # Create the Gnowangerup project data
        gnowangerup_data = {
            "project": {
                "name": "Gnowangerup Community Housing",
                "type": "community_housing",
                "location": "gnowangerup",
                "site_area_ha": 17.18,
                "developable_fraction": 0.333,
                "land_tenure": "peppercorn_lease",
                "land_cost": 0,
                "lease_terms": {
                    "years_remaining": 40,
                    "annual_rent": 1
                },
                "site_description": "Former Aboriginal Mission site. Land is level and built up. Previous houses bulldozed."
            },
            "buildings": {
                "homes": [
                    {"type": "3x2", "count": 2, "bedrooms": 3, "bathrooms": 2, "area_sqm": 140, "construction_type": "standard"},
                    {"type": "2x1", "count": 6, "bedrooms": 2, "bathrooms": 1, "area_sqm": 90, "construction_type": "standard"},
                    {"type": "1x1", "count": 2, "bedrooms": 1, "bathrooms": 1, "area_sqm": 70, "construction_type": "standard"}
                ],
                "dorms": [
                    {"rooms": 6, "count": 2, "construction": "modular", "area_sqm": 180}
                ]
            },
            "infrastructure": {
                "water": {"existing": "mains", "crossovers": 14, "cost_per": 4000},
                "power": {"existing": "nearby", "connections": 14, "cost_per": 10000},
                "sewer": {"type": "septic", "units": 14, "cost_per": 20000},
                "roads": {"existing": "dirt", "upgrade_needed": True, "cost": 150000}
            },
            "funding": {
                "model": "nfp_grants",
                "sources": [
                    {"source": "Government Grant", "amount": 4500000},
                    {"source": "Philanthropic", "amount": 900000}
                ],
                "target": 8140000
            },
            "phases": {
                "planning": {"cost": 800000, "description": "Master Plan, DA, surveys, approvals"},
                "infrastructure": {"cost": 2300000, "description": "Water, power, septic, roads"},
                "construction": {"cost": 4000000, "description": "10 homes + 2 modular dorms"},
                "project_management": {"cost": 300000, "description": "Across all phases"},
                "contingency_percent": 10
            }
        }
        loader.save_project(gnowangerup_data, "gnowangerup")
        print("✅ Created Gnowangerup project from scratch!")
    
    # STEP 3: Display project information
    print("\n📊 STEP 3: Project Information")
    print("-" * 40)
    print(f"Project Name: {loader.get_project_name()}")
    print(f"Site Area: {loader.get_project_site_area()} hectares")
    print(f"Total Dwellings: {loader.get_total_dwellings()} homes")
    print(f"Contingency: {loader.get_contingency_percent()}%")
    print(f"Total Funding: ${loader.get_total_funding():,.2f}")
    
    # STEP 4: Run the Cost Agent
    print("\n🤖 STEP 4: Running Cost Analysis Agent...")
    agent = CostAgent(loader)
    output = agent.process()
    
    # STEP 5: Display results
    print("\n📈 STEP 5: Analysis Results")
    print("-" * 40)
    
    # Cost breakdown
    costs = output["results"]["cost_breakdown"]
    print("\n💰 COST BREAKDOWN:")
    print(f"  Planning:        ${costs['planning_cost']:>12,.2f}")
    print(f"  Infrastructure:  ${costs['infrastructure_cost']:>12,.2f}")
    print(f"  Construction:    ${costs['construction_cost']:>12,.2f}")
    print(f"  Management:      ${costs['management_cost']:>12,.2f}")
    print(f"  Contingency:     ${costs['contingency']:>12,.2f}")
    print("-" * 40)
    print(f"  TOTAL COST:      ${costs['total_cost']:>12,.2f}")
    
    # Funding analysis
    funding = output["results"]["funding_analysis"]
    print("\n💵 FUNDING ANALYSIS:")
    print(f"  Total Funding:   ${funding['total_funding_available']:>12,.2f}")
    print(f"  Funding Gap:     ${funding['funding_gap']:>12,.2f}")
    print(f"  Status:          {funding['funding_adequacy'].upper()}")
    
    # Feasibility
    feasibility = output["results"]["feasibility"]
    print("\n✅ FEASIBILITY:")
    print(f"  Status:          {feasibility['is_feasible']}")
    print(f"  Reason:          {feasibility['reason']}")
    
    # Unit metrics
    metrics = output["results"]["unit_metrics"]
    print("\n🏠 UNIT METRICS:")
    print(f"  Dwelling Count:  {metrics['dwelling_count']}")
    print(f"  Cost per Dwelling: ${metrics['cost_per_dwelling']:,.2f}")
    print(f"  Cost per sqm:    ${metrics['cost_per_sqm']:,.2f}")
    
    # STEP 6: Save the output
    print("\n💾 STEP 6: Saving results...")
    saved_path = agent.save_output(output)
    print(f"✅ Results saved to: {saved_path}")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE!")
    print("The project data is now separate from the agent logic.")
    print("You can add new projects by creating new JSON files in data/projects/")
    print("=" * 60)

if __name__ == "__main__":
    main()