"""
Image downloader for vehicle app.
Fetches images from DuckDuckGo image search (no API key required)
and saves them locally organized by vehicle ID.
Run once: python scrapers/fetch_images.py
"""

import json, os, re, time, hashlib
from pathlib import Path
from urllib.parse import quote_plus, urlencode
import requests
from PIL import Image
from io import BytesIO

IMAGES_DIR = Path(__file__).parent.parent / "images"
DATA_FILE  = Path(__file__).parent.parent / "data" / "vehicles.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-CA,en;q=0.9",
}

TARGET_W, TARGET_H = 900, 600  # resize target
IMAGES_PER_VEHICLE = 6


def ddg_image_urls(query, count=3):
    """Fetch image URLs from DuckDuckGo image search."""
    url = f"https://duckduckgo.com/?q={quote_plus(query)}&iax=images&ia=images"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        vqd_match = re.search(r"vqd=([\d-]+)", r.text)
        if not vqd_match:
            return []
        vqd = vqd_match.group(1)
    except Exception as e:
        print(f"    DDG token error: {e}")
        return []

    params = {
        "l": "ca-en", "o": "json", "q": query,
        "vqd": vqd, "f": ",,,,,", "p": "1"
    }
    api_url = "https://duckduckgo.com/i.js?" + urlencode(params)
    try:
        r2 = requests.get(api_url, headers={**HEADERS, "Referer": url}, timeout=10)
        data = r2.json()
        results = data.get("results", [])
        return [r["image"] for r in results[:count*2] if r.get("image")]
    except Exception as e:
        print(f"    DDG API error: {e}")
        return []


def download_image(url, save_path, target_w=TARGET_W, target_h=TARGET_H, retries=2):
    """Download, resize and save an image. Returns True on success."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15, stream=True)
            if r.status_code != 200:
                return False
            content_type = r.headers.get("content-type", "")
            if "image" not in content_type:
                return False

            img = Image.open(BytesIO(r.content)).convert("RGB")

            # Reject images that are too small to be useful
            if img.width < 300 or img.height < 200:
                return False

            # Crop to 3:2 aspect ratio from centre
            w, h = img.size
            target_ratio = target_w / target_h
            current_ratio = w / h
            if current_ratio > target_ratio:
                new_w = int(h * target_ratio)
                left = (w - new_w) // 2
                img = img.crop((left, 0, left + new_w, h))
            else:
                new_h = int(w / target_ratio)
                top = (h - new_h) // 2
                img = img.crop((0, top, w, top + new_h))

            img = img.resize((target_w, target_h), Image.LANCZOS)
            img.save(save_path, "JPEG", quality=85, optimize=True)
            return True
        except Exception:
            if attempt < retries:
                time.sleep(0.5 * (attempt + 1))
            continue
    return False


def fetch_vehicle_images(vehicle):
    vid = vehicle["id"]
    vdir = IMAGES_DIR / vid
    vdir.mkdir(parents=True, exist_ok=True)

    existing = list(vdir.glob("*.jpg"))
    if len(existing) >= IMAGES_PER_VEHICLE:
        print(f"  ✓ {vehicle['short_name']}: {len(existing)} images already present")
        return

    queries = vehicle.get("image_queries", [vehicle["name"]])
    downloaded = len(existing)
    img_index  = len(existing)

    print(f"  📷 {vehicle['short_name']} ", end="", flush=True)

    for query in queries:
        if downloaded >= IMAGES_PER_VEHICLE:
            break

        urls = ddg_image_urls(query, count=4)
        time.sleep(0.6)

        for url in urls:
            if downloaded >= IMAGES_PER_VEHICLE:
                break
            if any(skip in url.lower() for skip in ["svg", "logo", "icon", "sprite"]):
                continue

            save_path = vdir / f"{img_index:02d}.jpg"
            if download_image(url, save_path):
                downloaded += 1
                img_index += 1
                print(".", end="", flush=True)
                time.sleep(0.25)

    # If we got fewer than minimum, try broader queries
    if downloaded < 3:
        broader = [f"{vehicle['make']} {vehicle['model']} SUV exterior",
                   f"{vehicle['make']} {vehicle['model']} interior seats"]
        for query in broader:
            if downloaded >= IMAGES_PER_VEHICLE:
                break
            urls = ddg_image_urls(query, count=3)
            time.sleep(0.5)
            for url in urls:
                if downloaded >= IMAGES_PER_VEHICLE:
                    break
                save_path = vdir / f"{img_index:02d}.jpg"
                if download_image(url, save_path):
                    downloaded += 1
                    img_index += 1
                    print(".", end="", flush=True)

    status = "✓" if downloaded >= 4 else ("△" if downloaded > 0 else "✗")
    print(f" {status} {downloaded}/{IMAGES_PER_VEHICLE}")


def create_placeholder(vehicle):
    """Create a simple placeholder image if downloads fail."""
    vid = vehicle["id"]
    vdir = IMAGES_DIR / vid
    vdir.mkdir(parents=True, exist_ok=True)

    placeholder = vdir / "00.jpg"
    if not placeholder.exists():
        img = Image.new("RGB", (900, 600), color=(30, 56, 100))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((450, 280), vehicle["short_name"],
                  fill=(255,255,255), anchor="mm")
        draw.text((450, 320), f"Image not available",
                  fill=(180,180,180), anchor="mm")
        img.save(placeholder, "JPEG")


def main():
    with open(DATA_FILE) as f:
        vehicles = json.load(f)

    print(f"Fetching images for {len(vehicles)} vehicles...\n")
    for v in vehicles:
        try:
            fetch_vehicle_images(v)
        except Exception as e:
            print(f"  ✗ Error for {v['short_name']}: {e}")
            create_placeholder(v)
        time.sleep(1)

    # Count results
    print("\n=== Image fetch complete ===")
    for v in vehicles:
        vdir = IMAGES_DIR / v["id"]
        count = len(list(vdir.glob("*.jpg"))) if vdir.exists() else 0
        status = "✓" if count >= 4 else ("△" if count > 0 else "✗")
        print(f"  {status} {v['short_name']}: {count} images")


if __name__ == "__main__":
    main()
