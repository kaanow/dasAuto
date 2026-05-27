# CLAUDE.md — dasAuto Family Vehicle Picker
<!-- Update this file with any architectural decisions, changed
behaviour, or in-progress work before ending a session. Source of
truth for project state — do not rely on user-level memory. -->

## Project summary

Local Flask + HTMX app that scores a shortlist of family vehicles
against weighted criteria with live listings deep links. Originally
built for the kaan-and-tess household (Vancouver BC); structured so
the skill folder can be lifted for a different family.

## Three-layer architecture

```
dasAuto/
├── vehicle-app/           # SKILL — reusable framework
└── user-<family>/         # SITUATION (inputs) + WORK PRODUCT (outputs)
```

The skill is parameterised by `VEHICLE_DATA_DIR` (env var). With it
unset, the app defaults to `../user-kaan-and-tess/`. Anything specific
to a particular family (candidate list, scores, weights, TCO research,
images) lives in the user dir; the skill folder contains no
family-specific names.

## Skill layout

```
vehicle-app/
├── app.py             # Flask routes; loads paths from $VEHICLE_DATA_DIR
├── scoring.py         # 9-criterion definitions + weighted-sum + ranker
├── tco.py             # NPV-per-unit + powertrain consumption mixes
├── scrapers/
│   ├── listings.py    # AT + CL + deep-link generators
│   └── fetch_images.py # seed-file image downloader (Wikimedia-friendly UA)
├── templates/, static/
├── briefs/            # research-brief templates (image, TCO)
├── docs/HANDOFF.md    # original build session notes
├── tests/test_smoke.py # 17 route + behaviour tests
├── requirements.txt
└── run.sh, "Launch Vehicle Browser.bat"
```

## User folder contract

```
user-<family>/
├── situation.md       # who/where/needs/weights rationale (human-readable)
├── weights.json       # importance weights {key: float}
├── vehicles.json      # list of candidate vehicles
├── image_seeds.json   # [{id, images: [{url,type,caption}], notes}]
├── tco_research.md    # local rate research backing TCO methodology
└── images/<id>/*.jpg  # downloaded galleries (gitignored)
```

`weights.json` is optional; the app falls back to a built-in default if
absent. Everything else must be present for the app to start.

## Architectural decisions

- **Scoring framework:** 1 continuous TCO score (weight 3.0 default) +
  8 qualitative criteria (1–5). TCO score = `1 + 4×(max−this)÷(max−min)`
  across the cohort. Replaces an earlier model with 5 financial
  sub-scores that double-counted residual.
- **Weight threading:** custom weights set on the index sidebar flow
  through to `/vehicle/<id>` and `/compare` via `?w_<key>=<value>`
  query params (JS appends them at click time only when they differ
  from defaults — clean URLs by default). Detail-page rank and
  compare-selector ordering reflect current weights, not the static
  `rank` field in vehicles.json.
- **TCO methodology (`tco.py`):** present-value with annual
  escalation. `npv_per_unit(FuelRate, discount)` computes a per-unit
  price multiplier; `adjust_fuel_10yr` re-scales an existing bucket
  total when rates change. Per-powertrain consumption mixes (ICE/Hybrid:
  100% gas, PHEV: 50/50 gas/home, BEV: 85/15 home/DCFC) are preserved
  so a rate change doesn't re-assert consumption assumptions. Family-
  specific base rates and escalation curves live in `tco_research.md`.
- **Variable TCO horizon:** all routes accept `?horizon=N` (4 ≤ N ≤ 15;
  default 10). On the fly, each vehicle's components are re-derived
  from the stored 10yr totals:
  - **Fuel:** `fuel(N) = fuel_10yr × NPV_factor_fuel(N) / NPV_factor_fuel(10)`
    using the powertrain's dominant fuel rate (gas for ICE/hybrid, a
    50/50 mix for PHEV, an 85/15 mix for BEV). Captures the
    NPV-weighted time tilt rather than just N/10.
  - **Maintenance:** per-year rate model. Each vehicle carries three
    horizon-independent inputs:
    - `warranty_years_remaining` — years of the cost-dominant
      powertrain warranty left at point of purchase (battery for
      hybrid/PHEV/BEV; powertrain for ICE).
    - `maint_in_per_year` — CAD/yr while covered (scheduled
      maintenance: oil/filters/brakes for ICE; minimal items for
      BEV; small for Toyota hybrid).
    - `maint_oow_per_year` — CAD/yr once the cost-dominant warranty
      has expired (scheduled work + expected value of out-of-
      warranty repairs; varies by brand repair-tail).

    Formula at horizon N is a direct sum, no anchor or rescaling:
      `in_yrs   = min(N, warranty_years_remaining)`
      `out_yrs  = max(0, N − warranty_years_remaining)`
      `maint(N) = in_yrs × maint_in_per_year + out_yrs × maint_oow_per_year`

    Concrete (warranty=7, in=$1,400/yr, oow varies):
      Toyota (oow=$2,800):    N=7 $9,800  → N=10 $18,200 → N=15 $32,200
      Default (oow=$4,200):   N=7 $9,800  → N=10 $22,400 → N=15 $40,400
      Pacifica (oow=$5,600):  N=7 $9,800  → N=10 $26,600 → N=15 $48,800
    Pre-cliff years are identical across vehicles with the same in-
    rate; post-cliff years diverge linearly with the oow-rate.

    Vehicles missing per-year fields fall back to module defaults
    (`MAINT_IN_PER_YEAR_DEFAULT` = $1,500, `MAINT_OOW_PER_YEAR_DEFAULT`
    = $4,500, 1:3 ratio). The detail page exposes both rates and the
    warranty boundary so the user can see why each vehicle's curve
    looks the way it does.

    History: this replaces an earlier `maint_10yr` + `maint_oow_multiplier`
    schema (a 10-year aggregate input that was back-solved into per-
    year rates via denominator gymnastics). The per-year schema is
    mathematically equivalent at N=10 but the inputs are vehicle-
    intrinsic rather than horizon-locked, easier to source and
    validate, and more legible in the UI.
  - **Insurance:** linearly `× N / 10` (flat-rate methodology — no
    escalation/discount in the original totals).
  - **Residual:** exponential decay between `pretax` (t=0) and
    `resid_10yr` (t=10): `pretax × (resid_10yr / pretax)^(N/10)`.
    Front-loads depreciation correctly.
  - **TCO total:** `on_road + fuel + maint + ins − resid` at N.
  - **TCO score:** renormalized over the cohort's TCO range *at the
    chosen horizon* (so a vehicle's tco_score shifts when N changes).
  Slider in the index sidebar drives this live via HTMX; horizon
  propagates to detail/compare via `?horizon=N` query string.
- **Listings:** AutoTrader scraped + cached 12 hr in SQLite (per-family
  cache.db). Craigslist scraped fresh each time. Kijiji / CarGurus /
  Facebook are deep links only.
- **Scope plumbing:** Vancouver / BC / Canada scopes drive AT
  `prov`/`prx`/`loc`/`prv` together. National uses `/ca/`, drops
  `prv=British+Columbia`. CarGurus deep link likewise varies.
- **Images:** seed-file based. `data/image_seeds.json` lists curated
  URLs per vehicle; `fetch_images.py` downloads, letterbox-resizes to
  900×600 on `#14181e`, MD5-dedups. Wikimedia returns 429 for generic
  Chrome User-Agent → fetcher uses a contact-bearing UA per their
  policy.
- **AT URL overrides:** Grand Highlander needs `mdl=Grand+Highlander`
  (slug path returns unrelated Toyota inventory). Honoured via the
  `at_url_override` field; `autotrader_url()` regex-rewrites the
  `prov`/`prv` fields to keep scope in sync.

## Selection-filter principle (skill-level invariant)

When defining the candidate cohort for a new family, a trait is a HARD
filter only if it would make the vehicle **structurally infeasible**
(the family does not fit in it at all). A trait that varies by degree
must be a **scored criterion** — never both. We learned this in
session 5: an earlier "AWD/4WD available" hard filter pre-excluded
every minivan format despite the framework already having `winter`
and `fsr` as scored criteria. The minivan exclusion looked deliberate
but was an unrecognised modelling bug. The same shape of error nearly
excluded the Tesla Model Y under a 7-seat hard filter when a family
of five literally fits in a 5-seater.

A new user-data directory's `situation.md` should distinguish:
1. Hard filters — structural infeasibility (seats < household size,
   not in-market in the user's region).
2. Cohort-shape goals — diversity targets (span of powertrains, body
   styles); drive selection but aren't per-vehicle tests.
3. Scored, not filtered — drivetrain, ground clearance, hitch,
   warranty, etc. captured by the 1–5 criteria and TCO model.

## Known model simplifications

These are deliberate caricatures; document but don't pre-fix.
- **Single cost-dominant warranty boundary per vehicle.** The model
  collapses bumper-to-bumper (3yr typical), powertrain (5yr), and
  battery (8-10yr) into one `warranty_years_remaining` — the
  cost-dominant one. A multi-tier model (list of `(year, factor)`
  tuples) would capture the gentle ramps at 3yr/5yr that precede the
  big cliff at 10yr. Worth it only if a future user's situation is
  driven by mid-tier failures, not the battery tail.
- **Cliff is a hard step, not a ramp.** Real maintenance cost ramps
  up gradually as a vehicle ages. The 0.5/1.5 step is a useful
  caricature because the warranty boundary is the user's actual
  decision-relevant signal — but in-warranty year 1 is much cheaper
  than year 7, which the flat 0.5 factor doesn't capture.
- **Residual doesn't model the warranty cliff.** Out-of-warranty
  cars depreciate faster than in-warranty ones, but `residual_at`
  decays smoothly between `pretax` and `resid_10yr`. The CBB
  projections already bake in typical 10yr-old post-warranty
  discount, so the bias only shows up at short horizons (N=5–8 where
  the car is in-warranty and the smooth decay undervalues it).
- **Time anchoring.** `warranty_years_remaining` figures assume a
  purchase date matching the planning baseline (May 2026 for this
  household). If the actual purchase slides 6 months, every figure
  should shrink by 0.5. Not yet parameterised.

## Known issues / watch list

- AutoTrader.ca uses Incapsula bot detection. Sandbox IPs get rate-
  limited after ~10 requests. Home laptop IPs are not affected.
- Craigslist relevance filter is fuzzy (make + any model word in title).
- `@lru_cache` on `load_vehicles()` returns the cached list by reference.
  Callers must shallow-copy with `{**v, ...}` before mutating (current
  code does); nested fields like `v["specs"]` must not be mutated in-place.
- The visual UI hasn't been driven through a real browser in this
  session — only HTTP-response inspection. CSS expects letterboxed dark
  backgrounds (`#14181e`); confirmed visually for one screenshot but
  not exhaustively reviewed.

## Last updated

May 2026 — session 5: shipped warranty-cliff maintenance + weight-input
precision (both spec'd in session 4). Expanded cohort from 12 → 18:
added Sienna Hybrid new, Pacifica Hybrid (PHEV, used), Odyssey (used),
Carnival (used), and Tesla Model Y both new and used. Recomputed
tco_score across the new 18-vehicle cohort. Identified and fixed a
selection-filter modelling bug: AWD was both a hard filter and a
scored criterion, silently excluding every minivan format. Rewrote
the selection principle in situation.md as a skill-level invariant
(hard filter only for structural infeasibility). Added per-vehicle
`maint_oow_multiplier` (Toyota 2.0 → Stellantis 4.0) so post-cliff
maintenance reflects each brand's actual repair-tail; default 3.0
preserves back-compat for vehicles without the field. Then refactored
the maintenance schema from `maint_10yr + maint_oow_multiplier` (a
10-year aggregate back-solved into per-year rates) to direct
`maint_in_per_year + maint_oow_per_year` inputs: vehicle-intrinsic,
horizon-independent, easier to source, easier to extend to multi-
tier warranties later. Per-year rates are now surfaced on the
vehicle detail page ("$1,385/yr covered · $2,769/yr after · 7yr
warranty left"). Documented known model simplifications (multi-tier
warranty, gradual ramp, residual cliff, time anchoring) in CLAUDE.md
as deliberate caricatures. Tests: 17 passing.
