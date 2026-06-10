"""Re-resolve image seeds for the vehicles the audit left too thin, using
tighter queries + a stricter junk filter (blocks race concepts, Suzuki Across
rebadges, wrong-gen, diecast, wrong-model). Rewrites those entries in
image_seeds.json. Then: clear those dirs + run fetch_images.py.
"""
import json, time
from pathlib import Path
import requests

API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "dasauto-image-seeder/1.0 (https://github.com/kaanow/dasAuto)"}

# Tighter, generation/body-specific queries for the thin vehicles.
QUERIES = {
    "corolla-hybrid-new":   "Toyota Corolla sedan 2021",
    "corolla-2018-current": "Toyota Corolla 2016 sedan",
}
# Stricter blocklist for this pass.
BAD = ("logo", "emblem", "map", "diagram", "badge", "wordmark", "charging",
       "engine", "chassis", "patent", "drawing", " vin", "gauge",
       "across", "suzuki", "concept", "race", "racing", "motorsport", "tcr",
       "rn22", "en1", "pikes", "rally", "toy", "diecast", "scale", "model car",
       "cross", "nissan", "model s", "model 3", "ioniq 6", "interior",
       "dashboard", "cockpit", "wheel", "steering", "exeed", "chery",
       "subscribe", "police", "livery", "team", "tc2000", "touring", "taxi",
       "wrc", "rallye", "e210", "gr ")

def resolve(query, want=7):
    params = {"action": "query", "format": "json", "generator": "search",
              "gsrsearch": f"{query} car", "gsrnamespace": "6", "gsrlimit": "40",
              "prop": "imageinfo", "iiprop": "url|size|mime"}
    r = requests.get(API, params=params, headers=HEADERS, timeout=30); r.raise_for_status()
    pages = (r.json().get("query", {}) or {}).get("pages", {})
    cands = []
    for p in pages.values():
        title = p.get("title", ""); ii = (p.get("imageinfo") or [{}])[0]
        url, w, h, mime = ii.get("url"), ii.get("width", 0), ii.get("height", 0), ii.get("mime", "")
        if not url or mime not in ("image/jpeg", "image/png"): continue
        tl = title.lower()
        if any(b in tl for b in BAD): continue
        if w < 800 or h < 500 or w > h * 2.4: continue
        cands.append({"idx": p.get("index", 99), "url": url,
                      "caption": title[5:].rsplit(".", 1)[0].replace("_", " ")})
    cands.sort(key=lambda c: c["idx"])
    return cands[:want]

def main():
    seeds_path = Path(__file__).parent / "image_seeds.json"
    seeds = json.loads(seeds_path.read_text())
    by_id = {e["id"]: e for e in seeds}
    for vid, q in QUERIES.items():
        cands = resolve(q)
        by_id[vid]["images"] = [{"url": c["url"], "type": "exterior", "caption": c["caption"]} for c in cands]
        by_id[vid]["notes"] = f"Re-resolved (audit) from Commons '{q}' with strict junk filter. {len(cands)} candidates."
        print(f"  {vid:24} {len(cands)} imgs  (q='{q}')")
        time.sleep(0.4)
    seeds_path.write_text(json.dumps(seeds, indent=2))
    print("rewrote image_seeds.json")

if __name__ == "__main__":
    main()
