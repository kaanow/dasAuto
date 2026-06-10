"""One-shot: resolve real Wikimedia Commons image URLs for the theo cohort
and write image_seeds.json. Uses the Commons search-generator + imageinfo so
the URLs are live upload.wikimedia.org links the fetcher can download.

Re-run to regenerate. Tune QUERIES if a vehicle gets poor matches.
"""
import json, time, urllib.parse
from pathlib import Path
import requests

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "dasauto-image-seeder/1.0 (https://github.com/kaanow/dasAuto)"}

# Per-vehicle Commons search terms. Bias to the right generation where it helps.
QUERIES = {
    "tesla-model-y-new":     "Tesla Model Y",
    "tesla-model-y-used":    "Tesla Model Y 2022",
    "tesla-model-3-used":    "Tesla Model 3 2022",
    "ioniq5-new":            "Hyundai Ioniq 5",
    "ev6-used":              "Kia EV6",
    "ioniq6-new":            "Hyundai Ioniq 6",
    "bolt-euv-used":         "Chevrolet Bolt",
    "id4-used":              "Volkswagen ID.4",
    "rav4-prime-new":        "Toyota RAV4 Prime plug-in hybrid",
    "prius-prime-new":       "Toyota Prius 2023",
    "niro-phev-used":        "Kia Niro",
    "tucson-phev-used":      "Hyundai Tucson NX4",
    "rav4-hybrid-new":       "Toyota RAV4 Hybrid",
    "crv-hybrid-new":        "Honda CR-V 2023",
    "corolla-hybrid-new":    "Toyota Corolla Hybrid",
    "prius-new":             "Toyota Prius 2023",
    "mazda-cx5-new":         "Mazda CX-5",
    "outback-used":          "Subaru Outback 2022",
    "corolla-2018-current":  "Toyota Corolla 2018 sedan",
}

# Skip obvious non-photos by title substring.
BAD = ("logo", "emblem", "map", "diagram", "badge", "wordmark", "charging",
       "engine", "chassis", "patent", "drawing", " vin", "gauge")

def resolve(query, want=7):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{query} car", "gsrnamespace": "6", "gsrlimit": "30",
        "prop": "imageinfo", "iiprop": "url|size|mime",
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    pages = (r.json().get("query", {}) or {}).get("pages", {})
    cands = []
    for p in pages.values():
        title = p.get("title", "")
        ii = (p.get("imageinfo") or [{}])[0]
        url, w, h, mime = ii.get("url"), ii.get("width", 0), ii.get("height", 0), ii.get("mime", "")
        if not url or mime not in ("image/jpeg", "image/png"):
            continue
        tl = title.lower()
        if any(b in tl for b in BAD):
            continue
        if w < 800 or h < 500 or w > h * 2.4:  # reject tiny / banner-shaped
            continue
        cands.append({"idx": p.get("index", 99), "url": url, "w": w,
                      "caption": title[5:].rsplit(".", 1)[0].replace("_", " ")})
    cands.sort(key=lambda c: c["idx"])          # search relevance order
    return cands[:want]

def main():
    out = []
    for vid, q in QUERIES.items():
        try:
            cands = resolve(q)
        except Exception as e:
            print(f"  [ERR] {vid}: {e}")
            cands = []
        imgs = [{"url": c["url"], "type": "exterior", "caption": c["caption"]} for c in cands]
        out.append({"id": vid, "images": imgs,
                    "notes": f"Auto-resolved from Wikimedia Commons search '{q}'. "
                             f"{len(imgs)} candidates; representative of the model/generation."})
        print(f"  {vid:24} {len(imgs)} imgs  (q='{q}')")
        time.sleep(0.4)
    path = Path(__file__).parent / "image_seeds.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {path}")

if __name__ == "__main__":
    main()
