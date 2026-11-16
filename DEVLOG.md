# Development Log

Engineering milestones for the 5Horses Development Platform. Honest by doctrine: nothing is marked done unless real output has been read and verified by the platform owner.

---

## 2026-11-16 — Recovery and public baselining

- **Recovered** the Ox Alpha working tree (Stage 3 state, June–October 2026) from local storage: 16 agent lineage files (10 operating agents), orchestrator, FastAPI web app, project schema and validator, knowledge base loader, test files, and two live Western Australian pilot project datasets.
- **Established version control**: first repository baseline created on GitHub; subsequent history consolidated to a single clean commit during a confidentiality correction.
- **Redacted pilot financials** in line with the platform's confidentiality policy (Decision A7): budget figures, lease particulars, and proponent-organisation identifiers removed from all public files; redaction documented at `platform/data/projects/README.md`.
- **Committed the governance corpus**: the six-document design suite, the early unresolved decisions baseline, and the final decision record (A1–A12 with rationale).
- **Closed the record of the primary engineering lineage** with a sanitised archive index (`docs/history/`), in place of raw build-chat transcripts, which are withheld under the A7 model.

## Current state — honestly stated

| Component | State |
|---|---|
| Specification (PRD, TRD, schema, decision record) | Complete — 26 agents / 30 roles designed |
| Working code (this tree) | Stage 3 recovery — 10 agents operating |
| Knowledge base | 4 of ~24 knowledge files present |
| Validation | Gate 1 verified 2026-11-16 - full test suite 20/20 green (commit c7fe176). Gates 2 (dual-project web run) and 3 (Blender bridge) pending - next milestone. |
| Pilots | Two live WA community projects (data redacted in public copy) |

## Roadmap — what is needed next, in order

1. **Knowledge base completion (Tier 1):** the three foundation knowledge files (zoning, dwelling sizes, WA planning pathways) required by the existing 10 agents — restoration from the engineering record.
2. **Agent completion, Wave 2–5:** rebuilding the 16 designed agents to reach the full 26-agent registry (environmental/heritage, geotech, civil-structural, business case, risk register, project manager, utilities cluster, and twelve Wave-5 specialists).
3. **Knowledge base completion (Tier 2):** the seventeen companion knowledge files for the rebuilt agents.
4. **Validation:** the owner-run bring-up gates — full test suite, dual-project runs, real-output review. This converts "specification-complete, validation-pending" into "verified."
5. **Deployment (post-validation):** Stage 8 kit (auth, containerised hosting, private-tunnel remote access), gated on the A7 confidentiality checklist.
6. **Integration:** the frozen one-way export contract to the Project Architect consumer app (Decision A5).

Funding sought to resource items 1–4: completing and validating the platform against its two live pilot projects.

---

*Maintained by the platform owner. See `README.md` for the platform overview and `docs/decision-record/` for ratified decisions.*
