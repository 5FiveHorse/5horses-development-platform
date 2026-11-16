# Redaction Notice — Pilot Project Data

The project data files in this folder are **public redacted copies** of real, active
community development projects in Western Australia.

## What was redacted and why

The source briefs for both pilot projects are marked **PRIVATE AND CONFIDENTIAL** and
belong to their respective Aboriginal community corporations. Under the platform's
data-confidentiality policy (owner decision A7), full project documents may only be
read after administrative authorisation.

Redacted in these public copies:

- **All dollar figures** — construction cost-per-unit, infrastructure costs, phase
  budgets, funding source amounts, and funding targets (`null` in these files).
- **Lease particulars** — remaining term and annual rent.
- **Site-identifying detail** — lot numbers, wider landholding descriptions, and
  corporation-identifying particulars in the site description.

## What was kept, and why

Project structure, tenure type, site area, dwelling typologies and counts, phases,
and descriptions are retained so that the platform's data schema and agent logic can
be understood and exercised against realistic project shapes. Dwelling counts for
these projects are already publicly disclosed by the proponent.

## Structure integrity

Redacted fields are set to `null` rather than removed, so each file remains a valid
instance of the platform's `project_schema.json` — the schema treats all cost fields
as optional, and the costing agents flag `null` inputs as "estimate required" rather
than fabricating figures. The unredacted originals are held by the platform owner
under administrative authorisation.

## Requesting access

Legitimate requests for the full project data should be directed to the platform
owner, who will seek the relevant corporation's consent before any release.
