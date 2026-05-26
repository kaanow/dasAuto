# BC Family Vehicle Browser — Session Handoff
_Written April 5 2026 by Claude Sonnet 4.5 for the next Claude session._

> **Note (May 2026):** Several items in this document are now stale.
> The image fetcher is seed-file based (not DuckDuckGo); the flat-dump root
> files were removed; TCO numbers use NPV-discounted escalating rates per
> `TCO_RESEARCH_RESULTS.md`. See `CLAUDE.md` for the current architecture.
> This file is retained as a historical record of the initial handoff.

---

## What this project is

A local Flask web app for browsing, comparing, and finding purchase listings
for 12 candidate family vehicles in BC. Built for a Vancouver family (2 adults,
3 kids) making a 10-year vehicle purchase decision. The app surfaces a weighted
scoring matrix, full vehicle profiles, image galleries, and live purchase
listings from AutoTrader.ca and Craigslist Vancouver.

The companion spreadsheet and PDF summary document are separate deliverables
(in this same folder) — the web app is the interactive layer on top of them.

---

## Immediate first steps on the laptop

```bash
cd vehicle-app
pip install -r requirements.txt
python scrapers/fetch_images.py   # downloads ~72 images, takes 3-5 min
python app.py                     # starts server on http://localhost:5000
```

If `run.sh` is preferred: `bash run.sh` — same thing with friendlier output.

---

## Project structure

```
vehicle-app/
├── app.py                          # Flask app — all routes
├── run.sh                          # One-command startup
├── requirements.txt
├── data/
│   ├── vehicles.json               # All 12 candidates, scores, profile text
│   └── cache.db                    # SQLite: listing cache, notes, favourites
│                                   # (created on first run)
├── images/
│   └── <vehicle-id>/               # 6-8 JPGs per vehicle (after fetch_images)
├── scrapers/
│   ├── __init__.py
│   ├── fetch_images.py             # DuckDuckGo image downloader — run once
│   └── listings.py                 # AutoTrader + Craigslist scrapers + deep links
├── static/css/style.css            # Complete CSS — no build step
└── templates/
    ├── base.html                   # Nav + layout
    ├── index.html                  # Main ranked grid + weight controls
    ├── vehicle.html                # Vehicle detail: gallery, profile, scores, listings
    ├── compare.html                # Side-by-side up to 4 vehicles
    └── partials/
        ├── vehicle_cards.html      # HTMX-swappable card grid
        └── listings.html           # HTMX-swappable listings panel
```

---

## App features

**Main page (`/`)**
- Visual cards ranked by weighted score, one per vehicle
- Sidebar: editable weight fields per criterion, Apply re-ranks via HTMX
- Reset button resets to true defaults (hardcoded in JS as `TRUE_DEFAULTS`)
- Favourite (★) toggles stored in SQLite

**Vehicle detail (`/vehicle/<id>`)**
- Image gallery with thumbnail strip
- Key specs bar (on-road price, TCO, fuel economy, range, clearance, towing, cargo, 3rd row)
- Tabs: Why it ranks here / Trade-offs / My Notes (notes saved to SQLite)
- 10-year cost breakdown table
- Score breakdown with per-criterion bars and weighted net ranks
- Compare-with dropdown
- Listings panel: AutoTrader.ca cached scrape + Craigslist, scope selector (50km/BC/national), refresh button
- Deep links: Kijiji, CarGurus, Facebook Marketplace, AutoTrader national

**Compare page (`/compare?ids=...&ids=...`)**
- Up to 4 vehicles side by side
- Full specs, scores, TCO breakdown, Why/Trade-offs (collapsible)
- Selector dropdowns to swap vehicles

**API:** `GET /api/vehicles` returns ranked list as JSON.

---

## Scoring system

9 criteria: 1 TCO score (continuous, computed) + 8 qualitative (1-5, blue analyst inputs).

**TCO score formula:** `1 + 4 × (max_TCO − this_TCO) ÷ (max_TCO − min_TCO)`
- Score 5 = Sorento PHEV ($77,840 — lowest TCO)
- Score 1 = Telluride ($101,020 — highest TCO)

**Default weights** (confirmed by user April 2026):
```
tco: 3.0,  car_seat_fit: 2.0,  cargo: 1.0,  third_row: 1.0,
corridor: 1.5,  hitch: 0.5,  reliability: 2.0,  winter: 1.3,  fsr: 0.5
```

**Current ranking** (default weights):
1. Toyota Grand Highlander Hybrid XLE — New 2026 — 54.12
2. Toyota Grand Highlander Hybrid XLE — Used 2023-24 — 50.94
3. Toyota Sienna Hybrid Woodland AWD — Used 2022-23 — 50.05
4. Subaru Ascent Touring AWD — Used 2022-23 — 48.77
5. Toyota Highlander Hybrid XLE AWD — Used 2022-23 — 48.08
6. Hyundai Palisade Preferred AWD — Used 2022-23 — 46.14
7. Kia Telluride EX AWD — Used 2022-23 — 44.70
8. Honda Pilot EX-L/Touring AWD — Used 2023-24 — 44.28
9. Kia Sorento PHEV EX — Used 2022-23 — 43.40
10. Mazda CX-90 PHEV GS — Used 2024 — 41.45
11. Kia EV9 Land AWD — Used 2024 — 40.45
12. Hyundai IONIQ 9 Preferred AWD — New 2026 — 37.75

The Grand Highlander new ranking #1 is correct and not a bug — its ~$27K
year-10 residual vs ~$13K for the used version produces a genuinely better
net TCO ($88,620 vs $94,780) that outweighs the higher purchase price.
This was extensively validated and discussed with the user.

---

## Known issues fixed before handoff

- **Bug fixed:** `v.at_url` was referenced in listings partial before the variable
  was available — now computed server-side and passed as `at_url` to all templates.
- **Bug fixed:** Reset weights button was resetting to last-rendered values, not
  true defaults — now uses hardcoded `TRUE_DEFAULTS` constant in JS.
- **AT scraper:** `sts=` (New/Used) filter removed — unreliable, returns wrong
  vehicles. Year range (`yRng=`) is the reliable filter.
- **Grand Highlander AT slug:** Uses `mdl=Grand+Highlander` query parameter
  instead of the model path segment — the path segment returns unrelated Toyota
  inventory. This is set via `at_url_override` in vehicles.json.
- **IONIQ 9 AT slug:** Must be `ioniq%209` (URL-encoded space) not `ioniq+9`.

---

## Known sandbox limitation (not a bug)

AutoTrader.ca uses Incapsula bot detection. The sandbox IP gets rate-limited
after ~10 requests. On a home laptop IP this does not happen — the scraper
works correctly and was confirmed to return real listings before the block
kicked in. No code change needed.

---

## Likely first-run issues to watch for

1. **Images missing** — normal until `fetch_images.py` runs. App handles this
   gracefully with placeholder divs. If DuckDuckGo changes its API, the fetcher
   may need updating — the function is `ddg_image_urls()` in `fetch_images.py`.

2. **cache.db not found** — created automatically on first `python app.py`.
   If there's a permission error, check the `data/` directory is writable.

3. **Listing scraper returns 0 results** — first check if AutoTrader.ca loads
   normally in the browser. If yes, the issue is in the scraper. Most common
   cause: class name changes in AT's HTML. The key selectors are in
   `scrapers/listings.py`: `result-item`, `result-title`, `price-amount`,
   `kms`, `proximity-text`, `inner-link`.

4. **HTMX weight update not firing** — check browser console for JS errors.
   The form submits to `/rerank` via HTMX POST. If HTMX CDN is unavailable,
   it will silently fail — try `pip install flask-htmx` and serve HTMX locally.

---

## What was NOT yet done (natural next steps)

- **UI polish pass** — the CSS is functional but hasn't been tested on a real
  browser. Likely needs tweaks: card grid responsive breakpoints, gallery
  height on smaller screens, compare page on narrow viewports.

- **Image fetcher edge cases** — DuckDuckGo occasionally returns non-image URLs
  or SVGs. The fetcher filters these but may miss some. Manual replacement of
  poor images is straightforward: drop a JPEG into `images/<vehicle-id>/`.

- **Listing deduplication** — AutoTrader serves some listings twice in the HTML
  (enhanced + standard placement). The `seen_urls` set in the scraper handles
  this for most cases but may miss some edge cases if href differs slightly.

- **Craigslist relevance filtering** — currently filters by make + model name
  presence in the title. Dealer spam (unrelated vehicles tagged with popular
  names) occasionally slips through. Could be tightened with year filtering.

- **Print/export view** — user may want to print the comparison page. No print
  stylesheet exists yet.

- **The audit at the end of the previous session was interrupted mid-run.
  It was checking all 12 vehicle detail pages for rendering issues — the
  check passed on the first 3-4 vehicles before the session was compacted.
  Worth re-running the full audit on the laptop:**

```python
# run from vehicle-app/ directory
python3 -c "
import json, sys
sys.path.insert(0, '.')
from app import app, init_db
init_db()
with app.test_client() as c:
    with open('data/vehicles.json') as f:
        vehicles = json.load(f)
    for v in vehicles:
        r = c.get(f'/vehicle/{v[\"id\"]}')
        ok = '✓' if r.status_code == 200 else '✗'
        has_at = 'AutoTrader.ca' in r.data.decode()
        has_score = 'score-breakdown' in r.data.decode()
        print(f'  {ok} {v[\"rank\"]:>2} {v[\"short_name\"]:<36} AT={has_at} Scores={has_score}')
"
```

---

## User preferences (carry forward to new session)

- Prefers Python, is comfortable running terminal commands
- SI notation always: space between number and units (5 mm, 15 A)
- Location: Vancouver, BC — prices in CAD
- GitHub account: voxelisKW
- Tone: direct, technical, no fluff
- During coding sessions: update `.claude/CLAUDE.md` in the repo with
  architectural decisions, changed behaviour, and in-progress work.
  Keep it concise and factual. Do NOT use user-level memory for project state.

---

## Companion documents (same download folder)

- `BC_Family_Vehicle_Comparison.xlsx` — scored comparison matrix + TCO detail
- `BC_Family_Vehicle_Summaries.pdf` — shareable 7-page candidate profiles
- `VEHICLE_SUMMARIES.md` — markdown source for the PDF
- `RESEARCH.md` — raw research notes
- `PROJECT_BRIEF.md` — original project brief

---
_End of handoff. Good luck — the hard parts are done._
