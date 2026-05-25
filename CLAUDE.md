# CLAUDE.md — BC Family Vehicle Browser
<!-- IMPORTANT: Every Claude session working on this project must update this
file with any new architectural decisions, changed behaviour, or in-progress
work before ending. Keep it concise and factual. This file is the source of
truth for project state — do not use user-level memory for project details. -->

## Project summary
Local Flask web app for browsing 12 candidate family vehicles.
Companion to a spreadsheet/PDF comparison project for a Vancouver BC family.
Run with: `python app.py` → http://localhost:5000

## Stack
- Flask + Jinja2 templates
- HTMX for partial page updates (re-ranking, listings fetch)
- SQLite (data/cache.db) for listing cache, notes, favourites
- Plain CSS (static/css/style.css) — no build step
- BeautifulSoup scraper for AutoTrader.ca and Craigslist Vancouver

## Architectural decisions
- **Scoring:** 1 continuous TCO score (weight 3.0) + 8 qualitative criteria (1-5).
  TCO score = 1 + 4×(max_TCO − this_TCO)÷(max_TCO − min_TCO). This replaced
  5 separate financial sub-scores that were double-counting residual value.
- **Re-ranking:** Server-side via `/rerank` POST, returns card partial HTML.
  Weights are editable number fields, not sliders (user preference).
- **Listings:** AutoTrader scraped + cached 12hr in SQLite. Craigslist scraped
  fresh each time. Kijiji/CarGurus/Facebook are deep links only.
- **Images:** Downloaded by `scrapers/fetch_images.py`. Primary source: AutoTrader.ca
  search result thumbnails (full-res via CDN `-WxH` suffix stripping, 3 paginated
  pages). Fallback: Wikimedia Commons with `require_make` title filter to avoid
  place-name false matches (e.g. "Telluride" CO). Letterbox resize (no crop).
  MD5 dedup prevents saving identical images from duplicate AT CDN URLs.
  Run `--refresh` flag to clear and re-fetch all. AT is blocked on sandbox IPs
  (Incapsula); run from home laptop. Stored in `images/<vehicle-id>/`.
  App serves them via `/images/<id>/<file>`.
- **at_url_override field:** Grand Highlander requires `mdl=Grand+Highlander`
  query param on AT (slug-based URL returns unrelated Toyota inventory).
  Set in vehicles.json, honoured by `autotrader_url()` in scrapers/listings.py.
- **No at_status filter:** AT's `sts=New/Used` filter is unreliable — returns
  wrong vehicles. Year range (`yRng=`) is the only reliable filter used.

## Known issues / watch list
- AutoTrader.ca uses Incapsula bot detection. Sandbox IPs get rate-limited
  after ~10 requests. Home laptop IPs are not affected.
- Craigslist relevance filtering is fuzzy (make+model in title). Dealer spam
  occasionally slips through.
- UI not yet tested in a real browser — CSS may need responsive tweaks.
- Full vehicle detail page audit was not completed before handoff.

## In-progress / not yet done
- **Run `python scrapers/fetch_images.py --refresh` from home laptop** — AT is
  Incapsula-blocked on sandbox; current images are Wikimedia-only (2-4/vehicle).
  At home, expect 5-6/vehicle with real BC listing photos.
- Browser testing and CSS polish pass
- Print stylesheet for compare page
- Full detail page audit (see HANDOFF.md for the test script)

## Key files
- `data/vehicles.json` — all 12 candidates, scores, profile text, AT URLs
- `data/cache.db` — SQLite, created on first run
- `scrapers/listings.py` — scraper + deep link generators
- `scrapers/fetch_images.py` — one-time image downloader
- `app.py` — all Flask routes
- `HANDOFF.md` — full session handoff notes for new agents

## Last updated
April 5 2026 — session 2: project scaffolded into correct directory structure,
launch .bat created, image fetcher rewritten (AT thumbnails + Wikimedia fallback,
letterbox crop, MD5 dedup, title validation, require_make filter).
