"""
project_architect_export.py

Maps a completed Orchestrator.run_project() report into the entity schemas
documented in Project Architect's PRD (Project, ProjectPhase, BudgetItem,
Deliverable, RiskItem, FundingSource, ComplianceItem) - so our agents' output
can seed a Project Architect-style tracking database instead of a human
manually typing in 200+ budget lines from scratch.

This is a ONE-WAY, ONE-TIME seed export, not a live sync: once a project
moves into delivery, Project Architect's own tracking (actuals vs budgeted,
task status, contractor management) takes over - this module only produces
the STARTING records.

Known limitations, stated explicitly rather than silently guessed around:
  - RiskItem.likelihood/impact (1-5 ISO 31000 scale) are NOT computed by our
    agents - they produce qualitative risk statements, not numeric ratings.
    Exported as a neutral default (3/3) with a flag noting manual review is
    required, rather than fabricating a false-precision number.
  - cost_code assignment is at the GROUP level only (e.g. "J" for
    Infrastructure & Utilities) - the full 200+ individual Rawlinsons codes
    (e.g. "J.140") were not available in the source documents, only the
    group taxonomy. See knowledge/cost_code_groups.json.
  - FundingSource.status defaults to "identified" since our schema doesn't
    yet track application/decision status per source.
"""

from typing import Dict, Any, List
from datetime import datetime


# CostAgent cost_breakdown line -> Project Architect cost code group.
# Mapped at the group level only - see module docstring.
COST_BREAKDOWN_TO_GROUP = {
    "land_acquisition": "B",       # Land & Title
    "civil_works": "J",            # Infrastructure & Utilities
    "building_construction": None,  # resolved per project_type below (N/O/P)
    "landscape_works": "J",
    "infrastructure_contributions": "J",
    "professional_fees": "E",      # Design & Documentation
    "contingency": "M",            # Contingency & Risk Buffers
    "holding_costs": "I",          # Finance & Feasibility
    "marketing_sales": "I",
    "planning_approvals": "D",     # Planning & Approvals
}

# Our project.type -> Project Architect project_type enum
PROJECT_TYPE_MAP = {
    "community_housing": "residential",
    "social_housing": "residential",
    "commercial": "commercial",
    "traditional": "residential",
}

# Our project.type -> building_construction cost code group
BUILDING_CODE_BY_PROJECT_TYPE = {
    "commercial": "N",
    "community_housing": "O",
    "social_housing": "O",
    "traditional": "O",
}

# Our funding.sources[].source string heuristics -> PA source_type enum
def _infer_source_type(source_name: str) -> str:
    name = (source_name or "").lower()
    if "grant" in name:
        return "grant"
    if "government" in name:
        return "grant"
    if "philanthropic" in name or "donation" in name:
        return "donation"
    if "loan" in name:
        return "loan"
    if "sponsor" in name:
        return "sponsorship"
    return "other"


def export_to_project_architect(project_data: Dict[str, Any], orchestrator_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    project_data: the raw project_data.json dict (from ProjectLoader).
    orchestrator_report: the dict returned by Orchestrator.run_project().

    Returns {"Project": {...}, "ProjectPhase": [...], "BudgetItem": [...],
             "Deliverable": [...], "RiskItem": [...], "FundingSource": [...],
             "ComplianceItem": [...]}
    matching Project Architect's documented entity schemas.
    """
    results = orchestrator_report.get("results", {})
    project = project_data.get("project", {})
    project_type = project.get("type", "traditional")

    export = {
        "Project": _build_project(project, results),
        "ProjectPhase": _build_phases(project_data.get("phases", {})),
        "BudgetItem": _build_budget_items(results.get("cost"), project_type),
        "Deliverable": _build_deliverables(results.get("planning"), results.get("architect")),
        "RiskItem": _build_risk_items(results.get("cost"), results.get("planning")),
        "FundingSource": _build_funding_sources(project_data.get("funding", {})),
        "ComplianceItem": _build_compliance_items(results.get("planning")),
    }
    return export


def _build_project(project: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    cost_result = (results.get("cost") or {}).get("results", {})
    funded_phase = cost_result.get("funded_phase", {})
    total_budget = funded_phase.get("cost_breakdown", {}).get("total_cost")

    return {
        "name": project.get("name", "Unnamed Project"),
        "description": project.get("site_description", ""),
        "project_type": PROJECT_TYPE_MAP.get(project.get("type"), "mixed_use"),
        "status": "planning",
        "progress": 0,
        "location": project.get("location", ""),
        "land_type": _infer_land_type(project.get("land_tenure")),
        "budget": total_budget,
        "construction_environment": "australia_ncc",
        "jurisdiction": "Western Australia",
        "executive_summary": {
            "subtitle": project.get("type", "").replace("_", " ").title(),
            "intention": project.get("site_description", ""),
        },
        "_source_note": "Auto-generated by Orchestrator export - budget/status are a starting estimate, not yet confirmed.",
    }


def _infer_land_type(land_tenure: str) -> str:
    if land_tenure == "freehold":
        return "freehold"
    if land_tenure in ("peppercorn_lease", "leasehold"):
        return "lease"
    if land_tenure == "state_reserve":
        return "reserve"
    return "freehold"


def _build_phases(phases: Dict[str, Any]) -> List[Dict[str, Any]]:
    phase_order = ["planning", "infrastructure", "construction", "project_management"]
    codes = {"planning": "I", "infrastructure": "II", "construction": "III", "project_management": "IV"}
    out = []
    for i, key in enumerate(phase_order):
        data = phases.get(key)
        if not data:
            continue
        duration_months = data.get("duration_months")
        out.append({
            "phase_code": codes[key],
            "name": key.replace("_", " ").title(),
            "description": data.get("description", ""),
            "duration_weeks": round(duration_months * 4.33, 1) if duration_months else None,
            "budget_allocated": data.get("cost"),
            "status": "not_started",
            "order": i,
        })
    return out


def _build_budget_items(cost_agent_output: Dict[str, Any], project_type: str) -> List[Dict[str, Any]]:
    if not cost_agent_output:
        return []
    fp = cost_agent_output.get("results", {}).get("funded_phase", {})
    breakdown = fp.get("cost_breakdown", {})
    building_group = BUILDING_CODE_BY_PROJECT_TYPE.get(project_type, "O")

    items = []
    for line, amount in breakdown.items():
        if line in ("total_cost", "civil_works_source") or amount is None:
            continue
        group = COST_BREAKDOWN_TO_GROUP.get(line)
        if group is None and line == "building_construction":
            group = building_group
        items.append({
            "description": line.replace("_", " ").title(),
            "cost_code": group,
            "item_type": "other",
            "budgeted_amount": amount,
            "actual_amount": None,
            "committed_amount": None,
            "status": "draft",
            "flag": "needs_validation" if group is None else "none",
        })
    return items


def _build_deliverables(planning_output: Dict[str, Any], architect_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    if planning_output:
        p = planning_output.get("results", {})
        for doc in p.get("approval_requirements", {}).get("required_documentation", []):
            out.append({
                "title": doc,
                "deliverable_group": "Planning & Approvals",
                "output_type": "document",
                "authority": ", ".join(p.get("approval_requirements", {}).get("referrals", [])),
                "status": "not_started",
            })
    if architect_output:
        a = architect_output.get("results", {})
        for drawing in a.get("drawing_register", []):
            out.append({
                "title": drawing.get("title", "Untitled drawing"),
                "deliverable_group": "Design & Documentation",
                "output_type": "drawing",
                "authority": "",
                "status": "not_started",
            })
    return out


def _build_risk_items(cost_output: Dict[str, Any], planning_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Our agents produce qualitative risk statements, not numeric ISO 31000
    likelihood/impact ratings. Exported with a neutral 3/3 default and an
    explicit flag that manual assessment is needed - NOT a fabricated
    precise rating.
    """
    out = []
    risk_counter = 1

    if cost_output:
        for risk_text in cost_output.get("results", {}).get("funded_phase", {}).get("feasibility", {}).get("risks", []):
            out.append({
                "risk_id": f"R{risk_counter}",
                "description": risk_text,
                "category": "financial",
                "likelihood": 3,
                "impact": 3,
                "risk_rating": 9,
                "status": "open",
                "_source_note": "Auto-generated from CostAgent - likelihood/impact are a NEUTRAL DEFAULT, not computed. Review and reassess.",
            })
            risk_counter += 1

    if planning_output:
        rf = planning_output.get("results", {}).get("risk_factors", {})
        for key, level in rf.items():
            if level in ("High",):
                out.append({
                    "risk_id": f"R{risk_counter}",
                    "description": f"{key.replace('_', ' ').title()}: {level}",
                    "category": "planning_zoning",
                    "likelihood": 4,
                    "impact": 3,
                    "risk_rating": 12,
                    "status": "open",
                    "_source_note": "Auto-generated from PlanningAgent - likelihood/impact are a NEUTRAL DEFAULT for a flagged 'High' risk, not computed. Review and reassess.",
                })
                risk_counter += 1

    return out


def _build_funding_sources(funding: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for s in funding.get("sources", []):
        out.append({
            "source_type": _infer_source_type(s.get("source")),
            "name": s.get("source", "Unnamed source"),
            "amount": s.get("amount"),
            "status": "identified",
            "is_in_kind": False,
        })
    for ik in funding.get("in_kind_sources", []):
        out.append({
            "source_type": "in_kind",
            "name": ik.get("provider", "Unnamed provider"),
            "amount": ik.get("estimated_value"),
            "status": ik.get("status", "identified"),
            "is_in_kind": True,
            "notes": ik.get("description", ""),
        })
    return out


def _build_compliance_items(planning_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not planning_output:
        return []
    p = planning_output.get("results", {})
    out = []
    for referral in p.get("approval_requirements", {}).get("referrals", []):
        out.append({
            "title": f"{referral} referral/approval",
            "category": "planning_zoning",
            "authority": referral,
            "status": "not_started",
        })
    return out
