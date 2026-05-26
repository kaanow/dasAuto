# Research Brief: Vehicle Image URL Curation

## Context

A local vehicle comparison web app displays 6 images per vehicle (target: 4 exterior +
2 interior). The current image scraper is unreliable (AutoTrader Incapsula blocks;
Wikimedia API returns empty responses). We are replacing it with a curated seed file
of pre-vetted image URLs that a simple download script will fetch.

Your job: find 6 working image URLs for each of the 12 vehicles below and output them
as a single JSON block. Save the block as "image_seeds.json" and output it the display.

---

## The 12 Vehicles

| id | Vehicle | Year(s) |
|----|---------|---------|
| `grand-highlander-new` | Toyota Grand Highlander Hybrid XLE | 2026 |
| `grand-highlander-used` | Toyota Grand Highlander Hybrid | 2023–2024 |
| `sienna-used` | Toyota Sienna Hybrid Woodland Edition | 2022–2023 |
| `ascent-used` | Subaru Ascent Touring | 2022–2023 |
| `highlander-hybrid-used` | Toyota Highlander Hybrid XLE | 2022–2023 |
| `palisade-used` | Hyundai Palisade | 2022–2023 |
| `telluride-used` | Kia Telluride EX | 2022–2023 |
| `pilot-used` | Honda Pilot (gen 4, 2023+) | 2023–2024 |
| `sorento-phev-used` | Kia Sorento PHEV | 2022–2023 |
| `cx90-phev-used` | Mazda CX-90 PHEV | 2024 |
| `ev9-used` | Kia EV9 Land AWD | 2024 |
| `ioniq9-new` | Hyundai IONIQ 9 | 2026 |

---

## Image Requirements

For **each vehicle**, find exactly **6 image URLs**:
- **4 exterior shots**: front 3/4, rear 3/4, side profile, or action/driving shot
- **2 interior shots**: dashboard/front cabin, and rear seats or cargo area

**Quality bar:**
- Minimum size: 800 × 500 px (larger is better — the app resizes to 900×600)
- Must be a direct image URL ending in `.jpg`, `.jpeg`, `.png`, or `.webp`
  (not a page URL, not a redirect, not a thumbnail gallery link)
- Must be publicly accessible without login (no paywalls, no auth)
- Must clearly show the correct vehicle (correct make/model/approximate year)

**Preferred sources (in order):**
1. **Manufacturer press/newsroom CDNs** — Toyota, Hyundai, Kia, Honda, Subaru, Mazda
   all publish high-res press photos. Examples of CDN patterns:
   - `media.toyota.com`, `www.hyundainews.com`, `www.kiamedia.com`,
     `hondanews.com`, `media.subaru.com`, `mazdamedia.com`
   - These are often direct `.jpg` URLs and persist for years
2. **Wikipedia article images** — fetch the Wikipedia article for each vehicle
   (e.g. `en.wikipedia.org/wiki/Toyota_Grand_Highlander`) and extract image URLs
   from the article body or infobox. Use the full-resolution URL
   (`upload.wikimedia.org/wikipedia/commons/...`) not the thumbnail.
3. **Car and Driver / Motor Trend / Car magazine press photo galleries** — these
   sites host manufacturer-supplied press photos at stable URLs.

**Avoid:**
- AutoTrader, Kijiji, Craigslist, or any classified listing site
- Sites that require cookies / JS / login to serve the image
- Watermarked dealer photos
- Social media embeds (Instagram, Facebook, Twitter)
- URLs containing `resize`, `thumb`, `w=`, `h=`, `fit=`, `crop=` query parameters
  (these are resizing proxies that may expire)

---

## Validation Before Submitting

For **every URL** you include:
1. Confirm the URL is a direct image link (ends in `.jpg/.jpeg/.png/.webp` or
   content-type is `image/*`)
2. Confirm it loads without a login wall
3. Confirm the image shows the correct vehicle (right make/model/era)
4. Confirm it is ≥ 800 px wide

If you cannot find 6 validated URLs for a vehicle, output as many as you can
(minimum 2) and note the shortfall in the `notes` field.

---

## Output Format

Respond with **only** a JSON code block in the following exact schema.
Do not include any text before or after the JSON block.

```json
[
  {
    "id": "grand-highlander-new",
    "images": [
      {"url": "https://...", "type": "exterior", "caption": "2026 Toyota Grand Highlander front 3/4"},
      {"url": "https://...", "type": "exterior", "caption": "2026 Toyota Grand Highlander rear"},
      {"url": "https://...", "type": "exterior", "caption": "2026 Toyota Grand Highlander side"},
      {"url": "https://...", "type": "exterior", "caption": "2026 Toyota Grand Highlander driving"},
      {"url": "https://...", "type": "interior", "caption": "2026 Toyota Grand Highlander dashboard"},
      {"url": "https://...", "type": "interior", "caption": "2026 Toyota Grand Highlander rear seats"}
    ],
    "notes": ""
  },
  {
    "id": "grand-highlander-used",
    ...
  },
  ...all 12 vehicles...
]
```

Fields:
- `id` — must match exactly the IDs in the table above
- `images` — list of image objects; exterior first, then interior
- `url` — direct image URL, validated as described
- `type` — `"exterior"` or `"interior"`
- `caption` — brief description of what the image shows
- `notes` — empty string if all 6 found; otherwise describe any shortfall or substitutions

The JSON must be valid and parseable. All 12 vehicles must be present.

---

## What NOT to do

- Do not fabricate URLs — every URL must be confirmed to work
- Do not include page URLs instead of direct image URLs
- Do not include duplicate images (same image from two different CDN paths)
- Do not paraphrase or summarize — just output the JSON block
