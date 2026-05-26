"""
BC Family Vehicle Browser
Run: python app.py
Open: http://localhost:5000
"""

import json, os, sys, sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache

from flask import Flask, render_template, jsonify, request, send_from_directory

# Add scrapers to path
sys.path.insert(0, str(Path(__file__).parent))
from scrapers.listings import fetch_listings, autotrader_url, deep_links, SCOPES

BASE = Path(__file__).parent
DATA_FILE  = BASE / "data" / "vehicles.json"
IMAGES_DIR = BASE / "images"
DB_FILE    = BASE / "data" / "cache.db"

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# ── Scoring weights (default, matches spreadsheet) ───────────────────────────
DEFAULT_WEIGHTS = {
    "tco":          3.0,
    "car_seat_fit": 2.0,
    "cargo":        1.0,
    "third_row":    1.0,
    "corridor":     1.5,
    "hitch":        0.5,
    "reliability":  2.0,
    "winter":       1.3,
    "fsr":          0.5,
}

CRITERIA_LABELS = {
    "tco":          "10yr Net TCO",
    "car_seat_fit": "Car Seat Fit",
    "cargo":        "Cargo Utility",
    "third_row":    "3rd Row Comfort",
    "corridor":     "Corridor Performance",
    "hitch":        "Hitch / Bike Rack",
    "reliability":  "Reliability",
    "winter":       "Winter Capability",
    "fsr":          "FSR Capability",
}

# ── Database setup ────────────────────────────────────────────────────────────
def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS listing_cache (
            vehicle_id TEXT,
            scope TEXT,
            data TEXT,
            fetched_at TEXT,
            PRIMARY KEY (vehicle_id, scope)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            vehicle_id TEXT PRIMARY KEY,
            note TEXT,
            updated_at TEXT
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS favourites (
            vehicle_id TEXT PRIMARY KEY,
            added_at TEXT
        )
    """)
    con.commit()
    con.close()

def get_cached_listings(vehicle_id, scope, max_age_hours=12):
    con = sqlite3.connect(DB_FILE)
    row = con.execute(
        "SELECT data, fetched_at FROM listing_cache WHERE vehicle_id=? AND scope=?",
        (vehicle_id, scope)
    ).fetchone()
    con.close()
    if not row:
        return None
    fetched_at = datetime.fromisoformat(row[1])
    if datetime.now() - fetched_at > timedelta(hours=max_age_hours):
        return None
    return json.loads(row[0])

def save_cached_listings(vehicle_id, scope, data):
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "INSERT OR REPLACE INTO listing_cache VALUES (?,?,?,?)",
        (vehicle_id, scope, json.dumps(data), datetime.now().isoformat())
    )
    con.commit()
    con.close()

def get_note(vehicle_id):
    con = sqlite3.connect(DB_FILE)
    row = con.execute("SELECT note FROM notes WHERE vehicle_id=?", (vehicle_id,)).fetchone()
    con.close()
    return row[0] if row else ""

def save_note(vehicle_id, note):
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "INSERT OR REPLACE INTO notes VALUES (?,?,?)",
        (vehicle_id, note, datetime.now().isoformat())
    )
    con.commit()
    con.close()

def get_favourites():
    con = sqlite3.connect(DB_FILE)
    rows = con.execute("SELECT vehicle_id FROM favourites").fetchall()
    con.close()
    return {r[0] for r in rows}

def toggle_favourite(vehicle_id):
    con = sqlite3.connect(DB_FILE)
    exists = con.execute("SELECT 1 FROM favourites WHERE vehicle_id=?", (vehicle_id,)).fetchone()
    if exists:
        con.execute("DELETE FROM favourites WHERE vehicle_id=?", (vehicle_id,))
        is_fav = False
    else:
        con.execute("INSERT INTO favourites VALUES (?,?)", (vehicle_id, datetime.now().isoformat()))
        is_fav = True
    con.commit()
    con.close()
    return is_fav

# ── Vehicle data ──────────────────────────────────────────────────────────────
@lru_cache(maxsize=1)
def load_vehicles():
    with open(DATA_FILE) as f:
        return json.load(f)

def vehicle_by_id(vid):
    return next((v for v in load_vehicles() if v["id"] == vid), None)

def compute_score(vehicle, weights):
    """Compute weighted total score given a weights dict."""
    total = 0.0
    scores = vehicle["scores"]
    for key, wt in weights.items():
        total += scores.get(key, 0) * wt
    return round(total, 2)

def ranked_vehicles(weights):
    """Return vehicles sorted by computed score descending."""
    vehicles = load_vehicles()
    scored = []
    for v in vehicles:
        score = compute_score(v, weights)
        scored.append({**v, "computed_score": score})
    scored.sort(key=lambda x: x["computed_score"], reverse=True)
    for i, v in enumerate(scored):
        v["computed_rank"] = i + 1
    return scored

def get_vehicle_images(vehicle_id):
    """Return list of image paths for a vehicle, sorted."""
    vdir = IMAGES_DIR / vehicle_id
    if not vdir.exists():
        return []
    imgs = sorted(vdir.glob("*.jpg"))
    return [f"/images/{vehicle_id}/{p.name}" for p in imgs]

def powertrain_badge(pt_type):
    return {
        "bev":    ("BEV", "#1a7c4f"),
        "phev":   ("PHEV", "#2E75B6"),
        "hybrid": ("Hybrid", "#375623"),
        "ice":    ("ICE", "#595959"),
    }.get(pt_type, ("?", "#333"))

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    weights = parse_weights(request.args)
    favs = get_favourites()
    vehicles = ranked_vehicles(weights)
    for v in vehicles:
        v["is_favourite"] = v["id"] in favs
        v["images"] = get_vehicle_images(v["id"])
        v["badge_label"], v["badge_color"] = powertrain_badge(v["powertrain_type"])
    return render_template("index.html",
        vehicles=vehicles,
        weights=weights,
        weights_qs=weights_query_string(weights),
        criteria_labels=CRITERIA_LABELS,
        scopes=SCOPES,
    )


def parse_weights(source):
    """Parse w_<key> values from a MultiDict (request.form or request.args),
    falling back to DEFAULT_WEIGHTS for any missing or unparseable entry."""
    weights = {}
    for key, default in DEFAULT_WEIGHTS.items():
        try:
            weights[key] = float(source.get(f"w_{key}", default))
        except (TypeError, ValueError):
            weights[key] = default
    return weights


def weights_query_string(weights):
    """Encode weights as a URL query string fragment (without leading '?' or '&').
    Returns an empty string when weights match defaults so links stay clean."""
    if all(weights[k] == DEFAULT_WEIGHTS[k] for k in DEFAULT_WEIGHTS):
        return ""
    return "&".join(f"w_{k}={weights[k]}" for k in DEFAULT_WEIGHTS)


@app.route("/rerank", methods=["POST"])
def rerank():
    """AJAX endpoint: return re-ranked card HTML with new weights."""
    weights = parse_weights(request.form)
    favs = get_favourites()
    vehicles = ranked_vehicles(weights)
    for v in vehicles:
        v["is_favourite"] = v["id"] in favs
        v["images"] = get_vehicle_images(v["id"])
        v["badge_label"], v["badge_color"] = powertrain_badge(v["powertrain_type"])

    return render_template("partials/vehicle_cards.html",
        vehicles=vehicles,
        weights=weights,
        weights_qs=weights_query_string(weights),
    )


@app.route("/vehicle/<vehicle_id>")
def vehicle_detail(vehicle_id):
    v = vehicle_by_id(vehicle_id)
    if not v:
        return "Vehicle not found", 404

    scope = request.args.get("scope", "bc")
    weights = parse_weights(request.args)

    # Compute rank under current weights so detail header matches index ordering
    all_ranked = ranked_vehicles(weights)
    v_ranked = next(x for x in all_ranked if x["id"] == vehicle_id)
    score = v_ranked["computed_score"]
    rank = v_ranked["computed_rank"]

    cached = get_cached_listings(vehicle_id, scope)
    listings_data = cached  # may be None → will show "load" button

    favs = get_favourites()
    note = get_note(vehicle_id)
    images = get_vehicle_images(vehicle_id)

    badge_label, badge_color = powertrain_badge(v["powertrain_type"])

    at_url = autotrader_url(v, scope)
    cl_url = v.get("cr_url", "")
    dl     = deep_links(v, scope)

    return render_template("vehicle.html",
        v=v,
        score=score,
        rank=rank,
        weights=weights,
        weights_qs=weights_query_string(weights),
        criteria_labels=CRITERIA_LABELS,
        images=images,
        listings_data=listings_data,
        scope=scope,
        scopes=SCOPES,
        is_favourite=vehicle_id in favs,
        note=note,
        badge_label=badge_label,
        badge_color=badge_color,
        all_vehicles=all_ranked,
        at_url=at_url,
        cl_url=cl_url,
        deep_links_default=dl,
    )


@app.route("/listings/<vehicle_id>")
def get_listings(vehicle_id):
    """AJAX: fetch/refresh listings for a vehicle."""
    v = vehicle_by_id(vehicle_id)
    if not v:
        return jsonify({"error": "not found"}), 404

    scope = request.args.get("scope", "bc")
    force = request.args.get("force", "0") == "1"

    at_url = autotrader_url(v, scope)
    cl_url = v.get("cr_url", "")
    dl     = deep_links(v, scope)
    ctx    = dict(v=v, scope=scope, scopes=SCOPES,
                  at_url=at_url, cl_url=cl_url, deep_links_default=dl)

    if not force:
        cached = get_cached_listings(vehicle_id, scope)
        if cached:
            return render_template("partials/listings.html",
                listings_data=cached, **ctx)

    data = fetch_listings(v, scope)
    save_cached_listings(vehicle_id, scope, data)
    return render_template("partials/listings.html",
        listings_data=data, **ctx)


@app.route("/compare")
def compare():
    ids = request.args.getlist("ids")
    if not ids:
        ids = [v["id"] for v in load_vehicles()[:3]]

    weights = parse_weights(request.args)
    ranked = ranked_vehicles(weights)
    by_id = {v["id"]: v for v in ranked}

    selected = []
    for vid in ids[:4]:  # max 4
        v = by_id.get(vid)
        if v:
            v = dict(v)
            v["images"] = get_vehicle_images(vid)
            v["badge_label"], v["badge_color"] = powertrain_badge(v["powertrain_type"])
            selected.append(v)

    return render_template("compare.html",
        selected=selected,
        all_vehicles=ranked,
        criteria_labels=CRITERIA_LABELS,
        weights=weights,
        weights_qs=weights_query_string(weights),
    )


@app.route("/favourite/<vehicle_id>", methods=["POST"])
def favourite(vehicle_id):
    is_fav = toggle_favourite(vehicle_id)
    return jsonify({"is_favourite": is_fav})


@app.route("/note/<vehicle_id>", methods=["POST"])
def note(vehicle_id):
    text = request.form.get("note", "")
    save_note(vehicle_id, text)
    return jsonify({"saved": True})


@app.route("/images/<vehicle_id>/<filename>")
def serve_image(vehicle_id, filename):
    return send_from_directory(IMAGES_DIR / vehicle_id, filename)


@app.route("/api/vehicles")
def api_vehicles():
    weights = DEFAULT_WEIGHTS.copy()
    vehicles = ranked_vehicles(weights)
    return jsonify([{
        "id": v["id"], "name": v["name"], "rank": v["computed_rank"],
        "score": v["computed_score"], "tco": v["tco_value"],
    } for v in vehicles])


@app.route("/health")
def health():
    """Debug page — quick status of images, cache, and DB."""
    vehicles = load_vehicles()

    # Image status
    image_status = []
    for v in vehicles:
        vdir = IMAGES_DIR / v["id"]
        count = len(list(vdir.glob("*.jpg"))) if vdir.exists() else 0
        image_status.append({
            "id": v["id"], "name": v["short_name"],
            "count": count, "ok": count >= 4,
        })

    # Listing cache status
    con = sqlite3.connect(DB_FILE)
    cache_rows = con.execute(
        "SELECT vehicle_id, scope, fetched_at FROM listing_cache ORDER BY fetched_at DESC"
    ).fetchall()
    fav_rows  = con.execute("SELECT vehicle_id FROM favourites").fetchall()
    note_rows = con.execute("SELECT vehicle_id FROM notes WHERE note != ''").fetchall()
    con.close()

    cache_status = [
        {"vehicle_id": r[0], "scope": r[1], "fetched_at": r[2][:19]}
        for r in cache_rows
    ]

    total_imgs = sum(s["count"] for s in image_status)
    img_ok     = sum(1 for s in image_status if s["ok"])

    html = f"""<!DOCTYPE html><html><head>
<title>Vehicle Browser — Health</title>
<style>
body{{font-family:monospace;max-width:900px;margin:2rem auto;padding:0 1rem;background:#f0f4f8}}
h1{{color:#1F3864}}h2{{color:#2E75B6;margin-top:1.5rem}}
table{{border-collapse:collapse;width:100%;margin:.5rem 0}}
td,th{{border:1px solid #ccc;padding:.35rem .6rem;text-align:left;font-size:.85rem}}
th{{background:#1F3864;color:white}}
.ok{{color:#2d9e5f;font-weight:700}}.warn{{color:#e05c5c;font-weight:700}}
.back{{display:inline-block;margin-bottom:1rem;color:#2E75B6}}
</style></head><body>
<a class="back" href="/">← Back to app</a>
<h1>🩺 Health Check</h1>

<h2>Images ({total_imgs} total, {img_ok}/12 vehicles with ≥4 images)</h2>
{"<p class='warn'>⚠ Run: python scrapers/fetch_images.py</p>" if img_ok < 12 else "<p class='ok'>✓ All vehicles have images</p>"}
<table><tr><th>Vehicle</th><th>Images</th><th>Status</th></tr>"""

    for s in image_status:
        status = f"<span class='ok'>✓ {s['count']}</span>" if s["ok"] \
                 else f"<span class='warn'>✗ {s['count']}</span>"
        html += f"<tr><td>{s['name']}</td><td>{s['count']}</td><td>{status}</td></tr>"

    html += f"""</table>

<h2>Listing Cache ({len(cache_rows)} cached searches)</h2>"""

    if cache_status:
        html += "<table><tr><th>Vehicle ID</th><th>Scope</th><th>Fetched At</th></tr>"
        for r in cache_status:
            html += f"<tr><td>{r['vehicle_id']}</td><td>{r['scope']}</td><td>{r['fetched_at']}</td></tr>"
        html += "</table>"
    else:
        html += "<p>No cached listings yet — visit a vehicle detail page to fetch.</p>"

    html += f"""
<h2>User Data</h2>
<p>Favourites: <strong>{len(fav_rows)}</strong> &nbsp;|&nbsp;
   Notes saved: <strong>{len(note_rows)}</strong></p>

<h2>Paths</h2>
<table>
<tr><td>App root</td><td>{BASE}</td></tr>
<tr><td>Images dir</td><td>{IMAGES_DIR}</td></tr>
<tr><td>Database</td><td>{DB_FILE}</td></tr>
<tr><td>Vehicles JSON</td><td>{DATA_FILE}</td></tr>
</table>
</body></html>"""
    return html


if __name__ == "__main__":
    init_db()

    # Honour PORT env var so launchers can avoid macOS's AirPlay clash on 5000.
    port = int(os.environ.get("PORT", "5000"))

    vehicles = load_vehicles()
    total_imgs = sum(
        len(list((IMAGES_DIR / v["id"]).glob("*.jpg")))
        for v in vehicles
        if (IMAGES_DIR / v["id"]).exists()
    )
    img_pct = int(total_imgs / (len(vehicles) * 6) * 100)

    url = f"http://localhost:{port}"
    print("┌─────────────────────────────────────────────────┐")
    print("│  BC Family Vehicle Browser                       │")
    print("├─────────────────────────────────────────────────┤")
    print(f"│  URL:     {url:<35}  │")
    print(f"│  Health:  {url + '/health':<35}  │")
    print(f"│  Images:  {total_imgs:>3} downloaded  ({img_pct}% complete)          │")
    if total_imgs < 12:
        print(f"│  Run: python scrapers/fetch_images.py            │")
    print(f"│  Ctrl+C to stop                                  │")
    print("└─────────────────────────────────────────────────┘")
    print()
    app.run(debug=True, host="0.0.0.0", port=port)
