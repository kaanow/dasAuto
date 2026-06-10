"""
Family Vehicle Browser — Flask app.

The skill: the routes, scoring framework (in scoring.py), TCO maths
(in tco.py), and listings scrapers.

The data: comes from a per-family directory pointed at by VEHICLE_DATA_DIR
(default: ../user-kaan-and-tess/ relative to this file). Expected contents:
  vehicles.json       — candidate list with per-criterion scores + TCO
  weights.json        — default importance weights (optional; falls back
                        to scoring.DEFAULT_WEIGHTS)
  images/<id>/*.jpg   — galleries downloaded by scrapers/fetch_images.py
  cache.db            — runtime SQLite (listings cache, favourites, notes;
                        created on first run)
"""

import json, os, sys, sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from functools import lru_cache

from flask import Flask, render_template, jsonify, request, send_from_directory

sys.path.insert(0, str(Path(__file__).parent))
from scrapers.listings import fetch_listings, autotrader_url, deep_links, SCOPES
from scoring import CRITERIA_LABELS, compute_score, rank_vehicles, reframe_for_horizon

# Allowed horizon range for the user-facing slider.
HORIZON_MIN = 4
HORIZON_MAX = 15
HORIZON_DEFAULT = 10

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent

def _resolve_data_dir():
    """VEHICLE_DATA_DIR env var wins. An absolute value is used as-is; a
    relative value (e.g. "user-theo") resolves against the REPO ROOT, not the
    process CWD — gunicorn runs from vehicle-app/ in production, so resolving
    against CWD would point at vehicle-app/user-theo and 500. Unset → the
    canonical user-kaan-and-tess folder beside vehicle-app/."""
    env = os.environ.get("VEHICLE_DATA_DIR")
    if env:
        p = Path(env)
        return p.resolve() if p.is_absolute() else (BASE.parent / p).resolve()
    return (BASE.parent / "user-kaan-and-tess").resolve()

DATA_DIR    = _resolve_data_dir()
VEHICLES_FILE = DATA_DIR / "vehicles.json"
WEIGHTS_FILE  = DATA_DIR / "weights.json"
IMAGES_DIR    = DATA_DIR / "images"
MANUAL_LISTINGS_FILE = DATA_DIR / "manual_listings.json"
SITE_FILE     = DATA_DIR / "site.json"

# DB lives next to the family data by default. In production (Railway)
# the data dir ships in the immutable git checkout, but cache.db needs
# a persistent volume so favourites/notes survive deploys — set
# VEHICLE_DB_PATH (e.g. /data/cache.db) to point at the volume mount.
DB_FILE = Path(os.environ.get("VEHICLE_DB_PATH") or (DATA_DIR / "cache.db")).resolve()

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0


# ── Weights ──────────────────────────────────────────────────────────────────
FALLBACK_WEIGHTS = {
    "tco":          3.0, "car_seat_fit": 2.0, "cargo":       1.0,
    "third_row":    1.0, "corridor":     1.5, "hitch":       0.5,
    "reliability":  2.0, "winter":       1.3, "fsr":         0.5,
}

@lru_cache(maxsize=1)
def default_weights():
    """User's per-family defaults from weights.json, else built-in fallback."""
    if WEIGHTS_FILE.exists():
        with open(WEIGHTS_FILE) as f:
            return json.load(f)
    return dict(FALLBACK_WEIGHTS)


# ── Site identity ──────────────────────────────────────────────────────────────
# Per-family display config (name, region label, insurance reference). Keeps
# family/region strings out of the templates so one codebase serves any
# family. BC-centric defaults — the region_code drives the non-BC guard below.
FALLBACK_SITE = {
    "site_name":     "Family Vehicle Browser",
    "short_name":    "Family Vehicle",
    "region_label":  "BC",
    "region_code":   "BC",
    "insurance_ref": "",
    "data_sources":  "AutoTrader.ca, CarGurus.ca",
}

@lru_cache(maxsize=1)
def site_config():
    """Per-family site identity from site.json, merged over the defaults."""
    cfg = dict(FALLBACK_SITE)
    if SITE_FILE.exists():
        with open(SITE_FILE) as f:
            cfg.update(json.load(f))
    return cfg

# Region guard: the tax engine (BC PST tiers), the listing-scope filter, and
# the insurance reference all assume British Columbia. If a family is set up
# outside BC, surface it loudly rather than silently mispricing.
_site = site_config()
if str(_site.get("region_code", "")).upper() != "BC":
    sys.stderr.write(
        f"WARNING: site region_code={_site.get('region_code')!r} is not 'BC'. "
        "Tax math (BC PST tiers), the AutoTrader scope filter, and insurance "
        "references are BC-specific and will be WRONG for this family. "
        "Generalise docs/tax_math_canada.md + the scope filter before trusting "
        "all-in pricing.\n"
    )

@app.context_processor
def inject_site():
    return {"site": site_config()}


# ── Database ─────────────────────────────────────────────────────────────────
def init_db():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_FILE)
    con.execute("""
        CREATE TABLE IF NOT EXISTS listing_cache (
            vehicle_id TEXT, scope TEXT, data TEXT, fetched_at TEXT,
            PRIMARY KEY (vehicle_id, scope)
        )""")
    con.execute("CREATE TABLE IF NOT EXISTS notes (vehicle_id TEXT PRIMARY KEY, note TEXT, updated_at TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS favourites (vehicle_id TEXT PRIMARY KEY, added_at TEXT)")
    # Per-vehicle active overrides: lets the user archive/restore from the
    # web without editing vehicles.json. Lives on the Railway volume so
    # the overrides survive deploys; vehicles.json's `active` field is
    # the fallback when no override exists.
    con.execute("CREATE TABLE IF NOT EXISTS active_overrides (vehicle_id TEXT PRIMARY KEY, active INTEGER NOT NULL, updated_at TEXT NOT NULL)")
    con.commit()
    con.close()

# Ensure DB schema exists at import time so gunicorn workers don't race the
# first request. Local dev (python app.py) also benefits since the __main__
# init_db() call below becomes redundant but harmless.
init_db()


def merge_listings(live, manual):
    """Combine live-scrape and manually-curated listing payloads. Curated
    listings show first (they're hand-vetted); live listings follow, with
    duplicates dropped on URL or (year, price, title-prefix) hash. Source
    counts in the rendered footer sum both sources so the user sees the
    real total."""
    if not manual:
        return live
    if not live:
        # Render the manual payload directly but mark its provenance so the
        # footer counts make sense.
        out = dict(manual)
        out.setdefault("count_at", sum(1 for l in manual["listings"] if l.get("source") == "AutoTrader"))
        out.setdefault("count_cl", sum(1 for l in manual["listings"] if l.get("source") in ("Craigslist", "Kijiji")))
        return out
    manual_urls   = {l.get("url") for l in manual["listings"] if l.get("url")}
    manual_hashes = {f"{l.get('year','')}|{l.get('price','')}|{l.get('title','')[:30]}" for l in manual["listings"]}
    extra = []
    for l in live["listings"]:
        u = l.get("url", "")
        h = f"{l.get('year','')}|{l.get('price','')}|{l.get('title','')[:30]}"
        if u and u in manual_urls: continue
        if not u and h in manual_hashes: continue
        extra.append(l)
    merged = list(manual["listings"]) + extra
    out = dict(live)
    out["listings"] = merged
    out["count_at"] = live.get("count_at", 0) + sum(1 for l in manual["listings"] if l.get("source") == "AutoTrader")
    out["count_cl"] = live.get("count_cl", 0) + sum(1 for l in manual["listings"] if l.get("source") in ("Craigslist", "Kijiji"))
    out["blocked_warning"] = False
    return out

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

@lru_cache(maxsize=1)
def load_manual_listings():
    """Hand-curated listings keyed by vehicle_id. Used as a fallback when the
    live cache is empty for a (vehicle_id, scope), so a fresh container or
    a vehicle that's hard to scrape (Incapsula on AT) still has results."""
    if not MANUAL_LISTINGS_FILE.exists():
        return {}
    with open(MANUAL_LISTINGS_FILE) as f:
        return json.load(f)

def get_manual_listings(vehicle_id, scope):
    """Return the curated payload for (vehicle_id, scope), or None."""
    entry = load_manual_listings().get(vehicle_id)
    if not entry:
        return None
    if entry.get("scope") and entry["scope"] != scope:
        return None
    return entry

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

def get_active_overrides():
    """Return {vehicle_id: bool} for every vehicle the user has flipped
    from the web. Missing keys mean "no override — use vehicles.json"."""
    con = sqlite3.connect(DB_FILE)
    rows = con.execute("SELECT vehicle_id, active FROM active_overrides").fetchall()
    con.close()
    return {vid: bool(a) for vid, a in rows}

def set_active_override(vehicle_id, active):
    con = sqlite3.connect(DB_FILE)
    con.execute(
        "INSERT OR REPLACE INTO active_overrides VALUES (?,?,?)",
        (vehicle_id, 1 if active else 0, datetime.now().isoformat())
    )
    con.commit()
    con.close()


# ── Vehicle data ─────────────────────────────────────────────────────────────
# Active state is two-layer: vehicles.json carries an `active` flag (git-
# controlled default), and the SQLite `active_overrides` table on the
# Railway volume holds per-vehicle web-side overrides. Override wins
# when present. Inactive entries are excluded from list views and TCO
# normalization but remain accessible via direct /vehicle/<id> URLs.
@lru_cache(maxsize=1)
def _load_vehicles_raw():
    """Raw JSON entries, no override merge. Cached because the file is
    read-only at runtime."""
    with open(VEHICLES_FILE) as f:
        return json.load(f)

def load_vehicles_all():
    """Every entry, with `active` reflecting the SQLite override (if any)
    merged in. Use this for direct-by-id lookups and for the "archived"
    view that needs to surface inactive entries."""
    overrides = get_active_overrides()
    return [
        {**v, "active": overrides.get(v["id"], v.get("active", True))}
        for v in _load_vehicles_raw()
    ]

def load_vehicles():
    """Active vehicles only — the working cohort for list views and TCO
    normalization."""
    return [v for v in load_vehicles_all() if v["active"]]

def archived_vehicles():
    """Inactive vehicles — for the show-archived view."""
    return [v for v in load_vehicles_all() if not v["active"]]

def vehicle_by_id(vid):
    return next((v for v in load_vehicles_all() if v["id"] == vid), None)

def ranked_vehicles(weights, horizon=HORIZON_DEFAULT, cohort=None):
    """Vehicles re-derived at the given horizon (TCO components + tco_score
    refreshed across the cohort), then weighted-sum ranked. `cohort` lets
    callers score against a specific subset (the archived view does this).
    Default cohort is all active vehicles."""
    base = cohort if cohort is not None else load_vehicles()
    framed = reframe_for_horizon(base, horizon)
    return rank_vehicles(framed, weights)

def get_vehicle_images(vehicle_id):
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


# ── Weight + horizon URL helpers ─────────────────────────────────────────────
def parse_weights(source):
    """Parse w_<key> values from a MultiDict; missing/garbage → user defaults.
    Values are rounded to 1dp so hand-typed precision past the input's
    step="0.1" grid (e.g. 1.34) gets normalised server-side."""
    weights = {}
    defaults = default_weights()
    for key, default in defaults.items():
        try:
            weights[key] = round(float(source.get(f"w_{key}", default)), 1)
        except (TypeError, ValueError):
            weights[key] = default
    return weights

def parse_horizon(source):
    """Parse horizon param from MultiDict, clamped to [HORIZON_MIN, HORIZON_MAX].
    Garbage / missing → HORIZON_DEFAULT."""
    try:
        h = int(float(source.get("horizon", HORIZON_DEFAULT)))
    except (TypeError, ValueError):
        return HORIZON_DEFAULT
    return max(HORIZON_MIN, min(HORIZON_MAX, h))

def url_state_qs(weights, horizon):
    """Encode customised state as a query-string fragment (no leading ?/&).
    Empty when both weights and horizon are at user defaults."""
    parts = []
    defaults = default_weights()
    if any(weights[k] != defaults[k] for k in defaults):
        parts.extend(f"w_{k}={weights[k]}" for k in defaults)
    if horizon != HORIZON_DEFAULT:
        parts.append(f"horizon={horizon}")
    return "&".join(parts)


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    weights = parse_weights(request.args)
    horizon = parse_horizon(request.args)
    showing_archived = request.args.get("show") == "archived"
    favs = get_favourites()
    # `?show=archived` switches the grid to the inactive cohort so the
    # user can restore individual entries. Ranking only the active set
    # would leave archived entries unscored — rank them too.
    if showing_archived:
        vehicles = ranked_vehicles(weights, horizon, cohort=archived_vehicles())
    else:
        vehicles = ranked_vehicles(weights, horizon)
    for v in vehicles:
        v["is_favourite"] = v["id"] in favs
        v["images"] = get_vehicle_images(v["id"])
        v["badge_label"], v["badge_color"] = powertrain_badge(v["powertrain_type"])
    return render_template("index.html",
        vehicles=vehicles,
        weights=weights,
        horizon=horizon,
        horizon_min=HORIZON_MIN, horizon_max=HORIZON_MAX,
        horizon_default=HORIZON_DEFAULT,
        weights_default=default_weights(),
        state_qs=url_state_qs(weights, horizon),
        criteria_labels=CRITERIA_LABELS,
        scopes=SCOPES,
        showing_archived=showing_archived,
        archived_count=len(archived_vehicles()),
        active_count=len(load_vehicles()),
    )


@app.route("/rerank", methods=["POST"])
def rerank():
    weights = parse_weights(request.form)
    horizon = parse_horizon(request.form)
    favs = get_favourites()
    vehicles = ranked_vehicles(weights, horizon)
    for v in vehicles:
        v["is_favourite"] = v["id"] in favs
        v["images"] = get_vehicle_images(v["id"])
        v["badge_label"], v["badge_color"] = powertrain_badge(v["powertrain_type"])

    return render_template("partials/vehicle_cards.html",
        vehicles=vehicles,
        weights=weights,
        horizon=horizon,
        state_qs=url_state_qs(weights, horizon),
    )


@app.route("/vehicle/<vehicle_id>")
def vehicle_detail(vehicle_id):
    v = vehicle_by_id(vehicle_id)
    if not v:
        return "Vehicle not found", 404

    scope = request.args.get("scope", "bc")
    weights = parse_weights(request.args)
    horizon = parse_horizon(request.args)

    all_ranked = ranked_vehicles(weights, horizon)
    v_ranked = next((x for x in all_ranked if x["id"] == vehicle_id), None)
    # Inactive vehicle: still show its profile so bookmarks resolve.
    # Reframe it alongside the active cohort so its TCO components and
    # tco_score normalize against the visible peer group.
    if v_ranked is None:
        from scoring import reframe_for_horizon
        synthetic = reframe_for_horizon(load_vehicles() + [v], horizon)
        v_ranked = next(x for x in synthetic if x["id"] == vehicle_id)
        v_ranked["computed_score"] = compute_score(v_ranked, weights)
        v_ranked["computed_rank"] = None  # not in the active ranking
    score = v_ranked["computed_score"]
    rank = v_ranked["computed_rank"]
    # Use the horizon-adjusted copy of v so detail-page tables/specs reflect
    # the current horizon (TCO breakdown, fuel/maint/ins/resid, on-road).
    v = v_ranked

    # Always show curated listings; merge with the live cache if one
    # exists so refreshing genuinely adds entries rather than replacing
    # the curated set.
    listings_data = merge_listings(
        get_cached_listings(vehicle_id, scope),
        get_manual_listings(vehicle_id, scope),
    )

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
        horizon=horizon,
        state_qs=url_state_qs(weights, horizon),
        criteria_labels=CRITERIA_LABELS,
        images=images,
        listings_data=listings_data,
        scope=scope,
        scopes=SCOPES,
        is_favourite=vehicle_id in favs,
        is_active=v["active"],
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

    manual = get_manual_listings(vehicle_id, scope)
    if not force:
        cached = get_cached_listings(vehicle_id, scope)
        if cached or manual:
            return render_template("partials/listings.html",
                listings_data=merge_listings(cached, manual), **ctx)

    # Force refresh: scrape live, cache it, then merge with curated so the
    # hand-curated entries never get hidden by a successful scrape.
    data = fetch_listings(v, scope)
    save_cached_listings(vehicle_id, scope, data)
    data = merge_listings(data, manual)
    return render_template("partials/listings.html",
        listings_data=data, **ctx)


@app.route("/compare")
def compare():
    ids = request.args.getlist("ids")
    if not ids:
        ids = [v["id"] for v in load_vehicles()[:3]]

    weights = parse_weights(request.args)
    horizon = parse_horizon(request.args)
    ranked = ranked_vehicles(weights, horizon)
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
        horizon=horizon,
        state_qs=url_state_qs(weights, horizon),
    )


@app.route("/favourite/<vehicle_id>", methods=["POST"])
def favourite(vehicle_id):
    return jsonify({"is_favourite": toggle_favourite(vehicle_id)})


@app.route("/active/<vehicle_id>", methods=["POST"])
def toggle_active(vehicle_id):
    """Flip a vehicle's active state. Writes to the overrides table so
    the change survives deploys and doesn't conflict with vehicles.json
    edits from git."""
    v = vehicle_by_id(vehicle_id)
    if not v:
        return jsonify({"error": "not found"}), 404
    new_active = not v["active"]
    set_active_override(vehicle_id, new_active)
    return jsonify({"active": new_active, "archived_count": len(archived_vehicles()),
                    "active_count": len(load_vehicles())})


@app.route("/note/<vehicle_id>", methods=["POST"])
def note(vehicle_id):
    save_note(vehicle_id, request.form.get("note", ""))
    return jsonify({"saved": True})


@app.route("/images/<vehicle_id>/<filename>")
def serve_image(vehicle_id, filename):
    return send_from_directory(IMAGES_DIR / vehicle_id, filename)


# ── Sienna cross-shop view ─────────────────────────────────────────────────
# Single-page comparison of every Sienna option (cohort entries omitted —
# they're hypothetical; the listings + the active dealer quote are real).
# Math runs in the route (not in the cohort engine) so each candidate's
# warranty/km timeline is honestly modeled per-vehicle.

def _bc_pst_rate(sale_price):
    """BC luxury PST is a FLAT rate at price thresholds, applied to the
    whole purchase price. Returns the rate as a decimal."""
    if sale_price < 55000:       return 0.07
    elif sale_price < 56000:     return 0.08
    elif sale_price < 57000:     return 0.09
    elif sale_price < 125000:    return 0.10
    elif sale_price < 150000:    return 0.15
    else:                        return 0.20

def _bc_all_in(sale_price, license_fee=50):
    pst_rate = _bc_pst_rate(sale_price)
    gst = sale_price * 0.05
    pst = sale_price * pst_rate
    return {
        "sale": sale_price,
        "gst": gst,
        "pst": pst,
        "pst_rate": pst_rate,
        "license": license_fee,
        "all_in": sale_price + gst + pst + license_fee,
    }

def _sienna_residual(year_built, current_km, hold_years, trim):
    """Estimate retail residual for a Sienna AWD Hybrid at hold-end. Trims
    multiplier reflects typical resale ladder. Floor at $5,000."""
    annual_km = 15000
    end_km = current_km + hold_years * annual_km
    end_age = (2026 - year_built) + hold_years
    trim_mult = {"LE": 0.85, "XLE": 1.00, "XSE": 1.05,
                 "XSE Technology": 1.10, "Limited": 1.15, "Platinum": 1.25}.get(trim, 1.00)
    # Baseline XLE retail vs age (rough $ floor-curve)
    base = max(5000, 55000 * (0.90 ** min(end_age, 3)) * (0.95 ** max(0, end_age - 3)))
    # Mileage penalty: $0.10/km over 75k
    km_penalty = max(0, (end_km - 75000) * 0.10)
    return max(5000, base * trim_mult - km_penalty)

def _sienna_maint(year_built, current_km, hold_years):
    """Year-by-year maintenance, sensitive to which of the three warranty
    tiers (basic / system / battery) is active. Toyota ratios: ~$1,000 in,
    ~$2,500 OOW, +$500 high-km premium past 200k."""
    annual_km = 15000
    age_at_buy = 2026 - year_built
    total = 0
    for n in range(hold_years):
        age = age_at_buy + n
        km = current_km + (n + 1) * annual_km
        battery_active = (age < 10) and (km < 240000)
        system_active  = (age < 8)  and (km < 160000)
        if system_active:
            total += 1000   # in-warranty era
        elif battery_active:
            total += 2200   # past system warranty but battery still covers worst case
        else:
            total += 2700   # fully OOW
            if km > 200000: total += 500
            if age > 10:    total += 300
    return total

def _sienna_5_10(option):
    """Compute net 5-yr and 10-yr cost for a Sienna option dict."""
    annual_fuel = 1700
    annual_ins  = 1700
    out = dict(option)
    for hold in (5, 10):
        residual = _sienna_residual(option["year"], option["km"], hold, option["trim"])
        maint    = _sienna_maint(option["year"], option["km"], hold)
        fuel = hold * annual_fuel
        ins  = hold * annual_ins
        net  = option["all_in"] + fuel + ins + maint - residual
        out[f"residual_{hold}yr"] = residual
        out[f"maint_{hold}yr"]    = maint
        out[f"fuel_{hold}yr"]     = fuel
        out[f"ins_{hold}yr"]      = ins
        out[f"net_{hold}yr"]      = net
    return out

@app.route("/siennas")
def siennas():
    """Cross-shop table for every Sienna AWD Hybrid option — real listings
    plus the active dealer quote on the new 2026 LE. No hypothetical cohort
    entries."""
    options = []

    # 1) Listings from manual_listings.json (sienna-used, bc scope)
    bundle = get_manual_listings("sienna-used", "bc")
    if bundle:
        for l in bundle["listings"]:
            # Parse the visual strings back into structured fields
            try:
                year = int(l["year"])
                km = int(l["km"].replace("km", "").replace(",", "").strip())
                sale_str = l["price"].replace("$", "").replace(",", "").strip()
                if not sale_str.replace(".", "").isdigit():
                    continue  # "Please Contact" etc.
                sale_advertised = float(sale_str)
            except Exception:
                continue

            # Mandatory fees that get added to the sale price before tax.
            # Pulled from the per-listing _note where we captured them.
            mandatory_fee = 0
            note = (l.get("_note") or "").lower()
            if "1,298" in note or "1298" in note: mandatory_fee = 1298
            elif "595 doc" in note: mandatory_fee = 595
            else:
                # AT listings: assume dealer doc fee ~$895 unless flagged
                # (this matches Metro Van Toyota-dealer norm; Audi $895,
                # Destination $895, OpenRoad $895, Jim Pattison $895)
                if l["source"] == "AutoTrader" and "ON" not in l["location"] \
                   and "NS" not in l["location"] and "AB" not in l["location"]:
                    mandatory_fee = 895
                else:
                    mandatory_fee = 0  # out-of-province, treat as as-listed

            # Derive trim from title
            title_lower = l["title"].lower()
            if "limited" in title_lower:           trim = "Limited"
            elif "xse technology" in title_lower or "xse tech" in title_lower: trim = "XSE Technology"
            elif "xse" in title_lower:             trim = "XSE"
            elif "xle" in title_lower:             trim = "XLE"
            elif "le " in title_lower or title_lower.endswith("le"): trim = "LE"
            else:                                  trim = "XLE"

            sale = sale_advertised + mandatory_fee
            pricing = _bc_all_in(sale)
            options.append(_sienna_5_10({
                "id": f"listing-{l['url'][-20:]}",
                "source": l["source"],
                "source_icon": l["source_icon"],
                "year": year,
                "trim": trim,
                "km": km,
                "color": l.get("color", ""),
                "location": l["location"],
                "seller": l["seller"],
                "url": l["url"],
                "advertised": sale_advertised,
                "mandatory_fee": mandatory_fee,
                "sale": sale,
                "gst": pricing["gst"],
                "pst": pricing["pst"],
                "pst_rate": pricing["pst_rate"],
                "all_in": pricing["all_in"],
                "note": l.get("_note", ""),
                "is_quote": False,
            }))

    # 2) The active dealer quote for sienna-new, if any. Quotes live in
    # user-<family>/dealer_quotes/<vehicle-id>.json so they generalise to
    # any nameplate via the same /cross-shop/<vehicle-id> pattern later.
    quote_path = DATA_DIR / "dealer_quotes" / "sienna-new.json"
    if quote_path.exists():
        with open(quote_path) as f:
            q = json.load(f)
        pricing = _bc_all_in(q["sale_price_before_tax"])
        options.append(_sienna_5_10({
            "id": q["id"],
            "source": "Dealer Quote",
            "source_icon": "📝",
            "year": q["year"],
            "trim": q["trim"].split()[0],   # "LE" from "LE AWD 8-Pass"
            "km": 0,
            "color": q.get("color", ""),
            "location": "BC (active quote)",
            "seller": q["dealer"] + " — incl. mandatory Pro Pack + Dash Cam per dealer",
            "url": "",
            "advertised": q["msrp_breakdown"]["_total_msrp"],
            "mandatory_fee": q["dealer_extras"]["_total_extras"],
            "sale": q["sale_price_before_tax"],
            "gst": pricing["gst"],
            "pst": pricing["pst"],
            "pst_rate": pricing["pst_rate"],
            "all_in": pricing["all_in"],
            "note": f"Arrival ETA: {q['arrival_eta']}",
            "is_quote": True,
            "msrp_breakdown": q["msrp_breakdown"],
            "dealer_extras": q["dealer_extras"],
        }))

    # Compute "top picks" — the row each decision criterion points to. These
    # also drive per-row badges so the same vehicle picks up multiple
    # highlights if it wins more than one.
    badges_by_id = {}
    def _badge(opt, label, slug):
        if not opt:
            return
        badges_by_id.setdefault(opt["id"], []).append((label, slug))

    used_only = [o for o in options if not o["is_quote"]]
    quote_opt = next((o for o in options if o["is_quote"]), None)
    best_10yr = min(options, key=lambda o: o["net_10yr"]) if options else None
    best_5yr  = min(options, key=lambda o: o["net_5yr"])  if options else None
    cheapest  = min(options, key=lambda o: o["all_in"])   if options else None
    lowest_km = min((o for o in used_only if o["km"] > 0), key=lambda o: o["km"], default=None)
    _badge(best_10yr,  "Best 10-yr value",     "best-10yr")
    _badge(best_5yr,   "Best 5-yr value",      "best-5yr")
    _badge(cheapest,   "Lowest capital",       "cheapest")
    _badge(lowest_km,  "Lowest km used",       "lowest-km")
    _badge(quote_opt,  "Fresh warranty (new)", "fresh-warranty")

    top_picks = [
        {"slug": "best-10yr",       "title": "💰 Best 10-yr value",      "vehicle": best_10yr},
        {"slug": "fresh-warranty",  "title": "🛡 Fresh-warranty (new)",  "vehicle": quote_opt},
        {"slug": "lowest-km",       "title": "🚙 Lowest-km used",        "vehicle": lowest_km},
        {"slug": "cheapest",        "title": "💵 Lowest cash out the door","vehicle": cheapest},
    ]

    # Attach badges to each option for the table rows
    for o in options:
        o["badges"] = badges_by_id.get(o["id"], [])

    # Default sort: 10-yr net cost ascending
    sort_by = request.args.get("sort", "net_10yr")
    valid = {"net_5yr", "net_10yr", "all_in", "km", "year", "advertised"}
    if sort_by not in valid: sort_by = "net_10yr"
    reverse = sort_by == "year"  # newest first for year sort
    options.sort(key=lambda o: o.get(sort_by, 0), reverse=reverse)

    return render_template("siennas.html", options=options, sort_by=sort_by,
                           top_picks=top_picks, total_count=len(options))


@app.route("/api/vehicles")
def api_vehicles():
    weights = parse_weights(request.args)
    horizon = parse_horizon(request.args)
    vehicles = ranked_vehicles(weights, horizon)
    return jsonify([{
        "id": v["id"], "name": v["name"], "rank": v["computed_rank"],
        "score": v["computed_score"], "tco": v["tco_value"],
        "horizon": horizon,
    } for v in vehicles])


@app.route("/health")
def health():
    """Debug page — quick status of images, cache, and DB."""
    vehicles = load_vehicles()

    image_status = []
    for v in vehicles:
        vdir = IMAGES_DIR / v["id"]
        count = len(list(vdir.glob("*.jpg"))) if vdir.exists() else 0
        image_status.append({
            "id": v["id"], "name": v["short_name"],
            "count": count, "ok": count >= 4,
        })

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
<h1>Health Check</h1>

<h2>Images ({total_imgs} total, {img_ok}/{len(vehicles)} vehicles with ≥4 images)</h2>
{"<p class='warn'>Run: python scrapers/fetch_images.py</p>" if img_ok < len(vehicles) else "<p class='ok'>All vehicles have images</p>"}
<table><tr><th>Vehicle</th><th>Images</th><th>Status</th></tr>"""

    for s in image_status:
        status = f"<span class='ok'>OK {s['count']}</span>" if s["ok"] \
                 else f"<span class='warn'>WARN {s['count']}</span>"
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
<tr><td>Skill (app) root</td><td>{BASE}</td></tr>
<tr><td>Data dir</td><td>{DATA_DIR}</td></tr>
<tr><td>Vehicles JSON</td><td>{VEHICLES_FILE}</td></tr>
<tr><td>Weights JSON</td><td>{WEIGHTS_FILE}{"" if WEIGHTS_FILE.exists() else " (missing — using built-in fallback)"}</td></tr>
<tr><td>Images dir</td><td>{IMAGES_DIR}</td></tr>
<tr><td>Database</td><td>{DB_FILE}</td></tr>
</table>
</body></html>"""
    return html


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", "5000"))

    vehicles = load_vehicles()
    total_imgs = sum(
        len(list((IMAGES_DIR / v["id"]).glob("*.jpg")))
        for v in vehicles
        if (IMAGES_DIR / v["id"]).exists()
    )
    target_imgs = len(vehicles) * 6
    img_pct = int(total_imgs / target_imgs * 100) if target_imgs else 0

    url = f"http://localhost:{port}"
    W = 49
    def row(s):
        print(f"│ {s.ljust(W - 1)}│")
    print("┌" + "─" * W + "┐")
    row("Family Vehicle Browser")
    print("├" + "─" * W + "┤")
    row(f"Data:    {DATA_DIR.name}")
    row(f"URL:     {url}")
    row(f"Health:  {url}/health")
    row(f"Images:  {total_imgs}/{target_imgs}  ({img_pct}% of target)")
    if total_imgs < len(vehicles):
        row("Run: python scrapers/fetch_images.py")
    row("Ctrl+C to stop")
    print("└" + "─" * W + "┘")
    print()
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=port)
