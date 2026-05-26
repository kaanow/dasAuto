# BC Family Vehicle Browser

Local Flask web app for browsing, scoring, and finding listings for 12
candidate family vehicles in Vancouver BC. See `CLAUDE.md` for architecture
and `HANDOFF.md` for the original build notes.

## Launch

One-time setup (creates the venv, installs deps, downloads the 68 vehicle
images from Wikimedia):

```bash
cd vehicle-app
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scrapers/fetch_images.py
```

Start the app:

```bash
.venv/bin/python app.py
```

Open <http://localhost:5000>.

### If port 5000 is taken

macOS uses port 5000 for AirPlay Receiver by default. Either disable it
(System Settings → General → AirDrop & Handoff → AirPlay Receiver: Off),
or change the port at the bottom of `vehicle-app/app.py`:

```python
app.run(debug=True, host="0.0.0.0", port=5057)
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

```bash
.venv/bin/python scrapers/fetch_images.py --refresh
```

Adds any missing or replaces existing per-vehicle galleries from
`data/image_seeds.json`. The seed file is curated; if you want to swap
images, edit the URLs there and re-run with `--refresh`.
