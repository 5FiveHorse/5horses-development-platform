# **5Horses Development Platform — Decision Record (Final)**

**PROVENANCE:** This record reconstructs the final state of OPEN\_DECISIONS.md as rewritten in the Ox Alpha lineage's "Decision Execution" delivery (2026), when all twelve owner decisions (A1–A12) and the three go-ahead gates were resolved by the App Administrator / Project Manager. Questions are preserved deliberately — with answers and rationale — so future sessions see what was decided *and why*. The earlier unresolved baseline is preserved as OPEN\_DECISIONS\_early\_baseline.md in this folder.

Reconstruction assembled 2026-11-16 during repository formation, from the Ox Alpha chat archives held in ../history/.

|  |
| - |

## **A. Business decisions — RESOLVED**

| **\#** | **Question (condensed)** | **DECISION** |
| - | - | - |
| **A1** | **Build order for remaining roles** | **MOOTED — all roles built (Wave 5); 30-role coverage complete** |
| **A2** | **Subdivision-potential view prominence** | **KEEP current default: funded phase prominent, full-site yield demoted to informational. Rationale: Gnowangerup may be Phase 1 of progressive development on the same site — full-yield visibility aids devising successive phases to realise the site's full potential** |
| **A3** | **Carbon/ACCU revenue projections** | **FORMALLY ACCEPTED $0 placeholders until baseline carbon stock assessment delivers real figures. Revenue streams remain honestly unmodelled; business\_case continues to flag as unmodeled** |
| **A4** | **Mount Barker commercial construction rate** | **RESOLVED WITH REAL DATA: WA 2026 indicative commercial construction $3,900–$6,500/sqm (gallery/school/café/office), varying by finishes/services. Zoned-rate allocation adopted per owner guidance (never one homogeneous rate). Source hierarchy supplied: Rawlinsons / RLB Riders Digest / AIQS index / QS elemental cost plan / WA Government tenders / BMT cross-check / contractor quotes. Implementation: regional\_pricing.json rebuilt; CostAgent prices commercial buildings by type-zone within the owner range; range sensitivity reported** |
| **A5** | **Project Architect integration depth** | **OPTION (c): reproduce Project Architect as a custom app eventually. Interim: structure integration facility with import/upload compatibility between the platforms. Export contract frozen (additive-only evolution); entities/endpoints documented for the future app** |
| **A6** | **Cloud hosting intent** | **YES eventually — primary driver: PM remote access while on site. Current user: App Administrator/PM only. Stage 8 deployed with auth; remote access via private tunnel first (Tailscale), public HTTPS optional** |
| **A7** | **Confidentiality rules** | **App Administrator/PM OWNS all documents. Host organisations/stakeholders access ONLY by Admin-granted permission. Any external hosting of organisation/corporation/contractor/stakeholder data requires Admin approval/review FIRST. Admin may set RETENTION PERIODS on access grants. Enforced in code: roles, per-project grants, grant expiry, audit log, approval checklist in DEPLOYMENT.md** |
| **A8** | **Blender massing permanence** | **WANTED PERMANENTLY, with clean ON/OFF: no errors when Blender isn't running, and NO background process persistently polling for a connection. Confirmed architecture already compliant: connection attempted ONLY inside an agent run when explicitly enabled; zero polling; 5-second timeout; graceful skip** |
| **A9** | **External use of AI-assisted renders** | **ACCEPTED recommendation: NO for formal submissions as-is; CONDITIONAL yes for community settings WITH explicit Corporation sign-off; always captioned "AI-assisted concept visualisation — indicative massing only, NOT a design". Caption enforcement stands; policy recorded here and in PRD NFRs** |
| **A10** | **Asset custodianship post-handover** | **The relevant community organisation/corporation holds each asset: the Aboriginal corporation holding the Gnowangerup housing assets; the corporation behind the Heritage Sanctuary precinct. (Named entities withheld in public copies per A7.) Implemented: project.custodianship added (schema-additive); asset\_management agent surfaces declared custodian instead of open prompts** |
| **A11** | **Tenure security acceptance** | **YES — funder accepts peppercorn/reserve tenure as secure-for-asset-life PROVIDED: duly executed lease for the asset lifespan (~40 yrs residential / ~39 yrs commercial, capital-works context) WITH clear permissions to erect the edifices. Proponent must demonstrate this in submission. Implemented via grant\_programs.json + legal\_governance\_standards.json (zero code change — knowledge-driven); grant\_compliance warning becomes a demonstrable-criteria checklist** |
| **A12** | **Livability mandate** | **50% Gold = program-QUALITY target, NOT automatically the funder's minimum. Statutory floor: NCC livable-housing provisions (≈Silver). Higher Gold/Platinum share may improve assessment scoring without being pass/fail. Do NOT claim 50% Gold mandated in the Gnowangerup application unless funding documents say so. Implemented: accessibility\_standards.json rewritten with three-tier distinction + approved application wording** |


## **C. Go-ahead gates — RESOLVED**

| **Gate** | **Decision** |
| - | - |
| **UI polish (Tier P + screens S2/S3/S5)** | **APPROVED — build (delivered as the UI-polish delivery: S2 Project Library, S3 Knowledge editor, S5 Settings)** |
| **LLM-narrative layer** | **DEFERRED BY DESIGN — leave architecture dormant; activate later. No code shipped** |
| **Stage 8 deployment** | **APPROVED — deployed (auth, Docker/Caddy/Tailscale kit), subject to the A7 pre-flight checklist before ANY external user is granted access** |


## **Known open residuals (as at the final Ox Alpha state)**

- **renewal\_provision\_holder** — which entity holds the asset-renewal funds — remained "(to be confirmed — account structure choice)" in both project files.

- **A4 follow-on** — Heritage Sanctuary's recorded phase budgets were annotated as HISTORICAL (pre-A4, based on the retired $1,200/sqm assumption), retained unchanged as the brief's recorded position, to be reconciled at next budget revision.

- **Owner-run bring-up gates** — test suites, dual-project runs, Blender verification — specified but without recorded transcripts of execution.

## **Related technical items (B1–B6)**

B1 shared zoning lookup (location\_zoning.json) — closed in Stage 2 · B2 missing knowledge files — closed · B3 Blender bridge hardening — closed · B4 dependency expansion — grew organically through Waves 1–5 · B5 test suite (pytest) — closed · B6 dashboard/UI polish — later approved and delivered.
