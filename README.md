# BC Family Vehicle Browser

Local Flask web app for browsing, scoring, and finding listings for 12
candidate family vehicles in Vancouver BC. See `CLAUDE.md` for architecture
and `HANDOFF.md` for the original build notes.

## Launch

**macOS / Linux:**

```bash
bash vehicle-app/run.sh
```

**Windows:** double-click `vehicle-app\Launch Vehicle Browser.bat`.

On first run the launcher creates a project-local virtual environment,
installs the Python dependencies, downloads the 68 vehicle images from
Wikimedia, and starts the server. Subsequent runs reuse all of that and
start in under a second.

By default the app serves on <http://localhost:5000>. On macOS that port
is often held by AirPlay Receiver; `run.sh` detects this and falls back
to 5057, then 5500, then 8080. To pin a specific port set `PORT`:

```bash
PORT=5500 bash vehicle-app/run.sh
```

## Routes

- `/` — ranked card grid; edit weights in the sidebar to re-rank live
- `/vehicle/<id>` — full profile, gallery, scores, listings
- `/compare?ids=<a>&ids=<b>...` — side-by-side, up to 4 vehicles
- `/health` — image count, listing cache, paths (debug)
- `/api/vehicles` — ranked JSON list

Customised weights flow through every link via `?w_<key>=<value>` query
params, so a rerank on the index page persists into the detail and
compare pages.

## Refreshing images

Delete `vehicle-app/images/` and re-run the launcher — it'll re-fetch
from `data/image_seeds.json`. To swap individual images, edit the URLs
in that seed file first.
