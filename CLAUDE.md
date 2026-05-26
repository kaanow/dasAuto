# CLAUDE.md — BC Family Vehicle Browser
<!-- IMPORTANT: Every Claude session working on this project must update this
file with any new architectural decisions, changed behaviour, or in-progress
work before ending. Keep it concise and factual. This file is the source of
truth for project state — do not use user-level memory for project details. -->

## Project summary
Local Flask web app for browsing 12 candidate family vehicles.
Companion to a spreadsheet/PDF comparison project for a Vancouver BC family.
Run with: `cd vehicle-app && python app.py` → http://localhost:5000

## Stack
- Flask + Jinja2 templates
- HTMX for partial page updates (re-ranking, listings fetch)
- SQLite (`data/cache.db`) for listing cache, notes, favourites
- Plain CSS (`static/css/style.css`) — no build step
- BeautifulSoup scraper for AutoTrader.ca and Craigslist Vancouver

## Repo layout
All app code lives in `vehicle-app/`. Root holds research/handoff docs only
(`HANDOFF.md`, `IMAGE_RESEARCH_BRIEF.md`, `TCO_RESEARCH_BRIEF.md`,
`TCO_RESEARCH_RESULTS.md`, this file). The previous flat-dump of root copies
was removed May 2026.

## Architectural decisions
- **Scoring:** 1 continuous TCO score (weight 3.0) + 8 qualitative criteria (1-5).
  TCO score = 1 + 4×(max_TCO − this_TCO)÷(max_TCO − min_TCO). This replaced
  5 separate financial sub-scores that were double-counting residual value.
- **Weight threading:** Custom weights set on the index sidebar flow through
  to `/vehicle/<id>` and `/compare` via `?w_<key>=<value>` query params,
  encoded by JS at click time only when they differ from defaults. The detail
  page rank/score and the compare page selector ordering both reflect the
  user's current weights, not the static `rank` field in vehicles.json.
- **TCO methodology (Apr 2026):** Per `TCO_RESEARCH_RESULTS.md`, costs are
  modelled with escalating prices discounted to present value:
  - Gas $1.79/L base, +3.5%/yr nominal escalation
  - Home electricity $0.1172/kWh base, +4.5%/yr blended
  - DCFC $0.40/kWh base, +3.5%/yr
  - Nominal discount 5.5% (3.0% real + 2.5% CPI)
  Per-vehicle `fuel_10yr` is computed by applying the new NPV-per-unit factors
  to the original analyst's powertrain-bucket consumption shares (ICE/Hybrid:
  100% gas, PHEV: 50/50 gas/home, BEV: 85/15 home/DCFC). Net rate-only effect
  vs the prior flat-rate model is small: gas −0.3%, hydro −10.1%, DCFC −3.3%,
  and the ranking is unchanged.
- **Re-ranking:** Server-side via `/rerank` POST returns card partial HTML.
  Weights are editable number fields (user preference; not sliders).
- **Listings:** AutoTrader scraped + cached 12 hr in SQLite. Craigslist
  scraped fresh each time. Kijiji/CarGurus/Facebook are deep links only.
- **Scope plumbing:** Vancouver / BC / Canada scopes pass through to the AT
  URL builder via `SCOPES[scope]` (sets `prov` path segment, `prx`, `loc`,
  `prv`). National scope correctly uses `/ca/` and drops `prv=`. CarGurus
  deep link also varies by scope. Override URLs in vehicles.json (e.g. Grand
  Highlander's `mdl=`-based URL) are regex-rewritten in `autotrader_url()`
  to keep the four scope fields in sync.
- **Images:** Downloaded by `scrapers/fetch_images.py` from a curated
  `data/image_seeds.json` (list of `{id, images: [{url, type, caption}], notes}`
  per vehicle). Letterboxed to 900×600 on dark background (matches CSS
  `#14181e`), MD5-deduped per vehicle. Run with `--refresh` to clear and
  re-fetch. Generate `image_seeds.json` by handing `IMAGE_RESEARCH_BRIEF.md`
  to a research agent and saving the JSON it returns.
- **at_url_override field:** Grand Highlander needs `mdl=Grand+Highlander`
  on AT (slug-based URL returns unrelated Toyota inventory).
  Honoured by `autotrader_url()` in `scrapers/listings.py`.
- **No at_status filter:** AT's `sts=New/Used` filter is unreliable — returns
  wrong vehicles. Year range (`yRng=`) is the only reliable filter used.

## Known issues / watch list
- AutoTrader.ca uses Incapsula bot detection. Sandbox IPs get rate-limited
  after ~10 requests. Home laptop IPs are not affected.
- Craigslist relevance filter is fuzzy (make + any model word in title).
  Dealer spam occasionally slips through.
- `@lru_cache` on `load_vehicles()` returns the cached list by reference.
  Callers must shallow-copy with `{**v, ...}` before mutating (current code
  does); nested fields like `v["specs"]` must not be mutated in-place.

## In-progress / not yet done
- **`data/image_seeds.json` not yet generated.** Until it exists, the image
  fetcher exits with instructions. App falls back to placeholder divs.
- **Browser/CSS polish pass** — never run in a real browser.
- **Print stylesheet for compare page.**

## Key files
- `vehicle-app/data/vehicles.json` — all 12 candidates, scores, profile text, AT URLs
- `vehicle-app/data/cache.db` — SQLite, created on first run (gitignored)
- `vehicle-app/scrapers/listings.py` — scraper + deep link generators
- `vehicle-app/scrapers/fetch_images.py` — seed-file image downloader
- `vehicle-app/app.py` — all Flask routes
- `HANDOFF.md` — historical handoff notes from the original build session

## Last updated
May 2026 — session 3: removed flat-dump root duplicates and `files.zip`;
gitignored `cache.db` and `images/`; integrated TCO_RESEARCH_RESULTS.md
(NPV-adjusted fuel_10yr per vehicle, renormalized tco_score, no rank
changes); threaded weights through detail/compare so customised rankings
persist; fixed national scope to actually go national in AT URL + CarGurus
deep link; refreshed CLAUDE.md to match current code (HANDOFF.md retained
as historical record).
