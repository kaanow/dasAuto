# dasAuto — Family Vehicle Picker

A reusable Flask + HTMX app that scores a curated shortlist of family
vehicles against weighted criteria, with live links to AutoTrader and
Craigslist listings. Built originally for the kaan-and-tess household
in Vancouver BC; structured to run as one repo serving multiple
families, each at their own domain (`VEHICLE_DATA_DIR` selects the
family). Currently assumes every family is in BC — see the note under
"Use for a different family".

## Layout

```
dasAuto/
├── CLAUDE.md              # architectural rules (authoritative on structure)
├── docs/                  # ARCHITECTURAL docs — apply to every family
│   ├── new_family_playbook.md   # the buildout sequence for a new family
│   ├── scoring_framework.md     # the 9 criteria + rubric + formula
│   ├── tco_methodology.md       # NPV, warranty cliff, residual math
│   ├── brand_repair_tail.md     # OOW maintenance multipliers
│   ├── tax_math_canada.md       # BC PST tiers, GST, dealer fees
│   ├── selection_principle.md   # hard-filter vs scored-criterion rule
│   └── multi_family_todo.md     # generalisation status (done + deferred)
├── vehicle-app/           # the SKILL — reusable across families
│   ├── app.py             # Flask routes; reads $VEHICLE_DATA_DIR
│   ├── scoring.py         # criteria + weighted-sum framework
│   ├── tco.py             # NPV-based TCO computation
│   ├── repair_ratios.json # brand×powertrain OOW-maintenance multipliers
│   ├── scrapers/          # AutoTrader + Craigslist + image fetcher
│   ├── templates/, static/, tests/test_smoke.py
│   ├── briefs/            # research-brief templates to seed a new family
│   └── run.sh, "Launch Vehicle Browser.bat"
└── user-<family>/         # one folder per family (e.g. user-kaan-and-tess)
    ├── family.md          # PURE FAMILY INPUT — the canonical brief
    ├── site.json          # display identity (name, region, insurance ref)
    ├── weights.json       # default importance weights
    ├── vehicles.json      # the cohort, with per-criterion scores
    ├── image_seeds.json   # curated image URLs (input to fetch_images)
    ├── manual_listings.json     # AI-curated market listings
    ├── dealer_quotes/<id>.json  # one JSON per active dealer quote
    ├── images/            # downloaded galleries
    └── research/          # AI-generated deliverables
        ├── tco_research.md, cohort_rationale.md, decisions_log.md
```

The skill folder is portable: nothing inside it names a specific family.
Every per-family input/output lives in `user-<family>/`. The split
between architectural and family-specific knowledge is enforced — see
`CLAUDE.md`.

## Launch

**macOS / Linux:**

```bash
bash vehicle-app/run.sh
```

**Windows:** double-click `vehicle-app\Launch Vehicle Browser.bat`.

First run creates a `.venv`, installs deps, downloads ~68 vehicle images
from Wikimedia, and starts the server. Subsequent runs reuse all of
that. Defaults to <http://localhost:5000>; falls back to 5057/5500/8080
on macOS when AirPlay holds 5000. Pin with `PORT=5500 bash …`.

## Use for a different family

The full sequence (intake → criteria → cohort → TCO → images → deploy)
is in **`docs/new_family_playbook.md`** — follow it end-to-end. The
short version:

1. Create `user-<their-label>/`.
2. Have the family fill in `family.md` from
   `vehicle-app/briefs/family_brief_template.md`. This is canonical
   input — don't edit it later; clarifications go to
   `research/decisions_log.md`.
3. Add `site.json` (display name, region label, insurance ref) and
   build out `weights.json`, `vehicles.json`, `image_seeds.json`, and
   `research/tco_research.md`. A vehicle that omits `maint_oow_per_year`
   inherits the brand×powertrain default from `repair_ratios.json`; set
   it explicitly only for a per-vehicle age/km premium.
4. Run with the new data dir:
   ```bash
   VEHICLE_DATA_DIR=$(pwd)/user-<their-label> bash vehicle-app/run.sh
   ```
5. To deploy, provision a separate Railway service pointed at the new
   folder and CNAME a subdomain (see "Deploying to Railway").

**BC-only for now.** The tax engine, listing-scope filter, and
insurance references assume British Columbia. If `site.json` sets
`region_code` to anything other than `BC`, the app logs a startup
warning — that's the signal to generalise the items tracked in
`docs/multi_family_todo.md` before trusting all-in pricing.

## Routes

- `/` — ranked card grid; edit weights in the sidebar to re-rank live
- `/vehicle/<id>` — full profile, gallery, scores, listings
- `/compare?ids=<a>&ids=<b>...` — side-by-side, up to 4 vehicles
- `/siennas` — Sienna AWD-Hybrid cross-shop table (kaan-and-tess; will
  generalise to `/cross-shop/<vehicle-id>` once a second family
  converges — see `docs/multi_family_todo.md`)
- `/active/<id>` — archive/restore a vehicle from the web UI
- `/health` — image count, listing cache, paths
- `/api/vehicles?w_<key>=<val>...` — ranked JSON list under chosen weights

Customised weights flow through every link via `?w_<key>=<value>` query
params, so a rerank on the index persists into detail and compare pages.

## Tests

```bash
cd vehicle-app && .venv/bin/python -m unittest tests.test_smoke
```

17 smoke tests cover every route, weight threading, custom-weight
rerank behaviour, the variable-horizon TCO model (warranty cliff,
per-year maintenance, renormalisation), garbage-input tolerance, and
the JSON API.

## Refreshing images

Delete `user-kaan-and-tess/images/` and re-run the launcher — it'll
re-fetch from `image_seeds.json`. To swap individual images, edit the
URLs in the seed file first.

## Deploying to Railway

The repo is set up to auto-deploy to Railway on push to `main`. The
moving parts that matter:

- **`Procfile`** at the repo root tells Railway to `cd vehicle-app &&
  gunicorn app:app …`.
- **`requirements.txt`** at the repo root re-exports
  `vehicle-app/requirements.txt` so Nixpacks auto-detects Python.
- **Images** ship in the git tree (no longer gitignored) so the
  container doesn't depend on Wikimedia at boot.
- **`cache.db`** (favourites + per-vehicle notes + listings cache)
  must live on a persistent volume — see env-var setup below.

### One-time setup in the Railway dashboard

1. **Create project → Deploy from GitHub repo** → pick `kaanow/dasAuto`,
   branch `main`. Railway will run the first build automatically.
2. **Settings → Networking → Generate Domain.** You'll get a
   `<project>.up.railway.app` URL.
3. **Add a Volume**: Settings → Volumes → **+ New Volume**, mount path
   `/data`, size 1 GB. (~$0.25/month at Railway's rate.)
4. **Set environment variables** (Settings → Variables):
   - `VEHICLE_DB_PATH=/data/cache.db` — points the app at the volume so
     favourites/notes survive every deploy.
   - `PYTHONUNBUFFERED=1` — makes gunicorn access logs flush
     immediately so Railway's log viewer is live.
   - `VEHICLE_DATA_DIR` — the family folder this service serves (e.g.
     `user-kaan-and-tess` or `user-theo`). Leave unset only for the
     default kaan-and-tess service. Each family runs as its **own
     Railway service** off the same repo/branch, differentiated by this
     var, with its own volume and CNAME'd subdomain
     (`dasauto.alti2.de` → kaan-and-tess, `brudersauto.alti2.de` →
     theo).
5. **Trigger redeploy** (Deployments → Redeploy) so the new env vars
   take effect. Subsequent pushes to `main` auto-deploy.

### Edit-and-ship loop

The intended workflow:

1. Edit `vehicles.json`, `weights.json`, `image_seeds.json`, or any
   prose locally (Claude or your editor).
2. If you added a vehicle, run `python vehicle-app/scrapers/fetch_images.py`
   to pull its images into `user-kaan-and-tess/images/`.
3. `git push origin main` → Railway rebuilds and serves the new
   version in ~60 s.

Notes and favourites added through the deployed UI live on the volume
and are NOT version-controlled — they survive deploys but not volume
deletion. Vehicle data is canonical in git.

### Soft-deactivating entries

`vehicles.json` entries can carry `"active": false` to drop them from
the index, /compare, /api, and TCO normalization without deleting them
from the file. Direct `/vehicle/<id>` URLs still resolve (the detail
page renders with "Archived — not in active cohort" in place of the
rank). Flip the flag back to `true` to re-enable.
