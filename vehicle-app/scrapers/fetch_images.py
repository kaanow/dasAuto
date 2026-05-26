"""
Vehicle image downloader — seed-file based.

Reads <data-dir>/image_seeds.json (curated list of pre-vetted image URLs
per vehicle), downloads each image, letterbox-resizes to 900x600 on a
dark background, and saves to <data-dir>/images/<vehicle-id>/00.jpg, ...

Usage:
    python scrapers/fetch_images.py              # skip vehicles that already have images
    python scrapers/fetch_images.py --refresh    # clear and re-fetch all

The data dir is taken from VEHICLE_DATA_DIR (same env var the Flask app
uses); defaults to ../user-kaan-and-tess relative to this file. Generate
image_seeds.json by handing briefs/image_research_brief.md to a research
agent and pasting the returned JSON into <data-dir>/image_seeds.json.
"""

import json, os, sys, time, hashlib
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageDraw

SKILL_ROOT = Path(__file__).parent.parent
DATA_DIR = Path(
    os.environ.get("VEHICLE_DATA_DIR")
    or SKILL_ROOT.parent / "user-kaan-and-tess"
).resolve()

IMAGES_DIR  = DATA_DIR / "images"
DATA_FILE   = DATA_DIR / "vehicles.json"
SEEDS_FILE  = DATA_DIR / "image_seeds.json"

# Wikimedia returns 429 for generic browser User-Agents. Their policy requires
# an identifiable UA with contact info. See:
#   https://meta.wikimedia.org/wiki/User-Agent_policy
HEADERS = {
    "User-Agent": "bc-family-vehicle-browser/1.0 "
                  "(local Flask app; https://github.com/kaanow/dasAuto)",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

TARGET_W, TARGET_H = 900, 600
BG_COLOR = (20, 26, 40)      # dark blue-grey, matches app CSS #14181e
MIN_W, MIN_H = 400, 250      # reject images smaller than this


# ---------------------------------------------------------------------------
# Image download + letterbox
# ---------------------------------------------------------------------------

def download_and_letterbox(url, save_path, retries=2):
    """
    Fetch url, letterbox-resize to TARGET_W x TARGET_H on BG_COLOR background,
    save as JPEG. Returns True on success.
    """
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20, stream=True)
            if r.status_code != 200:
                return False
            ct = r.headers.get("content-type", "")
            if "image" not in ct and not url.lower().split("?")[0].endswith(
                    (".jpg", ".jpeg", ".png", ".webp", ".gif")):
                return False

            img = Image.open(BytesIO(r.content)).convert("RGB")

            if img.width < MIN_W or img.height < MIN_H:
                return False  # too small to be useful

            # Scale to fit within target, preserve aspect ratio
            img.thumbnail((TARGET_W, TARGET_H), Image.LANCZOS)

            # Paste centred onto background
            bg = Image.new("RGB", (TARGET_W, TARGET_H), BG_COLOR)
            x = (TARGET_W - img.width) // 2
            y = (TARGET_H - img.height) // 2
            bg.paste(img, (x, y))
            bg.save(save_path, "JPEG", quality=85, optimize=True)
            return True

        except Exception:
            if attempt < retries:
                time.sleep(1 * (attempt + 1))
    return False


def file_md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


# ---------------------------------------------------------------------------
# Placeholder
# ---------------------------------------------------------------------------

def make_placeholder(vehicle, save_path):
    """Create a dark placeholder with the vehicle name."""
    img = Image.new("RGB", (TARGET_W, TARGET_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    draw.text((TARGET_W // 2, TARGET_H // 2 - 20),
              vehicle.get("short_name", vehicle["id"]),
              fill=(200, 200, 200), anchor="mm")
    draw.text((TARGET_W // 2, TARGET_H // 2 + 20),
              "Image not available",
              fill=(120, 120, 120), anchor="mm")
    img.save(save_path, "JPEG")


# ---------------------------------------------------------------------------
# Per-vehicle fetch
# ---------------------------------------------------------------------------

def fetch_vehicle(vehicle, seed_images, refresh=False):
    vid  = vehicle["id"]
    name = vehicle.get("short_name", vid)
    vdir = IMAGES_DIR / vid
    vdir.mkdir(parents=True, exist_ok=True)

    if refresh:
        for f in vdir.glob("*.jpg"):
            f.unlink()

    existing = list(vdir.glob("*.jpg"))
    if existing and not refresh:
        print(f"  [SKIP] {name}: {len(existing)} images already present")
        return len(existing)

    print(f"  [IMG] {name} ", end="", flush=True)

    known_hashes = set()
    downloaded = 0
    img_index = 0

    for entry in seed_images:
        url = entry.get("url", "").strip()
        if not url:
            continue

        save_path = vdir / f"{img_index:02d}.jpg"

        if not download_and_letterbox(url, save_path):
            print("x", end="", flush=True)
            time.sleep(0.3)
            continue

        h = file_md5(save_path)
        if h in known_hashes:
            save_path.unlink()   # duplicate
            print("=", end="", flush=True)
            continue

        known_hashes.add(h)
        downloaded += 1
        img_index += 1
        print(".", end="", flush=True)
        time.sleep(0.25)

    if downloaded == 0:
        make_placeholder(vehicle, vdir / "00.jpg")
        print(f" [FAIL] 0/{len(seed_images)}")
    else:
        status = "OK" if downloaded >= 4 else "~"
        print(f" [{status}] {downloaded}/{len(seed_images)}")

    return downloaded


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    refresh = "--refresh" in sys.argv

    if not SEEDS_FILE.exists():
        print(f"ERROR: {SEEDS_FILE} not found.")
        print()
        print("To create it:")
        print("  1. Hand IMAGE_RESEARCH_BRIEF.md to a research-capable chat agent.")
        print("  2. Paste the returned JSON into data/image_seeds.json.")
        print("  3. Re-run this script.")
        sys.exit(1)

    with open(DATA_FILE) as f:
        vehicles = json.load(f)

    with open(SEEDS_FILE) as f:
        seeds_list = json.load(f)

    # Index seeds by vehicle id for O(1) lookup
    seeds = {entry["id"]: entry.get("images", []) for entry in seeds_list}

    if refresh:
        print("--refresh: clearing and re-fetching all images\n")
    print(f"Downloading images for {len(vehicles)} vehicles...\n")

    results = []
    for v in vehicles:
        vid = v["id"]
        seed_images = seeds.get(vid, [])
        if not seed_images:
            print(f"  [WARN] {v.get('short_name', vid)}: no seed URLs in image_seeds.json — placeholder only")
            vdir = IMAGES_DIR / vid
            vdir.mkdir(parents=True, exist_ok=True)
            make_placeholder(v, vdir / "00.jpg")
            results.append((v["short_name"], 0))
            continue

        count = fetch_vehicle(v, seed_images, refresh=refresh)
        results.append((v.get("short_name", vid), count))
        time.sleep(0.5)

    print("\n=== Download complete ===")
    for name, count in results:
        status = "OK" if count >= 4 else ("~" if count > 0 else "FAIL")
        print(f"  [{status}] {name}: {count} images")


if __name__ == "__main__":
    main()
