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
├── tests/test_smoke.py # 11 route + behaviour tests
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
  - **Maintenance, insurance:** linearly `× N / 10` (flat-rate
    methodology — no escalation/discount in the original totals).
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

## Pending work (specified, not yet built)

- **Warranty-cliff maintenance.** Add per-vehicle
  `warranty_years_remaining` in vehicles.json (cost-dominant
  powertrain warranty in years from purchase date). Replace
  `maint(N) = maint_10yr × N/10` in `tco.recompute_tco` with a
  two-rate model: in-warranty years cost less per year, out-of-
  warranty years cost more. Calibrate IN_FACTOR / OUT_FACTOR so
  the existing `maint_10yr` is preserved at N=10 (suggested 0.5 /
  1.5, ratio 1:3). See `user-kaan-and-tess/situation.md` for seed
  values per vehicle.
- **Weight-input precision.** Sidebar inputs reject `1.3` (default
  winter weight) because `step="0.5"`. Loosen to `step="0.1"` and
  round to 1dp in `parse_weights` server-side as a truncation
  belt-and-suspenders.

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

May 2026 — session 4: three-layer reorg. Split vehicles/image_seeds/
TCO research/cache.db/images into `user-kaan-and-tess/`. Extracted
`scoring.py` and `tco.py` from `app.py`. Parameterised app by
`VEHICLE_DATA_DIR` env var. Moved briefs into `vehicle-app/briefs/`,
HANDOFF.md into `vehicle-app/docs/`. Added `tests/test_smoke.py` (11
unittest cases, all passing). Updated launchers to honour the env var
and default to user-kaan-and-tess/.
