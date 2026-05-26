"""
Listings scraper for vehicle app.
Sources: AutoTrader.ca (scraped), Craigslist Vancouver (scraped),
         Kijiji / CarGurus / Facebook (deep links only).
"""

import re, time, json
from datetime import datetime, timedelta
from urllib.parse import quote_plus
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-CA,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

# Geographic scope options
# `prov` is the AutoTrader URL path/query province segment ("ca" disables the
# province filter for national searches).
SCOPES = {
    "vancouver":  {"prx": "50",  "loc": "Vancouver,+BC", "prov": "bc",
                   "prv": "British+Columbia",
                   "label": "Within 50 km of Vancouver"},
    "bc":         {"prx": "-2",  "loc": "BC",            "prov": "bc",
                   "prv": "British+Columbia",
                   "label": "All of BC"},
    "national":   {"prx": "-1",  "loc": "Canada",        "prov": "ca",
                   "prv": "",
                   "label": "All of Canada"},
}


# ─────────────────────────────────────────────────────────────────────────────
# AutoTrader.ca
# ─────────────────────────────────────────────────────────────────────────────

def autotrader_url(vehicle, scope="bc"):
    sc = SCOPES.get(scope, SCOPES["bc"])

    # Some vehicles need a custom URL structure (e.g. Grand Highlander uses mdl= param)
    if vehicle.get("at_url_override"):
        base = vehicle["at_url_override"]
        # Substitute scope-dependent fields. The override has /<prov>/ in the path
        # and prv=/loc=/prx= in the query — keep them all in sync with `sc`.
        base = re.sub(r"prx=-?\d+", f"prx={sc['prx']}", base)
        base = re.sub(r"loc=[^&]+", f"loc={sc['loc']}", base)
        base = re.sub(r"prv=[^&]+", f"prv={sc['prv']}", base) if sc["prv"] else \
               re.sub(r"&?prv=[^&]+", "", base)
        base = re.sub(r"/cars/([^/]+)/[a-z]{2}/", f"/cars/\\1/{sc['prov']}/", base)
        return base

    make  = vehicle["at_make"]
    model = vehicle["at_model"]
    yr    = vehicle.get("at_years", "")
    yr_param = f"&yRng={yr}" if yr else ""
    prv_param = f"&prv={sc['prv']}" if sc["prv"] else ""
    return (
        f"https://www.autotrader.ca/cars/{make}/{model}/{sc['prov']}/"
        f"?rcp=15&rcs=0&srt=35"
        f"&prx={sc['prx']}{prv_param}&loc={sc['loc']}"
        f"&hprc=True&wcp=True{yr_param}"
    )


def _is_blocked(response):
    """Detect Incapsula / bot-detection block pages."""
    if response.status_code != 200:
        return True
    if b"Incapsula incident" in response.content:
        return True
    if b"Access Denied" in response.content and len(response.content) < 5000:
        return True
    return False


def scrape_autotrader(vehicle, scope="bc", max_listings=12):
    url = autotrader_url(vehicle, scope)
    listings = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)

        if _is_blocked(r):
            print(f"  ⚠ AutoTrader blocked request for {vehicle['short_name']} "
                  f"(bot detection). Will show deep links instead.")
            return listings, url

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("div", class_=lambda c: c and "result-item" in str(c))

        seen_urls = set()
        for item in items:
            try:
                title_el  = item.find(class_="result-title")
                price_el  = item.find(class_="price-amount")
                km_el     = item.find(class_="kms")
                loc_el    = item.find(class_="proximity-text")
                seller_el = item.find(class_="seller-name")
                link_el   = item.find("a", class_="inner-link")
                img_el    = item.find("img")

                title = (title_el.get_text(strip=True) if title_el else "").strip()
                if not title:
                    continue

                yr_match = re.search(r"\b(20\d{2})\b", title)
                year = yr_match.group(1) if yr_match else ""

                price_raw = price_el.get_text(strip=True) if price_el else ""
                price_match = re.search(r"\$([\d,]+)", price_raw)
                price = "$" + price_match.group(1) if price_match else "Contact"

                listing_url = ""
                if link_el and link_el.get("href"):
                    href = link_el["href"]
                    listing_url = "https://www.autotrader.ca" + href if href.startswith("/") else href

                if listing_url in seen_urls:
                    continue
                seen_urls.add(listing_url)

                thumb = ""
                if img_el:
                    thumb = img_el.get("src") or img_el.get("data-src") or ""

                listings.append({
                    "source": "AutoTrader.ca",
                    "source_icon": "🚗",
                    "title": title[:80],
                    "year": year,
                    "price": price,
                    "km": km_el.get_text(strip=True) if km_el else "",
                    "location": loc_el.get_text(strip=True) if loc_el else "",
                    "seller": seller_el.get_text(strip=True) if seller_el else "",
                    "url": listing_url,
                    "thumb": thumb,
                    "fetched_at": datetime.now().isoformat(),
                })

                if len(listings) >= max_listings:
                    break
            except Exception:
                continue

    except Exception as e:
        print(f"  AutoTrader scrape error: {e}")

    return listings, url


# ─────────────────────────────────────────────────────────────────────────────
# Craigslist Vancouver
# ─────────────────────────────────────────────────────────────────────────────

def craigslist_query(vehicle):
    """Build a good Craigslist search query for this vehicle."""
    make  = vehicle["make"].lower()
    model = vehicle["model"].lower().replace("+", " ").replace("-", " ")
    years = vehicle["years"].replace("–", "-")
    yr_from = years.split("-")[0] if "-" in years or "–" in years else years
    return f"{make} {model} {yr_from}"


def craigslist_url(vehicle):
    query = craigslist_query(vehicle)
    return f"https://vancouver.craigslist.org/search/cta?query={quote_plus(query)}&sort=date"


def scrape_craigslist(vehicle, max_listings=8):
    url = craigslist_url(vehicle)
    listings = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if _is_blocked(r):
            print(f"  ⚠ Craigslist blocked request for {vehicle['short_name']}")
            return listings, url
        if r.status_code != 200:
            return listings, url

        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("li", class_="cl-static-search-result")

        make_lower  = vehicle["make"].lower()
        model_parts = vehicle["model"].lower().replace("+", " ").split()

        for item in items:
            try:
                a   = item.find("a", href=True)
                txt = item.get_text(separator="|", strip=True)

                title_raw = txt.split("$")[0].strip() if "$" in txt else txt.split("|")[0].strip()

                # Basic relevance filter
                title_lower = title_raw.lower()
                if make_lower not in title_lower:
                    continue
                if not any(mp in title_lower for mp in model_parts):
                    continue

                price_match = re.search(r'\$([\d,]+)', txt)
                price = "$" + price_match.group(1) if price_match else "Contact"

                parts = txt.split("|")
                location = parts[-1].strip() if len(parts) > 1 else "Vancouver area"

                yr_match = re.search(r"\b(20\d{2})\b", title_raw)
                year = yr_match.group(1) if yr_match else ""

                listing_url = a["href"] if a else ""
                if not listing_url.startswith("http"):
                    listing_url = "https://vancouver.craigslist.org" + listing_url

                listings.append({
                    "source": "Craigslist",
                    "source_icon": "📋",
                    "title": title_raw[:80],
                    "year": year,
                    "price": price,
                    "km": "",
                    "location": location,
                    "seller": "Private / Dealer",
                    "url": listing_url,
                    "thumb": "",
                    "fetched_at": datetime.now().isoformat(),
                })

                if len(listings) >= max_listings:
                    break
            except Exception:
                continue

    except Exception as e:
        print(f"  Craigslist scrape error: {e}")

    return listings, url


# ─────────────────────────────────────────────────────────────────────────────
# Deep links — open in browser, no scraping
# ─────────────────────────────────────────────────────────────────────────────

def deep_links(vehicle, scope="bc"):
    make  = vehicle["make"]
    model = vehicle["model"]
    q_simple = quote_plus(f"{make} {model}")

    if scope == "national":
        cg_url = (f"https://www.cargurus.ca/Cars/l-Used-{make}-"
                  f"{model.replace(' ','-')}-d999")
        cg_name, cg_desc = "CarGurus (all Canada)", "Market analysis + deal ratings"
    else:
        cg_url = (f"https://www.cargurus.ca/Cars/l-Used-{make}-"
                  f"{model.replace(' ','-')}-British-Columbia-d999_L167132")
        cg_name, cg_desc = "CarGurus BC", "Market analysis + deal ratings"

    # Always offer a "broaden search" link unless we're already national.
    broaden_link = {
        "name": "AutoTrader (all Canada)",
        "icon": "🌐",
        "url": autotrader_url(vehicle, scope="national"),
        "description": "Broaden search to all of Canada"
    } if scope != "national" else None

    links = [
        {
            "name": "Kijiji Autos",
            "icon": "🏠",
            "url": f"https://www.kijijiautos.ca/cars/{vehicle['at_make']}/{vehicle['at_model']}/used/#od=ASC",
            "description": "Private + dealer listings, national"
        },
        {
            "name": cg_name,
            "icon": "🔍",
            "url": cg_url,
            "description": cg_desc
        },
        {
            "name": "Facebook Marketplace",
            "icon": "👥",
            "url": f"https://www.facebook.com/marketplace/108449209188687/vehicles/?query={q_simple}&exact=false",
            "description": "Private sellers, Vancouver area"
        },
    ]
    if broaden_link:
        links.append(broaden_link)
    return links


# ─────────────────────────────────────────────────────────────────────────────
# Main scrape function
# ─────────────────────────────────────────────────────────────────────────────

def fetch_listings(vehicle, scope="bc"):
    """
    Fetch and combine listings from all sources.
    Returns dict: {listings, deep_links, at_url, cr_url, fetched_at, scope}
    """
    print(f"  Fetching listings: {vehicle['short_name']} [{scope}]")

    at_listings, at_url = scrape_autotrader(vehicle, scope)
    time.sleep(0.5)
    cl_listings, cl_url = scrape_craigslist(vehicle)
    time.sleep(0.3)

    all_listings = at_listings + cl_listings

    # Dedup: primary on URL, fallback on (year, price, title-prefix) hash
    seen_urls   = set()
    seen_hashes = set()
    deduped = []
    for l in all_listings:
        url_key = l.get("url", "")
        hash_key = f"{l.get('year','')}|{l.get('price','')}|{l.get('title','')[:30]}"
        if url_key and url_key in seen_urls:
            continue
        if not url_key and hash_key in seen_hashes:
            continue
        seen_urls.add(url_key)
        seen_hashes.add(hash_key)
        deduped.append(l)
    all_listings = deduped

    # Sort by price ascending (put "Contact" at end)
    def price_sort_key(l):
        p = l["price"].replace("$", "").replace(",", "")
        try:
            return int(p)
        except ValueError:
            return 999999999

    all_listings.sort(key=price_sort_key)

    # Detect if both sources were blocked (likely sandbox/rate-limit)
    blocked_warning = (
        len(at_listings) == 0 and len(cl_listings) == 0
        and (len(all_listings) == 0)
    )

    return {
        "listings": all_listings,
        "deep_links": deep_links(vehicle, scope),
        "at_url": at_url,
        "cl_url": cl_url,
        "fetched_at": datetime.now().isoformat(),
        "scope": scope,
        "scope_label": SCOPES.get(scope, SCOPES["bc"])["label"],
        "count_at": len(at_listings),
        "count_cl": len(cl_listings),
        "blocked_warning": blocked_warning,
    }


if __name__ == "__main__":
    # Quick test
    with open("data/vehicles.json") as f:
        vehicles = json.load(f)

    v = vehicles[2]  # Sienna
    result = fetch_listings(v, scope="bc")
    print(f"\nResults for {v['short_name']}:")
    print(f"  AutoTrader: {result['count_at']} listings")
    print(f"  Craigslist: {result['count_cl']} listings")
    for l in result["listings"][:3]:
        print(f"  {l['source']} | {l['price']} | {l['year']} | {l['location']}")
