# FiveHorses Development Platform

**A multi-agent estate planning and construction development platform for community-led projects in Western Australia.**

This repository holds the recovered working codebase and governance documentation of a platform designed to produce consultant-grade development feasibility appraisals: a 26-agent architecture covering 30 professional roles (town planning, costing, risk, environment, valuation, heritage, and more), orchestrating into phased project reports against a validated project schema.

---

## Status — honestly stated

- **Specification:** complete. The full design suite, agent registry, and decision record document the platform's target architecture (26 agents, 30 roles, provenance discipline, verification gates).
- **Code (this tree):** a recovered Stage 3 working state (June–October 2026) implementing **16 specialist agents**, the orchestrator, a FastAPI web dashboard, the project schema and validator, a knowledge base of WA planning/costing data, and a test suite. Recovered from the original local build and committed here as the platform's first version-controlled baseline.
- **Validation:** Gate 1 verified 2026-11-16 - full test suite 20/20 green (commit c7fe176). Gates 2 (dual-project web run) and 3 (Blender) are the next milestone - this project's discipline: no claim without real output.
- **Successor app:** an operator-side command centre ("5Horses Development OS") has also been built on Base44 under the Itinerate Building Co. banner, carrying the same doctrine into a hosted React stack.

## What's in this repo

| Path                      | Contents                                                                                                                     |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `platform/`               | The recovered Python/FastAPI working tree — agents, orchestrator, web app, schema, knowledge base, tests, two pilot projects |
| `platform/data/projects/` | Pilot project data, **publicly redacted** (see the README in that folder)                                                    |
| `docs/`                   | Governance corpus: design suite, decision record, agent registry, doctrine (being assembled)                                 |

## The two pilots

The platform was built against two real community development projects in Western Australia, proposed with Aboriginal community corporations: a community housing estate in the Great Southern, and a commercial/cultural precinct in Mount Barker. Their data files are published **redacted** — every dollar figure, lease particular, and identifying detail is set to `null` under the platform's confidentiality policy, because the source briefs are private and belong to the corporations. The redaction method and rationale are documented in `platform/data/projects/README.md`; that restraint is a feature of this project, not a gap.

## Engineering doctrine

This platform was built with a strict no-fabrication discipline:

- **Every number ships with provenance** — real project data, sourced benchmark, estimate, or not-yet-verified.
- **Agents may flag gaps; they may not invent precision.**
- **Cultural and confidentiality safeguards** are enforced in code and data handling, not just policy.
- **Owner-run verification gates** stand between "delivered" and "done."

## History

The platform's specification was developed across multiple AI-assisted build lineages (Ox Alpha as the primary engineering lineage), consolidated into a design suite and a twelve-decision ratified decision record, and partially implemented before this working tree was recovered and placed under version control. The full lineage story and decision record are being assembled into `docs/`.

## Running locally

```powershell
cd platform
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_web.py
```

Then open `http://localhost:8000`. The pilot projects load through the project loader and validate against `data/schemas/project_schema.json`.

---

**Maintainer:** 5FiveHorse — Western Australia.
**Purpose:** community-led development, construction, and cultural infrastructure appraisals at consultant grade.
