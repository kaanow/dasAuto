# CLAUDE.md — dasAuto Vehicle Picker (skill + multi-family deployment)

> **This file is architectural.** It describes the project skeleton, the
> separation between architectural and family-specific knowledge, and the
> non-negotiable rules that keep the multi-family deployment from drifting.
> It is not a session log and not family-specific. Family stories live in
> each family's `research/decisions_log.md`.

## What this project is

A Flask + HTMX app that ranks family vehicles against weighted criteria. It
runs as one repo serving multiple families, each at their own domain. Each
family's data lives in `user-<label>/`; the app code in `vehicle-app/`
serves whichever family the `VEHICLE_DATA_DIR` env var points it at.

Active deployments:
- `dasauto.alti2.de` → `user-kaan-and-tess/`
- `brudersauto.alti2.de` → `user-theo/` (stub at this writing)

## Repository layout

```
dasAuto/
├── CLAUDE.md                        # this file — architectural rules
├── README.md                        # user-facing readme + deploy guide
├── Procfile, requirements.txt       # Railway deployment glue
├── docs/                            # ARCHITECTURAL DOCS — apply to every family
│   ├── new_family_playbook.md       # the buildout sequence for a new family
│   ├── selection_principle.md       # hard-filter vs scored-criterion rule
│   ├── scoring_framework.md         # the 9 criteria + 1–5 rubric + formula
│   ├── tco_methodology.md           # NPV, warranty cliff, residual math
│   ├── brand_repair_tail.md         # Toyota 2.0× / Honda 2.5× / VW 4.8× table
│   └── tax_math_canada.md           # BC PST tiers, GST, dealer-fee taxonomy
├── vehicle-app/                     # SKILL — family-agnostic code
│   ├── app.py, scoring.py, tco.py
│   ├── repair_ratios.json           # brand×powertrain OOW-maint multipliers
│   ├── scrapers/, templates/, static/, tests/
│   ├── briefs/                      # research-brief templates for new families
│   └── docs/HANDOFF.md              # internal dev notes (pre-multi-family)
└── user-<family>/                   # one folder per family
    ├── family.md                    # PURE FAMILY INPUT — the canonical brief
    ├── site.json                    # display identity (name, region, insurance ref)
    ├── weights.json                 # tunable importance weights
    ├── vehicles.json                # the cohort
    ├── image_seeds.json             # curated image URLs
    ├── images/                      # downloaded galleries
    ├── manual_listings.json         # AI-curated market listings
    ├── dealer_quotes/               # one JSON per active dealer quote
    │   └── <vehicle-id>.json
    └── research/                    # AI-generated research deliverables
        ├── tco_research.md          # family-region rate research
        ├── cohort_rationale.md      # why these vehicles, scoring narrative
        └── decisions_log.md         # session-by-session decision history
```

## Hard rules (do not violate)

### 1. Family-specific data NEVER lives in `vehicle-app/` or `docs/`

If you find yourself writing a family name, vehicle preference, or
region-specific value into those folders, stop. It belongs in
`user-<family>/`. The skill folder must serve any family by changing
`VEHICLE_DATA_DIR`.

### 2. Architectural knowledge NEVER lives in `user-<family>/`

If you find yourself documenting the TCO model, the scoring formula, the
selection principle, or any other family-agnostic fact inside a family
folder, stop. Lift it to `docs/`. The family folder is for what *they* told
you and what you *researched for them*, not how the system works.

### 3. `family.md` is the canonical record of original intent

It's the file the family gives you. **Do not edit it** to capture
clarifications or research findings. Those go in
`research/decisions_log.md`. The brief is the spec; the decisions log is
the change log.

### 4. The selection principle (see `docs/selection_principle.md`)

A trait is a HARD filter only if it would make the vehicle structurally
infeasible. A trait that varies by degree must be a SCORED criterion —
never both. The kaan-and-tess "AWD-minivan" bug taught us this; don't
repeat it.

### 5. Surface drift explicitly

If `family.md` says X and the current cohort assumes Y, that's drift.
**Ask the family** rather than silently working around it. Document the
resolution in `research/decisions_log.md`.

### 6. At session start, verify the brief is present

Check `user-<family>/family.md` exists before doing structural work. If
absent, ask the user to provide it. Drift starts when sessions trust the
current state without consulting the original spec.

## Multi-family considerations

### Adding a new family

Follow `docs/new_family_playbook.md` end-to-end. The short version:

1. Create `user-<label>/`
2. Have the family fill in `family.md` from `vehicle-app/briefs/family_brief_template.md`
3. Run through the playbook (intake → criteria → cohort → TCO → images → deploy)
4. Provision a Railway service pointed at the new folder
5. CNAME a subdomain

### Working on multiple families in one Claude project

Currently both `user-kaan-and-tess/` and `user-theo/` live in the same repo
and are worked on from the same Claude project. **Each family's data is
isolated by folder**, and the Railway services are independent. When
working on a family:

- Read *their* `family.md` first
- Read *their* `research/decisions_log.md` for context on prior choices
- Don't borrow assumptions from the other family unless they're explicitly
  shared knowledge (those live in `docs/`)

### Session memory

Memory is per-Claude-project, not per-family. When this project's memory
references "the family" it implicitly means whichever family the current
work is about. Prefer writing durable decisions to
`user-<family>/research/decisions_log.md` over relying on session memory —
the log survives memory limits.

## Coding conventions

### Template + route changes

The app is family-agnostic; routes read from `VEHICLE_DATA_DIR`. When
adding a feature:

1. Don't hard-code a family name or family-specific path
2. Add config to `family.md` schema (or a sidecar JSON) rather than
   inferring family-specific behaviour from data presence
3. If the feature is vehicle-nameplate-specific (like the Sienna
   cross-shop), make the route parameterised: `/cross-shop/<vehicle-id>`,
   not `/siennas`

### Testing

`vehicle-app/tests/test_smoke.py` runs against
`VEHICLE_DATA_DIR=user-kaan-and-tess/` by default. When adding a test, use
`load_vehicles_all()` to find any vehicle matching a criterion rather than
hardcoding a specific id — that way the test survives soft-archival and
data evolution.

### Deploying

See `README.md` § "Deploying to Railway." The pattern: one Railway service
per family, both reading from the same repo's main branch, differentiated
by env vars (`VEHICLE_DATA_DIR`, `VEHICLE_DB_PATH`).

## Where the family-specific story lives

This file used to contain a long "Last updated" changelog of kaan-and-tess
sessions. That was a category error: session stories are family-specific,
not architectural. The kaan-and-tess history is now in
`user-kaan-and-tess/research/decisions_log.md`. Future sessions on either
family should append to *their* decisions log, not this file.

This file changes only when the **architecture** changes (folder structure,
deployment model, code conventions, the rules above). If you're tempted to
add a session note here, ask whether it's truly architectural — almost
always the answer is no.
