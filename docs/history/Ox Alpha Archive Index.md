# Project History — Ox Alpha Lineage Archive Index

> **STATUS NOTE (per Decision A7, confidentiality model):** The full chat archives of the
> Ox Alpha lineage are held privately by the platform owner and are deliberately
> **not published in this repository**. They contain working transcripts that reference
> confidential client-brief material belonging to the two pilot-project proponent
> organisations, which is released only under administrative authorisation.
> This index records what the archives contain and their role in the platform's history.
> The redacted project datasets and this index are the public-safe representations.
> Serious reviewers, funders, or partners may request supervised access.

---

## The Ox Alpha lineage — what it is

Ox Alpha is the platform's principal engineering lineage. Working through OpenRouter
across mid-to-late 2026, it took the 5Horses concept from a founding brief to a
26-agent working platform covering all 30 mapped professional roles, with a frozen
export contract, a twelve-decision governance record, a deployment kit, and a polished
operator UI. The recovered working tree in `/platform` is a Stage-3-era snapshot of
this lineage; the governance corpus in `/docs` is reconstructed from it.

## The archived files (held privately)

| File (private) | Size | Contents |
|---|---|---|
| Ox Alpha Original Chat — original | ~311 KB | The founding conversation: brief analysis, PRD formation, the three founding agents (PlanningAgent, CostAgent, ArchitectAgent), the seven handoff documents, the fragmentation diagnosis of the three rival lineages, and Waves 1–4 |
| Ox Alpha Original Chat — full | ~620 KB | The complete record: everything above plus Wave 5 (twelve specialist agents, 26-agent registry, ~120-test suite), the Blender bridge and verification script, the A1–A12 owner decisions with rationale, the Stage 8 deployment kit, and the UI-polish delivery |
| Ox Alpha Original Chat — part 2 | ~340 KB | The decision-execution and later-wave segment, substantially overlapping the full version |

## Chronology recorded in the archives

1. **Founding** — brief intake for two Western Australian community pilots: a regional community housing estate (Gnowangerup Community Housing) and a Mount Barker heritage-precinct commercial/education precinct (Heritage Sanctuary Precinct). Definition of "Complete": outputs capable of supporting real development-approval and funding submissions.
2. **Specification formation** — PRD, Technical Specification, and five companion handoff documents; the nine verified-fixed bugs; the data/logic-separation doctrine (single `project_data.json` per project, JSON Schema Draft-07, no hardcoded project values).
3. **Fragmentation diagnosis** — identification of three incompatible parallel lineages (the canonical JSON-schema/BaseAgent line; an untested 20-agent batch with a filename collision; an incompatible dataclass-based system), and the ruling that the canonical line would absorb the best of the others.
4. **Wave builds 1–5** — from 3 agents to a 26-agent registry covering all 30 mapped professional roles, each wave shipped with tests, dashboard integration, package assembly, and owner-run bring-up gates.
5. **Decision execution** — all twelve owner decisions (A1–A12) answered with rationale; see `../decision-record/DECISION_RECORD.md`.
6. **Hardening** — the Blender bridge rebuilt against injection risk and given a verification script; the export contract frozen (additive-only evolution).
7. **Deployment staging** — Stage 8 kit (auth, Docker/Caddy/Tailscale), governed by the A7 confidentiality checklist before any external access.
8. **UI polish** — the Tier P design system and the S2/S3/S5 screens.

## Where the public record lives

- `/platform` — the recovered working tree (Stage 3 era)
- `/docs/design-suite` — the six governing documents
- `/docs/decision-record` — the early unresolved baseline and the final A1–A12 record

## Standing honesty note

The archives' own bring-up discipline — nothing is claimed done without the owner
reading real output — is preserved here: the last owner-verified state is recorded
in the decision record's open-residuals section, and no claim in this repository
should be read as extending beyond it.
