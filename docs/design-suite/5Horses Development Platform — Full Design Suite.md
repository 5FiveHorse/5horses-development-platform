# 5Horses Platform — Full Design Suite

I've designed the complete six-document suite the brief calls for, built directly on top of the existing seven handoff documents (nothing contradicts them — these extend and formalize). Here's how they map:

| New document                    | Relationship to existing handoff docs                                                                                 |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **DOC 1 — PRD**                 | Extends `PRD.md` with full feature inventory, screen inventory, and success criteria                                  |
| **DOC 2 — TRD**                 | Formalizes `TECHNICAL_SPECIFICATION.md` into a no-guesses stack/tooling blueprint                                     |
| **DOC 3 — App Flow**            | New — screen-by-screen interaction specification (didn't exist)                                                       |
| **DOC 4 — UI/UX Design Brief**  | New — respects the owner's UI deferral; specifies the design system for the polish phase + minimum standards now      |
| **DOC 5 — Backend Schema**      | Extends Tech Spec §5 into full entity/data-model documentation, output contracts, and a future DB/auth migration path |
| **DOC 6 — Implementation Plan** | Converts `ROADMAP_TO_DEPLOYMENT.md` + `OPEN_DECISIONS.md` into an ordered, gated, step-by-step build sequence         |

---

# DOC 1 — `PRD.md` (Full Product Requirements Document)

## 1. Product overview

**Product:** 5Horses Property Development Platform
**Owner:** 5Horses Property Development Company (WA)
**One-line description:** A local-first platform where AI agents perform the work of the ~30 professional roles required to take a WA property project from concept to Development Approval, driven entirely by real project data files.

**True intention (unchanged from handoff PRD):** produce trustworthy analysis, costings, and documentation for two real, active projects — **Gnowangerup Community Housing** (10 homes + 2 dorms, 22 tenancies, peppercorn-leased 17.18ha site, grant/philanthropic funded) and **Heritage Sanctuary Precinct** (Mount Barker; 8,498m² freehold + 40ha Crown reserve, rezoning required, rPPP Stream One). Both are Aboriginal community projects where cultural protocol and heritage handling are functional requirements, not decoration.

## 2. Users & personas

| Persona                                                      | Role                                   | Needs                                                                           | Technical level |
| ------------------------------------------------------------ | -------------------------------------- | ------------------------------------------------------------------------------- | --------------- |
| **The Owner** (primary)                                      | Non-developer, runs locally in VS Code | Select a project, run agents, read results, export a package. Never reads code. | Low — GUI only  |
| **Continuing AI agent** (secondary)                          | You, or another LLM in a future chat   | Handoff docs + codebase; needs unambiguous contracts                            | High            |
| **5Horses staff** (future)                                   | Eventual team members                  | Same as Owner, multi-user                                                       | Low             |
| **The two Aboriginal Corporations** (future, gated by A6/A7) | Stakeholders reviewing outputs         | Read-only access to their own project's outputs                                 | Low             |

**Not a target user yet:** funding bodies, public.

## 3. Definition of done (product-level)

The product is **complete** when, for both real projects, the owner can press one button and produce a coherent, internally-consistent submission-supporting package (planning pathway + cost/feasibility + design + environmental/heritage + risk register + project delivery plan) — every number carrying its basis and confidence label — without developer assistance. **Deployment** is a separate later milestone gated by Open Decisions A6/A7.

## 4. Complete feature inventory

### F1. Project data management ✅ built

Projects are single `project_data.json` files under `data/projects/{name}/`, validated against JSON Schema Draft-07. Multi-parcel, per-parcel tenure, explicit rezoning, buildings (homes/dorms/commercial with optional real `cost_per_unit`), itemized infrastructure, funding (sources, named programs, in-kind, revenue streams), phased budgets.

### F2. Schema validation ✅ built

Every load validates; failures fail fast and once, with human-readable errors.

### F3. Single-agent execution ✅ built

Run any one agent against any one project; structured JSON result.

### F4. Orchestrated multi-agent runs ✅ built

`Orchestrator.run_project(project, agent_names=[...])` — registry-driven, dependency-ordered, per-agent error isolation (one failure never aborts the run), partial results + explicit error reporting.

### F5. Cross-agent data flow ✅ built

`AGENT_DEPENDENCIES` registry; upstream output injected via `self.get_upstream_data()`. One real dependency wired (cost ← planning, rezoning-delay premium). Dependencies are enhancements — every agent must work with zero upstream data.

### F6. Knowledge base ✅ built, gaps remain

Hot-editable JSON in `src/knowledge/knowledge/` — editing never requires code change. Existing: `regional_pricing.json` (sourced, confidence-labeled), `r_codes.json` (WAPC 2024), `cost_code_groups.json`. Missing: `environmental_constraints.json`, `dwelling_sizes.json`, `wa_planning.json`.

### F7. Dual-scope costing ✅ built

`funded_phase` (authoritative) + `full_subdivision_potential` (informational). Prominence of the latter pending decision A2.

### F8. Funding-model-aware feasibility ✅ built

Grant-funded projects assessed on funding-gap coverage, not market profit margin. Cross-validation against recorded phase costs, variance ≥20% flagged.

### F9. Architectural design generation ✅ built

Per-typology designs, drawing register, cultural design elements keyed correctly by location. Optional 2D render (Replicate/Stable Diffusion) and 3D (Blender MCP) — both degrade gracefully. 3D **never verified against real Blender** (A8).

### F10. Project Architect export ✅ built

One-way JSON seed export (Project, ProjectPhase, BudgetItem, Deliverable, RiskItem, FundingSource, ComplianceItem). No confirmed import path (A5).

### F11. Dashboard reporting ✅ built

Project selector, agent selector, run, summary, itemized budget, two-scope comparison, raw JSON, export.

### F12. The ~27 remaining professional-role agents ⬜ not started

Priority order gated by decision **A1**. Full target list: environmental, ecological, heritage/cultural, geotechnical, civil/structural, traffic, landscape, hydrology, water supply, electrical, telecommunications, waste management, risk register, business case/economics, valuation, asset management, accessibility, project management, community engagement, legal/governance, and specialist assessments.

### F13. Package assembler ⬜ not built (new requirement)

Select completed runs for a project → compile a single ordered submission package (per-section documents + combined report) suitable for rPPP Stream One / grant round submission.

### F14. Provenance & confidence labeling ✅ principle, enforce everywhere

Every output number carries basis (`real_brief`, `sourced_benchmark`, `estimate`) and confidence. Never silently present a guess as a fact.

## 5. Screen inventory

| #   | Screen                                                                                                               | Status                            |
| --- | -------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| S1  | Dashboard (run center): project select, agent select, run, summary, budget table, scope comparison, raw JSON, export | ✅ Built                          |
| S2  | Project Library: list/validate/create/edit projects via guided form → writes `project_data.json`                     | ⬜ Future (post-backend-solidity) |
| S3  | Knowledge Base viewer/editor: browse and edit knowledge JSON with source/confidence fields visible                   | ⬜ Future                         |
| S4  | Run History & Package Assembler: past runs per project, select sections, compile package                             | ⬜ Future (F13)                   |
| S5  | Settings: Replicate API token, Blender path/port — only if A8 stays live                                             | ⬜ Future                         |

Current scope of build work is S1 + the agents behind it. S2–S5 are specified now so the data model doesn't preclude them, built only when the owner raises UI.

## 6. Non-functional requirements (carried forward verbatim in force)

Local-first (Windows, Python 3.12, no GPU) · no fabricated precision · cultural sensitivity as a functional requirement · confidentiality (briefs marked PRIVATE AND CONFIDENTIAL; no external data-handling until A7 resolved) · out of scope by owner direction: cloud/Docker, LLM-narrative layer, UI polish, auth, CI pipeline.

## 7. Success metrics

1. Both real projects generate a complete submission-supporting package end-to-end.
2. Zero silent wrong numbers — every figure traceable to basis + confidence (the $98M-on-an-$8M-project class of bug must be structurally impossible to ship).
3. Owner completes a full run + export without touching code or asking a developer.
4. Results demonstrably differ between the two real projects (hardcode detector).

---

# DOC 2 — `TRD.md` (Technical Requirements Document)

_Purpose: the continuing AI agent makes **zero** technical guesses. Everything below is decided._

## 1. Stack (locked)

| Layer         | Choice                                                   | Version / notes                                                              |
| ------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Language      | Python                                                   | **3.12.x** (owner's machine)                                                 |
| Web framework | FastAPI                                                  | current stable; HTTP layer only — no agent logic in `app.py`                 |
| Server        | uvicorn                                                  | run via `python app.py`                                                      |
| Validation    | `jsonschema`                                             | **Draft-07**, schema at `data/schemas/project_schema.json`                   |
| Frontend      | Vanilla HTML/CSS/ES6                                     | single file `static/dashboard.html`, **no build step, no framework, no npm** |
| Datastore     | Filesystem JSON (UTF-8)                                  | no database in current scope                                                 |
| Testing       | Manual dual-project harness now; **pytest** planned (B5) | see Implementation Plan Stage 2                                              |
| OS            | Windows 10/11                                            | all paths via `pathlib`; never string-concatenated separators                |

**Explicitly banned in current scope:** Docker, cloud services, databases, auth libraries, JS frameworks, LLM API calls inside calculation agents.

## 2. Optional integrations (must degrade gracefully)

| Integration                    | Trigger                                          | Protocol                                        | Degraded behavior                                                                                                                   |
| ------------------------------ | ------------------------------------------------ | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Replicate** (2D render)      | `REPLICATE_API_TOKEN` env var set                | Replicate Python SDK, Stable Diffusion          | Skip rendering; designs + drawing register still complete; output marks `rendering: "unavailable"`                                  |
| **Blender** (3D)               | Blender running locally with MCP addon listening | Socket bridge (`blender_bridge.py`)             | Skip 3D; mark `model_3d: "unavailable"`. **Security note B3 applies** — parameterize, never string-interpolate into exec-equivalent |
| **Project Architect** (export) | User clicks Export                               | One-way JSON file matching Base44 entity schema | N/A — always available                                                                                                              |

## 3. HTTP API contract (`app.py`)

```
GET  /                          → serves static/dashboard.html
GET  /api/projects              → [{name, valid, last_modified}]
GET  /api/projects/{name}       → validated project_data.json (422 with readable errors if invalid)
GET  /api/agents                → [{name, description, dependencies[]}] from registry
POST /api/run                   → body {project: str, agents: [str]} → full Orchestrator report
POST /api/export/project-architect → body {project, agents} → export JSON (Content-Disposition: attachment)
```

Rules: the API adds **no** logic; long runs return per-agent status in the report (sync is acceptable at current scale — no job queue needed).

## 4. Code standards (non-negotiable, encoded from real bugs)

1. **BaseAgent contract** — implement `get_required_inputs()`, `validate_inputs()`, `process()`; output via `self.format_output()`.
2. **`__init__` passthrough** — any override must accept and pass `upstream_results` (TypeError bug hit twice).
3. **No hardcoded per-project values** — everything via `self.get_project_data(path)` or knowledge files.
4. **Location normalization** — `.strip().lower().replace(" ", "_")` both sides of any location-keyed lookup.
5. **Schema strings ≠ enums** — explicit mapping dicts with fallbacks (`"3x2"` is not a typology).
6. **Output shape changes** → grep all consumers (`Orchestrator._build_summary`, `dashboard.html` JS, `project_architect_export.py`) — this bug class has recurred.
7. **Docstrings carry the "why"** — every fix gets a comment block explaining what was found and why the fix works (the code is the source of truth).
8. **Optional deps** — module-level `X_AVAILABLE` flags, try/except imports, never crash `process()`.
9. **Read `AGENT_MIGRATION_PLAYBOOK.md` before building any agent.** No exceptions.

## 5. Portability notes (for a future stack move — recorded, not built)

The JSON-schema data contract and the agent-output envelope are stack-neutral. A future move (Postgres/Supabase, Django/.NET) maps 1:1: `project_data.json` → document/JSONB column or normalized tables (see DOC 5 §6); `KnowledgeLoader` → seeded tables; FastAPI endpoints → equivalent routes; dashboard → any SPA. Nothing in the current design hard-couples to Python except the agents themselves, which are portable as pure functions of (project data, knowledge, upstream results).

---

# DOC 3 — `APP_FLOW.md` (Screen & Interaction Flow)

## S1 — Dashboard (current, authoritative spec)

```
┌────────────────────────────────────────────────────────┐
│ 5HORSES PLATFORM          [Project ▼]  [Run Selected]  │
├──────────────┬─────────────────────────────────────────┤
│ AGENTS       │  SUMMARY PANEL                          │
│ ☑ planning   │  (headline figures per run)             │
│ ☑ cost       │  ── ITEMIZED BUDGET TABLE ──            │
│ ☑ architect  │  ── TWO-SCOPE COST COMPARISON ──        │
│ (checkboxes  │  ── FULL RAW JSON (collapsed) ──        │
│  from GET    │                                         │
│  /api/agents)│                    [Export → Project    │
│              │                     Architect]          │
└──────────────┴─────────────────────────────────────────┘
```

### Flow 1 — Page load

1. `GET /api/projects` → populate Project dropdown. If zero projects: empty state ("No projects found in data/projects/").
2. `GET /api/agents` → render agent checkboxes with names + one-line descriptions; show dependency hints ("cost uses planning output").
3. Default state: first project selected, **all** agents checked.

### Flow 2 — Run

1. User clicks **Run Selected** → button disables, label "Running…", per-agent status list appears (pending → running → ✓ / ✗).
2. `POST /api/run {project, agents}`.
3. **Success (all agents):** render Summary Panel → Budget Table → Scope Comparison; raw JSON collapsed below.
4. **Partial (agent error):** render everything that succeeded; failed agents shown with their error message inline — **never** a silent omission, **never** a full-run failure.
5. **Project load failure:** single clear error banner (schema validation message), no per-agent noise (fail-fast-once behavior).

### Flow 3 — Inspect results

- Summary figures are clickable → scroll to the corresponding section in raw JSON.
- Raw JSON section: collapsed by default, expand toggles, monospace.
- Budget table rows show basis/confidence indicator per line (ties to F14).

### Flow 4 — Export

1. Click **Export** → `POST /api/export/project-architect` → browser downloads JSON.
2. Confirmation toast: "Export downloaded — import manually into Project Architect (no live sync)."

## S4 — Package Assembler (future, specified now)

Select project → list of past runs (grouped by agent, timestamped) → check sections in a suggested DA/submission order (planning → environmental/heritage → cost/feasibility → design → risk → delivery plan) → **Compile Package** → single document (Markdown/PDF) with cover page, table of contents, per-section provenance appendix.

## Global interaction rules

- Every long operation shows progress; nothing spins silently.
- Every error is specific and human-readable (schema path, agent name, reason).
- Every number displays its basis (real / sourced / estimated) — a number without provenance is a UI bug.
- No destructive actions exist in current scope (runs are pure; outputs regenerate).

---

# DOC 4 — `UI_UX_DESIGN_BRIEF.md`

**Status framing:** the owner has explicitly deferred UI polish. This brief has two tiers: **Tier N (now)** — minimum standards the functional dashboard must already meet; **Tier P (polish phase)** — the full design system, applied only when the owner raises UI.

## 1. Design principles

1. **Trust through provenance.** The product's soul is "no fabricated precision." Every displayed number carries a source tag and confidence badge. This is the single most important UI rule.
2. **Calm professional-services aesthetic.** This is a tool that produces funding submissions — it should feel like a quantity surveyor's report, not a game.
3. **Cultural respect.** No decorative use of Aboriginal art, motifs, or iconography anywhere in the UI without explicit consultation with the relevant Corporations. Correct, consistent naming of both projects and Corporations. Location-keyed cultural content must render exactly as authored — never paraphrased by UI.
4. **Progressive disclosure.** Headline summary first; itemized detail second; raw JSON last and collapsed.
5. **WCAG 2.1 AA** contrast; keyboard-navigable controls; tabular numerals for all currency.

## 2. Typography (Tier P)

| Use             | Face                                            | Notes                 |
| --------------- | ----------------------------------------------- | --------------------- |
| UI + headings   | **Inter** (or system-ui fallback)               | weights 400/600/700   |
| Data / currency | Inter with `font-variant-numeric: tabular-nums` | columns never jitter  |
| JSON / code     | **JetBrains Mono** / Consolas fallback          | 13px, 1.5 line-height |
| Scale           | 12 / 14 / 16 / 20 / 28                          | 28 = page title only  |

## 3. Colour palette (Tier P)

| Token            | Hex       | Use                                                       |
| ---------------- | --------- | --------------------------------------------------------- |
| `ink`            | `#1F2937` | primary text                                              |
| `slate-bg`       | `#F5F7F6` | page background                                           |
| `card`           | `#FFFFFF` | panels                                                    |
| `eucalyptus`     | `#2F6B4F` | primary accent (WA land context) — buttons, active states |
| `sand`           | `#E8E1D5` | secondary surfaces, table striping                        |
| `sourced-green`  | `#2F6B4F` | confidence badge: real/sourced data                       |
| `estimate-amber` | `#B45309` | confidence badge: estimate / low confidence               |
| `variance-red`   | `#B91C1C` | variance ≥20% flags, errors                               |
| `info-blue`      | `#1D4ED8` | informational, dependency hints                           |

All pairings above meet AA on white. Confidence badges always pair colour with a text label ("sourced", "estimate", "low confidence") — never colour alone.

## 4. Component library (Tier P)

`ConfidenceBadge` · `SourceTag` (e.g. "Master Builders WA 2024", "Brief ver.6") · `AgentCard` (name, description, dependency chips, last-run status) · `RunStatusList` · `BudgetTable` (sticky header, right-aligned tabular currency, per-row provenance) · `ScopeComparison` (funded phase vs full potential, the latter visually secondary per A2) · `JSONTree` (collapsible) · `ErrorBanner` (specific, actionable) · `EmptyState`.

## 5. Tier N — minimum standards for the current dashboard

1. No number rendered without its basis visible somewhere in reach (tooltip or adjacent column is acceptable).
2. Failed agents always visibly reported — never silently absent.
3. Full-scope subdivision figures visually de-emphasized relative to funded-phase figures (pending A2, this is the safe default).
4. Plain language in all labels — the owner is non-technical ("Funded build cost", not "funded_phase.total").
5. No cultural imagery (see principle 3).

---

# DOC 5 — `BACKEND_SCHEMA.md` (Data Model & Contracts)

## 1. Core entity: `project_data.json` (validated against Draft-07 schema)

```
project
├─ name, type, location (lowercase_underscore), description
├─ site_area_ha, developable_fraction (default 0.7)
├─ land_tenure (freehold | peppercorn_lease | state_reserve | …), annual_lease_rent, land_cost
├─ parcels[]                      ← multi-parcel: per-parcel {lot, area_ha, tenure, buildable}
└─ rezoning {required, current_zoning, proposed_zoning}   ← first-class, preferred over tenure inference

buildings
├─ homes[]      {type: "3x2" (bed/bath shorthand — NOT a typology), area_sqm, count, cost_per_unit?}
├─ dorms[]      {…same shape…}
└─ commercial[] {name, type, area_sqm, cost_per_unit?}

infrastructure
└─ water | power | sewer | roads   ← real itemized figures (counts × cost_per) preferred over area-based estimates

funding
├─ model (nfp_grants | government | commercial | mixed | in_kind)
├─ named_program (e.g. "rPPP Stream One")
├─ sources[] {name, amount, status}
├─ in_kind_sources[] {provider, description, estimated_value, status}
└─ ongoing_revenue_streams[] {name, projections[]?}   ← ACCU-style multi-year; currently placeholder $0 (A3)

phases
└─ planning | infrastructure | construction | project_management
        {cost, …} + contingency          ← used by CostAgent cross-validation (≥20% variance → flagged risk)
```

**Top-level required: `project`, `buildings`, `phases`.** All extensions to date are backward-compatible optional fields; **never remove or change a required field**.

## 2. Knowledge base schemas (`src/knowledge/knowledge/`)

| File                             | Status | Structure                                                                                                                                                                                                                                                  |
| -------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `regional_pricing.json`          | ✅     | per-location land/construction/sale rates, each with `source`, `confidence`, `basis` (methodology: Perth base $1,000–1,250/sqm × documented regional multiplier — MBWA uplifts: Busselton +5%, Geraldton +7–10%, Broome +45%, Derby +50%; upper floor ≈2×) |
| `r_codes.json`                   | ✅     | WAPC R-Codes 2024: density, setbacks, open space, parking per code                                                                                                                                                                                         |
| `cost_code_groups.json`          | ✅     | Rawlinsons/AS1181-pattern group-level taxonomy                                                                                                                                                                                                             |
| `location_zoning.json`           | ⬜ B1  | shared subdivision-density lookup (currently duplicated in two agents — consolidate)                                                                                                                                                                       |
| `environmental_constraints.json` | ⬜ B2  | required by untested LUMO-lineage code                                                                                                                                                                                                                     |
| `dwelling_sizes.json`            | ⬜ B2  | typical areas per typology — **default only**, never overrides real `area_sqm`                                                                                                                                                                             |
| `wa_planning.json`               | ⬜ B2  | WAPC/local planning pathway reference                                                                                                                                                                                                                      |

**Rule:** agents consume via `self.knowledge.get_knowledge(key)`; editing a file must never require a code change; verify the agent actually calls it (bug #7).

## 3. Agent output envelope (contract)

```json
{ "agent": "cost", "status": "success | error",
  "results": { …agent-specific… },
  "errors": [ …per-agent only… ],
  "meta": { "basis_fields": ["dwelling_basis", "cost_source_used"], "timestamp" } }
```

Any change to `results` shape → grep consumers: `Orchestrator._build_summary`, `dashboard.html`, `project_architect_export.py` (bug #8 class).

## 4. Orchestrator report

`{ project, run_timestamp, summary, agent_results: {name → envelope}, execution_order, dependency_map }` — with `completed_results` actually populated for injection (bug #9).

## 5. Project Architect export entities (one-way seed)

`Project, ProjectPhase, BudgetItem, Deliverable, RiskItem, FundingSource, ComplianceItem` — RiskItems carry explicit "neutral default, not computed" notes where no agent computed them.

## 6. Future relational mapping (only if A6 cloud is approved — not built now)

`projects → parcels`, `projects → buildings → units`, `projects → infrastructure_items`, `projects → funding_sources / in_kind_sources / revenue_streams / phases`, `projects → runs → agent_runs (output JSONB)`, `knowledge_documents (key, body JSONB, source, confidence)`.

## 7. Authentication (future, gated by A6+A7)

Current: **none, deliberately** (local single-user). Future model when cloud-hosted: OIDC (email + magic link minimum); roles `owner / staff / viewer`; **tenancy by Corporation** — each proponent Corporation's data isolated per tenant; no Corporation's data viewable by another; export/approval workflow before any external sharing. Confidentiality policy (A7) must be resolved **before** any of this is built.

---

# DOC 6 — `IMPLEMENTATION_PLAN.md` (Step-by-step, gated)

_Each stage lists tasks, touched files, and Definition of Done. Do not skip gates. Every agent task inherits the Migration Playbook's dual-project test discipline automatically._

## Stage 0 — Baseline verification _(owner, 30 min)_

Run `python app.py`, run both projects with all 3 agents, inspect output. Git tag `handoff-baseline`. **Gate:** known-good state confirmed before anything else.

## Stage 1 — Business decisions _(owner; nothing else blocks on all of these, but A1 blocks Stage 3)_

Answer A1 (role priority) · A2 (subdivision-scope prominence) · A3 (carbon/ACCU data or accept $0 placeholders) · A4 (Mount Barker quotes or accept flagged estimate) · A8 (Blender priority). Record answers in `OPEN_DECISIONS.md`. **Never fabricate data to un-block a gate.**

## Stage 2 — Technical debt sprint _(dev, no owner input needed)_

- **T2.1** Extract `location_zoning.json`; refactor PlanningAgent + CostAgent to shared lookup. _DoD: dual-project run identical results; one lookup, zero duplication._
- **T2.2** Build the 3 missing knowledge files from real sourced data (B2).
- **T2.3** Create `tests/` pytest suite encoding the manual dual-project checks: schema-valid both projects, plausibility assertions (cost within order-of-magnitude of funding), per-location lookup verification, "projects produce different outputs" assertion. _DoD: `pytest` green = the manual checklist, automated._
- **T2.4** Harden `blender_bridge.py` against injection (parameterized/whitelisted) — cheap now, mandatory before any external input path (B3).

## Stage 3 — Agent Wave 1 _(per A1; recommended: `environmental_heritage_agent`, `risk_register_agent`)_

- Environmental/heritage: both real projects have live Aboriginal cultural-heritage requirements; consume `environmental_constraints.json`; location-keyed cultural content handled per playbook checklist.
- Risk register: **real** cross-agent aggregation via `get_upstream_data(planning, cost, architect)` — the previously-simulated behavior, now genuine. Wire `AGENT_DEPENDENCIES` entries as built, not speculatively.
  _DoD per agent: playbook contract, bug checklist passed, dual-project output printed and inspected, consumers grepped, docstring "why" written._

## Stage 4 — Agent Wave 2 _(per A1)_

`geotech_agent` → `civil_structural_agent` (depends on geotech soil data) → `business_case_agent` (depends on cost). Same DoD.

## Stage 5 — Package assembler (F13, S4)

End-to-end run per project → compile ordered submission package with provenance appendix. _DoD: owner exports a complete Gnowangerup funding-round package and a Heritage Sanctuary rPPP Stream One package without help._

## Stage 6 — Integrations _(owner-gated)_

Blender real-instance verification (needs owner's Blender + MCP addon running) · Project Architect import path investigation (needs Base44 account access). Both skippable per A5/A8 answers.

## Stage 7 — UI polish _(only when owner raises it)_

Apply DOC 4 Tier P system to dashboard; build S2/S3/S5 screens if wanted.

## Stage 8 — Deployment _(only after A6 + A7 resolved)_

Containerize → host per A6 target → implement DOC 5 §7 auth + tenant isolation → confidentiality controls → backup regime. **Premature before Stages 3–5 are solid, per the owner's own sequencing.**

## Standing rules (carry forward)

- No agent built without reading the Migration Playbook.
- Nothing marked done without dual-project runs and **reading the output**.
- Don't re-import LUMO/QWEN-lineage code — ideas only, already folded in.
- Don't build deployment/UI/auth ahead of the owner asking.

---

**How to use this suite:** load these six documents alongside the original seven handoff docs and the Tier-1 code files. A continuing agent should read `HANDOFF_START_HERE.md` → this suite in order → then execute `IMPLEMENTATION_PLAN.md` from Stage 0, treating DOC 2 as the no-guesses technical authority and DOC 1 §3 as the definition of done. Want me to adjust any document — e.g., expand the App Flow for a future screen, or re-order the implementation stages around a different A1 priority answer?
