# Open Decisions - 5Horses Development Platform

Lineage: an `OPEN_DECISIONS.md` from an earlier era exists in the
`5HORSE PROPERTY DEVELOPMENT PLATFORM 28_7_26` archive (outside this repo);
it belongs to that project and was left untouched. This file is this
repository's own decision ledger.

---
## 2026-11-16 - Gate 1 decisions (recorded after 20/20 green)
### Doctrine: JSON Schema `default` is annotation-only
`jsonschema` (draft-07) never inserts `default` values into an instance; a
`"default": 0` on a numeric field changes nothing at validation time. A
missing key passes (field not `required`); an explicit `null` violates
`"type": "number"`. Therefore: defaults belong to the agents, supplied at
compute time (`x or 0`, `default=10`) where a `data_quality` flag can record
that a fallback fired. Validation never presumes defaults were applied.
### Decision: separate redacted-pilot schema (Option C) considered and declined
Proposal was a second schema, `project_schema_redacted.json`, selected by
flag. Declined. One `project_schema.json` with explicit nullable types
(`["number", "null"]`) keeps redaction legible in the data itself, avoids
two artifacts drifting apart, and forces the withheld-vs-absent distinction
to be honoured everywhere. Redaction (policy A7) is represented as explicit
nulls - never fabricated zeros - and agents must treat a withheld value
(proceed, flag partial results) differently from an absent one (refuse).
### Status after Gate 1
Test suite: 20 passed, 0 failed (`platform/tests/` +
`platform/test_blender_connection.py`). Verified 2026-11-16, commit c7fe176.
