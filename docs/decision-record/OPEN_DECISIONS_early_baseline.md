# Open Decisions — Business vs. Technical

Two different kinds of open items remain. **Business decisions need the
project owner's judgment — no amount of further coding resolves them.**
Technical decisions can be made by whoever's continuing development, ideally
flagged to the owner but not blocking.

---

## A. Business decisions needed (owner's call, not code)

### A1. Priority order for the remaining ~27 professional roles
Which are actually needed before Gnowangerup's funding round and Heritage
Sanctuary's rPPP Stream One submission can be supported end to end? My
suggested priority, but this is the owner's call: environmental/ecological
assessment, heritage/cultural heritage management plan, geotechnical, civil
engineering, risk register, project manager, business case/economics. Roles
like valuation, asset management, and some specialist surveys may be lower
priority for an initial submission.

### A2. Full subdivision potential — keep, de-emphasize, or drop?
`CostAgent`'s `full_subdivision_potential` scope (land-banking/full-yield
framing) was built at the owner's explicit request to support "both
questions." But neither real project's stated mission (Aboriginal community
housing, cultural precinct) reads as land-banking-oriented. Is this genuinely
useful ongoing, or was it primarily to resolve the earlier "171 vs 10
dwellings" confusion? If the latter, it may be worth de-emphasizing in the
dashboard (currently shown prominently) now that the funded-phase scope is
solid.

### A3. Revenue modeling for non-grant-funded / mixed-revenue projects
`CostAgent`'s funding-gap-based feasibility only applies to `nfp_grants`/
`government` funding models. Heritage Sanctuary's `ongoing_revenue_streams`
(carbon credits, native seed sales) are all currently placeholder `$0` —
no real figures exist yet. Does the owner have or can obtain real carbon-
credit/ACCU revenue projections (mentioned in the brief as pending a
"baseline carbon stock assessment")? Without that, this revenue stream will
continue to show as unmodeled.

### A4. `mount_barker` construction rate — get real quotes?
Unlike Gnowangerup (real per-unit costs from an actual itemized brief),
Heritage Sanctuary's 4 commercial buildings (gallery/office/school/café)
still price off an **unvalidated estimate** ($1,200/sqm, explicitly flagged
low-confidence in `regional_pricing.json`). Does the owner have or can
obtain real builder quotes for these specific building types, the way
Gnowangerup's brief provided?

### A5. Project Architect integration — export/seed only, or deeper?
Current state: one-way JSON export matching Project Architect's schema, no
confirmed import mechanism into the live Base44 app. Is it worth
investigating Base44's actual API/import capabilities (would need Base44
account access to check), or is a manual copy-paste/import workflow
acceptable indefinitely? Alternatively — does the owner want to eventually
reproduce Project Architect as a custom app (a much larger undertaking,
per its own Portability/Reproduction Guide) rather than keep using Base44?

### A6. Deployment target and timeline
Currently strictly local (owner's Windows machine). Is cloud hosting ever
intended (for team access, or for the Aboriginal Corporations themselves to
view outputs), and on what timeline? This materially changes what security/
auth work is actually required vs. premature.

### A7. Data confidentiality requirements
Source briefs are marked "PRIVATE AND CONFIDENTIAL." No data-handling
policy has been defined for if/when this moves beyond local-only use
(cloud storage, who can access the two Aboriginal Corporations' project
data, whether either Corporation needs to approve/review before any
external hosting). This should be resolved **before**, not after, any
deployment decision (A6).

### A8. Real Blender rendering — still a priority?
3D rendering has never been tested against a real running Blender instance
— only mocked. Is generating actual 3D building models/renders still wanted
near-term, or has priority shifted elsewhere? If still wanted, the owner
needs Blender + the MCP addon running locally to test it.

---

## B. Technical decisions needed (can be made by whoever continues development)

### B1. Consolidate the duplicated location→zone-density lookup
Both `CostAgent` and `PlanningAgent` currently have their own hardcoded
`{"gnowangerup": 30, "mount_barker": 20, ...}` dict for subdivision-density
assumptions. Should move into a shared knowledge file
(`location_zoning.json`?) that both agents read, rather than two copies
that could drift out of sync.

### B2. Build the missing knowledge files
`environmental_constraints.json`, `dwelling_sizes.json`, `wa_planning.json`
are referenced by other (untested) agent code from LUMO's batch but don't
exist. Needed before any environmental/dwelling-sizing agent can be trusted.

### B3. Security hardening on the Blender bridge
Flagged early, never fixed: `blender_bridge.py` builds Blender-side Python
via raw string interpolation into an `exec`-equivalent call. If any building
name/type string ever originates from untrusted input, this is a real
code-injection surface. Low urgency while everything is local-only and
owner-controlled input; becomes real priority if A6 (cloud deployment) or
any external-input path is ever built.

### B4. Expand `AGENT_DEPENDENCIES`
Only one real cross-agent dependency exists (`cost` → `planning`). Future
agents will need real ones (e.g. `structural` → `geotech`, `risk_register`
→ nearly everyone). Build these as the underlying agents get built, not
speculatively ahead of time.

### B5. No automated test suite
Testing is currently manual (run against both real projects, inspect output)
per the Migration Playbook. Worth converting into an actual `pytest` suite
at some point so regressions are caught automatically — not urgent while
the team is a single owner + AI assistant working synchronously, but will
matter if more contributors join.

### B6. Dashboard/UI polish
Explicitly deferred by the owner. No action needed until they raise it.
