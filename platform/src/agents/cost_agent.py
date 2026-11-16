"""
CostAgent - Development feasibility, quantity surveying, and business case
For 5Horses Property Development Company - Western Australia
WITH REGIONAL PRICING FROM UDIA & MASTER BUILDERS WA

Migrated to the Phase 1 Foundation pattern: reads site area, location, and
the actual building mix from project_data.json instead of hardcoded numbers.

Supports TWO explicit, separately-reported scopes:
  - "funded_phase": what does building what this project is ACTUALLY funded
    to build, right now, cost? Uses buildings.homes/dorms/commercial directly,
    including real per-unit costs when the project data provides them.
  - "full_subdivision_potential": what's the full development yield of this
    site if maximally subdivided under its zoning density - a land-banking /
    long-term-value question, independent of what's actually funded today.
Both are computed and reported; funded_phase is authoritative for the
feasibility verdict (it's the near-term, fundable question), and
full_subdivision_potential is informational.

Fixes vs. the original agent (found by testing against real project data):
  - buildings.dorms (short-stay/dormitory accommodation) is now costed and
    counted - previously silently excluded entirely from cost and tenancy
    counts, undercounting real project scope.
  - buildings.commercial is now costed per-building using its own area_sqm,
    not a crude floor_area/100 units estimate.
  - Per-item "cost_per_unit" overrides (when the project data supplies real
    quoted/budgeted costs) are used in preference to the area x regional-rate
    estimate, following the same "prefer real data, cross-check the
    estimate" pattern already used for phase cost validation.
  - Land acquisition respects land_tenure/land_cost (peppercorn/leasehold
    projects aren't charged market-rate land acquisition).
  - Costing is based on developable area, not raw site area.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from src.agents.base_agent import BaseAgent


@dataclass
class DevelopmentBudget:
    land_acquisition: float = 0
    planning_approvals: float = 0
    civil_works: float = 0
    building_construction: float = 0
    landscape_works: float = 0
    infrastructure_contributions: float = 0
    professional_fees: float = 0
    contingency: float = 0
    marketing_sales: float = 0
    holding_costs: float = 0
    total: float = 0


@dataclass
class RevenueModel:
    total_dwellings: int = 0
    average_sale_price: float = 0
    total_revenue: float = 0
    commercial_income: float = 0
    grant_funding: float = 0
    total_income: float = 0


@dataclass
class FeasibilityResult:
    is_viable: bool
    total_cost: float
    total_revenue: float
    gross_profit: float
    profit_margin: float
    roi_percentage: float
    break_even_years: float
    key_assumptions: List[str]
    risks: List[str]
    recommendations: List[str]


class CostAgent(BaseAgent):
    """
    Development costing, feasibility, and business case agent.
    Regional pricing sourced from UDIA State of the Land 2026 & Master Builders WA.
    """

    def __init__(self, project_loader=None, prefer_phase_costs: bool = False):
        """
        prefer_phase_costs: when True, and the project has phases.*.cost
        assumptions populated, use their total as the authoritative
        funded_phase total_cost instead of the computed regional-rate
        estimate (still reports both and the variance either way). Default
        False: the computed estimate is authoritative; phase assumptions are
        cross-checked against it and any large variance is flagged.
        """
        super().__init__(project_loader)
        self.prefer_phase_costs = prefer_phase_costs

        # Regional pricing knowledge (kept inline for now - candidate to move
        # into src/knowledge/knowledge/*.json in a later pass).
        self.land_rates = {
            "perth_metro": 1006, "perth_northern": 1000, "perth_southern": 950,
            "perth_eastern": 900, "perth_western": 1500, "great_southern": 350,
            "mount_barker": 380, "gnowangerup": 320, "albany": 450,
            "busselton": 500, "geraldton": 400, "broome": 600, "derby": 650,
            "default": 350,
        }
        self.construction_rates = {
            "perth_metro": 1100, "perth_northern": 1100, "perth_southern": 1080,
            "perth_eastern": 1050, "perth_western": 1200, "great_southern": 1210,
            "mount_barker": 1200, "gnowangerup": 1200, "albany": 1250,
            "busselton": 1150, "geraldton": 1210, "broome": 1595, "derby": 1650,
            "default": 1200,
        }
        self.sale_prices = {
            "perth_metro": 650000, "perth_northern": 620000, "perth_southern": 580000,
            "perth_eastern": 550000, "perth_western": 850000, "great_southern": 420000,
            "mount_barker": 450000, "gnowangerup": 380000, "albany": 480000,
            "busselton": 520000, "geraldton": 400000, "broome": 550000, "derby": 350000,
            "default": 420000,
        }
        self.cost_rates = {
            "civil_preliminary": 15.0, "civil_earthworks": 25.0, "civil_drainage": 18.0,
            "civil_roads": 35.0, "civil_services": 22.0, "civil_landscape": 12.0,
            "fees_architecture": 0.08, "fees_engineering": 0.06, "fees_planning": 0.03,
            "fees_environmental": 0.02, "fees_other_consultants": 0.04,
            "infrastructure_contribution_per_lot": 35000.0,
            "interest_rate_construction": 0.08, "interest_rate_land": 0.06,
            "contingency_percent": 0.10,
        }
        # Same location->zoning assumption PlanningAgent uses (duplicated
        # here deliberately for now; candidate to move to a shared
        # knowledge/r_codes.json + location->zone lookup once that exists).
        # Density is dwellings/lots per hectare, matching the R-Code number.
        self.density_by_location = {
            "gnowangerup": 30, "mount_barker": 20, "perth_metro": 60,
            "default": 30,
        }

    # ------------------------------------------------------------------
    # BaseAgent overrides
    # ------------------------------------------------------------------

    def get_required_inputs(self) -> list:
        return ["project.location", "project.site_area_ha", "buildings"]

    def validate_inputs(self) -> bool:
        ok = True
        for path in self.get_required_inputs():
            if self.get_project_data(path) is None:
                self.logger.warning(f"Missing required input: {path}")
                ok = False
        homes = self.get_project_data("buildings.homes") or []
        commercial = self.get_project_data("buildings.commercial") or []
        dorms = self.get_project_data("buildings.dorms") or []
        if not (homes or commercial or dorms):
            self.logger.warning("buildings has no homes, dorms, or commercial entries to cost")
            ok = False
        return ok

    def process(self) -> Dict[str, Any]:
        self.logger.info("Starting cost & feasibility analysis (funded_phase + full_subdivision_potential)...")
        if not self.validate_inputs():
            raise ValueError("Missing required inputs for CostAgent")

        location = (self.get_project_data("project.location") or "default").lower().replace(" ", "_")
        site_area_ha = self.get_project_data("project.site_area_ha") or 0
        developable_fraction = self.get_project_data("project.developable_fraction") or 0.7
        developable_area_ha = site_area_ha * developable_fraction

        funded_phase = self._run_funded_phase_scope(location, developable_area_ha)
        subdivision_potential = self._run_subdivision_potential_scope(location, developable_area_ha, site_area_ha)

        results = {
            "location": location,
            "site_area_ha": site_area_ha,
            "developable_area_ha": round(developable_area_ha, 2),
            "funded_phase": funded_phase,
            "full_subdivision_potential": subdivision_potential,
            # Top-level convenience fields mirror funded_phase, since that's
            # the near-term fundable question and what most callers want by
            # default - full detail for both scopes is always in the two
            # sections above.
            "total_cost": funded_phase["cost_breakdown"]["total_cost"],
            "is_viable": funded_phase["feasibility"]["is_viable"],
        }
        self.logger.info(
            f"Cost analysis complete. Funded phase: ${funded_phase['cost_breakdown']['total_cost']:,.0f} "
            f"(viable: {funded_phase['feasibility']['is_viable']}). "
            f"Full subdivision potential: {subdivision_potential['potential_yield']} lots/dwellings, "
            f"${subdivision_potential['cost_breakdown']['total_cost']:,.0f}."
        )
        return self.format_output(results)

    # ------------------------------------------------------------------
    # Scope 1: funded_phase - cost of what's actually being built now
    # ------------------------------------------------------------------

    def _run_funded_phase_scope(self, location: str, developable_area_ha: float) -> Dict[str, Any]:
        building_stats = self._cost_all_buildings(location)
        real_infra = self._get_real_infrastructure_cost()

        budget = self.calculate_development_budget(
            developable_area_ha=developable_area_ha,
            building_construction_cost=building_stats["total_construction_cost"],
            unit_count_for_scaling=building_stats["total_units"],
            location=location,
            civil_works_override=(real_infra["total"] if real_infra else None),
        )

        # Revenue: only buildings.homes are modeled as market-sold - dorms
        # and commercial buildings generate other revenue types (rental,
        # grant-funded operation, café/gallery income) not modeled here.
        homes = self.get_project_data("buildings.homes") or []
        homes_count = sum(h.get("count", 0) for h in homes)
        revenue = self.calculate_revenue(homes_count, location)

        phase_assumption = self._get_phase_cost_assumption()
        cost_validation = self._validate_against_phase_costs(budget.total, phase_assumption)

        if self.prefer_phase_costs and phase_assumption is not None:
            authoritative_total = phase_assumption["total"]
            cost_source = "phase_cost_assumptions (preferred override)"
        else:
            authoritative_total = budget.total
            cost_source = "calculated (regional rate model + real per-unit costs where provided)"

        feasibility = self.assess_feasibility(
            authoritative_total, revenue, location, building_stats["source_note"], cost_validation
        )

        if building_stats["total_units"] > homes_count and homes_count > 0:
            feasibility.risks.append(
                f"Revenue model only counts {homes_count} home(s) as market-sold; "
                f"{building_stats['total_units'] - homes_count} additional dorm/commercial "
                f"unit(s) are costed but generate no modeled revenue (grant/rental income not yet modeled)."
            )

        return {
            "dwelling_basis": building_stats["source_note"],
            "total_units": building_stats["total_units"],
            "total_tenancies": building_stats["total_tenancies"],
            "avg_unit_size_sqm": round(building_stats["avg_unit_size"], 1),
            "cost_source_used_for_feasibility": cost_source,
            "cost_breakdown": {
                "land_acquisition": budget.land_acquisition,
                "civil_works": budget.civil_works,
                "civil_works_source": ("real itemized infrastructure data" if real_infra else "area-based estimate (no itemized infrastructure data provided)"),
                "building_construction": budget.building_construction,
                "landscape_works": budget.landscape_works,
                "infrastructure_contributions": budget.infrastructure_contributions,
                "professional_fees": budget.professional_fees,
                "contingency": budget.contingency,
                "holding_costs": budget.holding_costs,
                "marketing_sales": budget.marketing_sales,
                "planning_approvals": budget.planning_approvals,
                "total_cost": budget.total,
            },
            "cost_per_tenancy": (
                round(budget.total / building_stats["total_tenancies"], 0)
                if building_stats["total_tenancies"] > 0 else None
            ),
            "phase_cost_validation": cost_validation,
            "revenue": {
                "homes_counted_for_revenue": homes_count,
                "average_sale_price": revenue.average_sale_price,
                "total_revenue": revenue.total_revenue,
                "grant_funding": revenue.grant_funding,
                "total_income": revenue.total_income,
            },
            "feasibility": {
                "is_viable": feasibility.is_viable,
                "gross_profit": feasibility.gross_profit,
                "profit_margin_percent": round(feasibility.profit_margin, 1),
                "roi_percent": round(feasibility.roi_percentage, 1),
                "break_even_years": round(feasibility.break_even_years, 1),
                "key_assumptions": feasibility.key_assumptions,
                "risks": feasibility.risks,
                "recommendations": feasibility.recommendations,
            },
        }

    def _cost_all_buildings(self, location: str) -> Dict[str, Any]:
        """
        Costs every building the project actually contains - homes, dorms,
        AND commercial - using each item's own real "cost_per_unit" when the
        project data provides one, falling back to area_sqm x regional
        construction rate otherwise. This replaces the earlier approach that
        only read buildings.homes and silently ignored dorms/commercial
        entirely.

        Also tracks two distinct counts, since they mean different things:
          - total_units: physical structures (used for infrastructure
            contributions, planning approval fees - these are typically
            charged per lot/connection, i.e. per building).
          - total_tenancies: actual dwelling/room tenancies (a 6-room dorm
            building is 1 unit but 6 tenancies) - used for cost-per-tenancy
            reporting, which is the metric real funding briefs benchmark
            against.
        """
        build_rate = self.get_construction_rate(location)
        total_cost = 0.0
        total_units = 0
        total_tenancies = 0
        total_area_weighted = 0.0
        area_weight_basis = 0
        used_real_costs = 0
        used_estimated_costs = 0

        homes = self.get_project_data("buildings.homes") or []
        for h in homes:
            count = h.get("count", 0)
            area = h.get("area_sqm", 0)
            cost_per_unit = h.get("cost_per_unit")
            if cost_per_unit is not None:
                used_real_costs += 1
            else:
                cost_per_unit = area * build_rate
                used_estimated_costs += 1
            total_cost += count * cost_per_unit
            total_units += count
            total_tenancies += count  # each home = 1 tenancy
            total_area_weighted += count * area
            area_weight_basis += count

        dorms = self.get_project_data("buildings.dorms") or []
        for d in dorms:
            count = d.get("count", 0)
            area = d.get("area_sqm", 0)
            rooms = d.get("rooms", 1)
            cost_per_unit = d.get("cost_per_unit")
            if cost_per_unit is not None:
                used_real_costs += 1
            else:
                cost_per_unit = area * build_rate
                used_estimated_costs += 1
            total_cost += count * cost_per_unit
            total_units += count  # dorm BUILDINGS, not rooms
            total_tenancies += count * rooms  # each room is a separate tenancy
            total_area_weighted += count * area
            area_weight_basis += count

        commercial = self.get_project_data("buildings.commercial") or []
        for c in commercial:
            area = c.get("area_sqm", 0)
            cost_per_unit = c.get("cost_per_unit")
            if cost_per_unit is not None:
                used_real_costs += 1
            else:
                cost_per_unit = area * build_rate
                used_estimated_costs += 1
            total_cost += cost_per_unit
            total_units += 1  # commercial items have no "count" field - always 1 building
            # commercial buildings are not counted as tenancies
            total_area_weighted += area
            area_weight_basis += 1

        avg_unit_size = (total_area_weighted / area_weight_basis) if area_weight_basis > 0 else 0

        if used_real_costs and used_estimated_costs:
            source_note = f"{used_real_costs} item(s) using real cost_per_unit, {used_estimated_costs} estimated from area x regional rate"
        elif used_real_costs:
            source_note = f"all {used_real_costs} item(s) using real cost_per_unit from project data"
        elif area_weight_basis > 0:
            source_note = f"all {used_estimated_costs} item(s) estimated from area x regional construction rate (no real per-unit costs provided)"
        else:
            source_note = "no building data available"

        return {
            "total_construction_cost": total_cost,
            "total_units": total_units,
            "total_tenancies": total_tenancies,
            "avg_unit_size": avg_unit_size,
            "source_note": source_note,
        }

    # ------------------------------------------------------------------
    # Scope 2: full_subdivision_potential - land-banking / long-term yield
    # ------------------------------------------------------------------

    def _run_subdivision_potential_scope(self, location: str, developable_area_ha: float,
                                          site_area_ha: float) -> Dict[str, Any]:
        """
        Models the site's full development yield if maximally subdivided
        under its zoning density - independent of what's actually funded
        today. This is deliberately a LOT-SALE model, not a
        build-and-sell-houses model: it costs subdivision (land + civil
        works + fees to create serviceable lots) and revenues lot sales, but
        does NOT include building construction cost for all potential
        dwellings - a land-banking play typically sells serviced lots rather
        than building every house itself.

        Known simplifications (stated explicitly in the output, not hidden):
          - Density assumed from a hardcoded location->zone lookup (same one
            PlanningAgent uses) since knowledge/r_codes.json doesn't exist
            yet. Should be replaced once that knowledge file is built.
          - Lot sale value is approximated using the existing house
            sale-price table as a proxy, since no real vacant-serviced-lot
            price dataset is available yet - flagged as an assumption, not
            presented as authoritative.
        """
        density = self.density_by_location.get(location, self.density_by_location["default"])
        potential_yield = int(developable_area_ha * density)

        land_tenure = self.get_project_data("project.land_tenure") or "freehold"
        explicit_land_cost = self.get_project_data("project.land_cost")
        site_area_sqm = developable_area_ha * 10000
        if land_tenure != "freehold" and explicit_land_cost is not None:
            land_acquisition = explicit_land_cost
        else:
            land_acquisition = site_area_sqm * self.get_land_rate(location)

        civil_rate_per_sqm = sum([
            self.cost_rates["civil_preliminary"], self.cost_rates["civil_earthworks"],
            self.cost_rates["civil_drainage"], self.cost_rates["civil_roads"],
            self.cost_rates["civil_services"],
        ])
        civil_works = site_area_sqm * civil_rate_per_sqm
        professional_fees = civil_works * (
            self.cost_rates["fees_engineering"] + self.cost_rates["fees_planning"] + self.cost_rates["fees_other_consultants"]
        )
        infrastructure_contributions = potential_yield * self.cost_rates["infrastructure_contribution_per_lot"]
        subtotal = land_acquisition + civil_works + professional_fees + infrastructure_contributions
        contingency = subtotal * self.cost_rates["contingency_percent"]
        total_cost = subtotal + contingency

        lot_value = self.get_sale_price(location)
        total_revenue = potential_yield * lot_value
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

        return {
            "note": (
                "Land-banking / long-term yield estimate: models selling "
                f"{potential_yield} serviced lots under assumed R{density} density on the "
                "developable area, NOT building all potential dwellings. Independent of "
                "current project funding - see funded_phase for the near-term fundable scope."
            ),
            "assumed_density_dwellings_per_ha": density,
            "density_source": "location->zone assumption (same lookup PlanningAgent uses; not yet backed by a real knowledge/r_codes.json)",
            "potential_yield": potential_yield,
            "cost_breakdown": {
                "land_acquisition": land_acquisition,
                "civil_works": civil_works,
                "professional_fees": professional_fees,
                "infrastructure_contributions": infrastructure_contributions,
                "contingency": contingency,
                "total_cost": total_cost,
            },
            "revenue": {
                "assumed_lot_value": lot_value,
                "lot_value_source": "approximated from house sale-price table (no real vacant-lot price dataset available yet)",
                "total_revenue": total_revenue,
            },
            "feasibility": {
                "gross_profit": gross_profit,
                "profit_margin_percent": round(profit_margin, 1),
            },
        }

    # ------------------------------------------------------------------
    # Phase cost cross-validation (funded_phase only - phases.*.cost
    # represents the actual funded construction phase, not a hypothetical
    # full-site subdivision)
    # ------------------------------------------------------------------

    def _get_phase_cost_assumption(self) -> Dict[str, Any]:
        phase_costs = {
            "planning": self.get_project_data("phases.planning.cost"),
            "infrastructure": self.get_project_data("phases.infrastructure.cost"),
            "construction": self.get_project_data("phases.construction.cost"),
            "project_management": self.get_project_data("phases.project_management.cost"),
        }
        if all(v is None for v in phase_costs.values()):
            return None

        direct_costs = sum(v or 0 for v in phase_costs.values())
        contingency_percent = self.get_project_data("phases.contingency_percent") or 10
        contingency = direct_costs * (contingency_percent / 100)
        total = direct_costs + contingency

        return {
            "breakdown": {k: (v or 0) for k, v in phase_costs.items()},
            "contingency_percent": contingency_percent,
            "contingency": contingency,
            "direct_costs": direct_costs,
            "total": total,
        }

    def _validate_against_phase_costs(self, calculated_total: float, phase_assumption: Optional[Dict]) -> Dict[str, Any]:
        if phase_assumption is None:
            return {
                "available": False,
                "note": "No phases.*.cost assumptions present on this project - nothing to validate against.",
            }

        phase_total = phase_assumption["total"]
        variance_amount = calculated_total - phase_total
        variance_percent = (variance_amount / phase_total * 100) if phase_total > 0 else 0
        flagged = abs(variance_percent) >= 20

        return {
            "available": True,
            "calculated_total": calculated_total,
            "phase_assumption_total": phase_total,
            "variance_amount": variance_amount,
            "variance_percent": round(variance_percent, 1),
            "flagged": flagged,
            "note": (
                f"Calculated estimate is {'above' if variance_amount >= 0 else 'below'} the project's "
                f"recorded phase cost assumptions by {abs(variance_percent):.1f}%."
                + (" This is a significant variance - review before relying on either figure."
                   if flagged else "")
            ),
        }

    # ------------------------------------------------------------------
    # Pricing lookups
    # ------------------------------------------------------------------

    def _get_real_infrastructure_cost(self) -> Optional[Dict[str, Any]]:
        """
        Sums the project's own itemized infrastructure figures
        (infrastructure.water/power/sewer/roads - real crossover/connection
        counts x real cost_per figures) when present. This is the actual
        on-site servicing cost for the buildings being funded now, and is a
        much better basis for funded_phase civil works than an area-based
        subdivision-scale estimate - that estimate is better suited to
        full_subdivision_potential, where no itemized real figures exist yet.
        Returns None if the project has no itemized infrastructure data.
        """
        water = self.get_project_data("infrastructure.water") or {}
        power = self.get_project_data("infrastructure.power") or {}
        sewer = self.get_project_data("infrastructure.sewer") or {}
        roads = self.get_project_data("infrastructure.roads") or {}

        if not (water or power or sewer or roads):
            return None

        water_cost = (water.get("crossovers", 0) or 0) * (water.get("cost_per", 0) or 0)
        power_cost = (power.get("connections", 0) or 0) * (power.get("cost_per", 0) or 0)
        sewer_cost = (sewer.get("units", 0) or 0) * (sewer.get("cost_per", 0) or 0)
        roads_cost = roads.get("cost") or 0 or 0
        total = water_cost + power_cost + sewer_cost + roads_cost

        if total <= 0:
            return None

        return {
            "water": water_cost, "power": power_cost, "sewer": sewer_cost, "roads": roads_cost,
            "total": total,
        }

    def get_land_rate(self, location: str) -> float:
        return self.land_rates.get(location, self.land_rates["default"])

    def get_construction_rate(self, location: str) -> float:
        return self.construction_rates.get(location, self.construction_rates["default"])

    def get_sale_price(self, location: str) -> float:
        return self.sale_prices.get(location, self.sale_prices["default"])

    # ------------------------------------------------------------------
    # Budget / revenue / feasibility for the funded_phase scope
    # ------------------------------------------------------------------

    def calculate_development_budget(self, developable_area_ha: float, building_construction_cost: float,
                                       unit_count_for_scaling: int, location: str,
                                       civil_works_override: Optional[float] = None) -> DevelopmentBudget:
        site_area_sqm = developable_area_ha * 10000
        budget = DevelopmentBudget()

        land_tenure = self.get_project_data("project.land_tenure") or "freehold"
        explicit_land_cost = self.get_project_data("project.land_cost")
        if land_tenure != "freehold" and explicit_land_cost is not None:
            budget.land_acquisition = explicit_land_cost
        else:
            land_rate = self.get_land_rate(location)
            budget.land_acquisition = site_area_sqm * land_rate

        if civil_works_override is not None:
            # Real itemized infrastructure cost for the buildings actually
            # being serviced - preferred over the area-based subdivision-scale
            # estimate below when the project provides real figures.
            budget.civil_works = civil_works_override
        else:
            civil_rate_per_sqm = sum([
                self.cost_rates["civil_preliminary"], self.cost_rates["civil_earthworks"],
                self.cost_rates["civil_drainage"], self.cost_rates["civil_roads"],
                self.cost_rates["civil_services"],
            ])
            budget.civil_works = site_area_sqm * civil_rate_per_sqm

        budget.building_construction = building_construction_cost

        budget.landscape_works = budget.building_construction * 0.02
        budget.infrastructure_contributions = unit_count_for_scaling * self.cost_rates["infrastructure_contribution_per_lot"]

        total_construction = budget.civil_works + budget.building_construction
        budget.professional_fees = total_construction * (
            self.cost_rates["fees_architecture"] + self.cost_rates["fees_engineering"] +
            self.cost_rates["fees_planning"] + self.cost_rates["fees_environmental"] +
            self.cost_rates["fees_other_consultants"]
        )

        subtotal = (budget.land_acquisition + budget.civil_works + budget.building_construction +
                    budget.professional_fees + budget.infrastructure_contributions)
        budget.contingency = subtotal * self.cost_rates["contingency_percent"]

        construction_loan = total_construction * self.cost_rates["interest_rate_construction"] * 1.5
        land_holding = budget.land_acquisition * self.cost_rates["interest_rate_land"] * 2
        budget.holding_costs = construction_loan + land_holding

        avg_price = self.get_sale_price(location)
        estimated_revenue = unit_count_for_scaling * avg_price
        budget.marketing_sales = estimated_revenue * 0.03

        budget.planning_approvals = unit_count_for_scaling * 2000

        budget.total = sum([
            budget.land_acquisition, budget.civil_works, budget.building_construction,
            budget.landscape_works, budget.infrastructure_contributions,
            budget.professional_fees, budget.contingency, budget.holding_costs,
            budget.marketing_sales, budget.planning_approvals,
        ])
        return budget

    def calculate_revenue(self, homes_count: int, location: str) -> RevenueModel:
        revenue = RevenueModel()
        revenue.total_dwellings = homes_count
        avg_price = self.get_sale_price(location)
        revenue.average_sale_price = avg_price
        revenue.total_revenue = homes_count * avg_price
        if homes_count >= 20:
            revenue.grant_funding = homes_count * 10000
        revenue.total_income = revenue.total_revenue + revenue.grant_funding
        return revenue

    def assess_feasibility(self, total_cost: float, revenue: RevenueModel,
                            location: str, dwelling_source: str,
                            cost_validation: Dict[str, Any]) -> FeasibilityResult:
        total_revenue = revenue.total_income
        gross_profit = total_revenue - total_cost
        profit_margin = (gross_profit / total_revenue) * 100 if total_revenue > 0 else 0
        roi_percentage = (gross_profit / total_cost) * 100 if total_cost > 0 else 0
        break_even_years = total_cost / (total_revenue / 3) if total_revenue > 0 else 0
        is_viable = (profit_margin >= 10 and roi_percentage >= 8 and gross_profit > 0)

        land_rate = self.get_land_rate(location)
        construction_rate = self.get_construction_rate(location)
        sale_price = self.get_sale_price(location)

        key_assumptions = [
            f"Location: {location.replace('_', ' ').title()}",
            f"Land rate: ${land_rate}/sqm",
            f"Construction rate: ${construction_rate}/sqm",
            f"Average sale price: ${sale_price:,.0f}",
            f"Building cost basis: {dwelling_source}",
            "Source: UDIA State of the Land 2026 & Master Builders WA",
        ]

        risks = []
        if profit_margin < 12:
            risks.append("Profit margin below regional benchmark (12-15%)")
        if sale_price < 400000:
            risks.append("Sale price below regional average - review product mix")
        if land_rate > 500:
            risks.append("Land cost above typical regional rate")
        if "estimated" in dwelling_source and "real cost_per_unit" not in dwelling_source:
            risks.append("Building costs are estimated from area x regional rate, not real quoted/budgeted per-unit costs - confirm before relying on this result")
        if cost_validation.get("flagged"):
            risks.append(cost_validation["note"])

        recommendations = []
        if profit_margin < 12:
            recommendations.append("Review product mix - consider house & land packages for higher margin")
        if is_viable:
            recommendations.append("Project is viable with current regional assumptions")
        else:
            recommendations.append("Review cost assumptions or seek additional funding")
        recommendations.append("Engage local agents to validate sale price assumptions")

        return FeasibilityResult(
            is_viable=is_viable, total_cost=total_cost, total_revenue=total_revenue,
            gross_profit=gross_profit, profit_margin=profit_margin, roi_percentage=roi_percentage,
            break_even_years=break_even_years, key_assumptions=key_assumptions,
            risks=risks, recommendations=recommendations,
        )
