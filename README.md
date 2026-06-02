# dasAuto — Family Vehicle Picker

A reusable Flask + HTMX app that scores a curated shortlist of family
vehicles against weighted criteria, with live links to AutoTrader and
Craigslist listings. Built originally for the kaan-and-tess household
in Vancouver BC; structured so you can lift it for a different family
with minimal further input.

## Layout

```
dasAuto/
├── vehicle-app/           # the SKILL — reusable across families
│   ├── app.py             # Flask routes; reads $VEHICLE_DATA_DIR
│   ├── scoring.py         # criteria + weighted-sum framework
│   ├── tco.py             # NPV-based TCO computation
│   ├── scrapers/          # AutoTrader + Craigslist + image fetcher
│   ├── templates/, static/
│   ├── briefs/            # research-brief templates to seed a new family
│   ├── docs/HANDOFF.md
│   ├── tests/test_smoke.py
│   ├── requirements.txt
│   └── run.sh, "Launch Vehicle Browser.bat"
└── user-kaan-and-tess/    # this family's SITUATION + WORK PRODUCT
    ├── situation.md       # who, where, needs, weights rationale
    ├── weights.json       # default importance weights
    ├── vehicles.json      # 12 candidates with per-criterion scores
    ├── image_seeds.json   # curated Wikimedia URLs (input to fetch_images)
    ├── tco_research.md    # Vancouver BC rate research
    └── images/            # downloaded galleries (gitignored)
```

The skill folder is portable: nothing inside it names a specific family.
Every per-family input/output lives in `user-kaan-and-tess/`.

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

1. Copy `user-kaan-and-tess/` to `user-<their-label>/`:
   ```bash
   cp -r user-kaan-and-tess user-jones-family
   ```
2. Edit `user-jones-family/situation.md` to describe who they are and
   what they want from a vehicle.
3. Update `weights.json`, `vehicles.json`, `image_seeds.json`, and
   `tco_research.md` to reflect that family's situation. The briefs in
   `vehicle-app/briefs/` are the templates a research agent fills in.
4. Run with the new data dir:
   ```bash
   VEHICLE_DATA_DIR=$(pwd)/user-jones-family bash vehicle-app/run.sh
   ```

## Routes

- `/` — ranked card grid; edit weights in the sidebar to re-rank live
- `/vehicle/<id>` — full profile, gallery, scores, listings
- `/compare?ids=<a>&ids=<b>...` — side-by-side, up to 4 vehicles
- `/health` — image count, listing cache, paths
- `/api/vehicles?w_<key>=<val>...` — ranked JSON list under chosen weights

Customised weights flow through every link via `?w_<key>=<value>` query
params, so a rerank on the index persists into detail and compare pages.

## Tests

```bash
cd vehicle-app && .venv/bin/python -m unittest tests.test_smoke
```

11 smoke tests cover every route, weight threading, custom-weight
rerank behaviour, garbage-input tolerance, and the JSON API.

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
   - *(optional)* `VEHICLE_DATA_DIR` — only set if you fork the repo
     and use a non-default family dir; otherwise the default
     (`user-kaan-and-tess/`) is correct.
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
