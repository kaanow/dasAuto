"""Build user-theo/manual_listings.json from the 2026-06-10 AutoTrader BC scan
of the cohort's BEVs. Real listings, filtered to BC (Kamloops-priority).
Model-level listings map to that model's vehicle id(s) (new + used share the
market). Re-run after a fresh scan with updated DATA below.
"""
import json
from pathlib import Path

FETCHED = "2026-06-10T12:00:00"
AT = "https://www.autotrader.ca/cars"
SEARCH = {
    "model-y": f"{AT}/tesla/bc/?mdl=Model+Y&loc=Kamloops%2C+BC&prx=500&srt=9",
    "model-3": f"{AT}/tesla/bc/?mdl=Model+3&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ioniq5":  f"{AT}/hyundai/bc/?mdl=IONIQ+5&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ev6":     f"{AT}/kia/bc/?mdl=EV6&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ioniq6":  f"{AT}/hyundai/bc/?mdl=IONIQ+6&loc=Kamloops%2C+BC&prx=500&srt=9",
    "bolt":    f"{AT}/chevrolet/bc/?mdl=Bolt+EUV&loc=Kamloops%2C+BC&prx=500&srt=9",
    "id4":     f"{AT}/volkswagen/bc/?mdl=ID.4&loc=Kamloops%2C+BC&prx=500&srt=9",
}
# model -> [(year, title, price, km, city, dealer), ...]
DATA = {
    "model-y": [
        (2024, "Model Y Long Range Dual Motor", 43997, 47425, "Surrey", "Go North Surrey GM"),
        (2022, "Model Y Performance AWD", 42995, 74383, "New Westminster", "Key West Ford"),
        (2021, "Model Y Long Range AWD", 38798, 51954, "Vancouver", "Go Downtown Kia"),
    ],
    "model-3": [
        (2024, "Model 3 Premium RWD", 41998, 37623, "Burnaby", "Destination Toyota"),
        (2023, "Model 3 RWD (local 1-owner)", 32995, 51130, "Richmond", "Volvo Cars Richmond"),
        (2023, "Model 3 RWD Leather/Navi/Glass roof", 33888, 41235, "Surrey", "Go Dodge Surrey"),
        (2022, "Model 3 Long Range AWD", 34990, 62159, "Coquitlam", "Infinite Ride Auto"),
        (2019, "Model 3 Standard Range RWD", 19888, 116016, "Burnaby", "Pioneer Motors Boundary"),
    ],
    "ioniq5": [
        (2023, "IONIQ 5 Preferred", 35818, 40182, "Duncan", "Duncan Hyundai"),
    ],
    "ev6": [
        (2024, "EV6 Land", 29999, 150967, "Coquitlam", "Go Kia West Coquitlam"),
        (2024, "EV6 Land AWD GT-Line Pkg 2", 45302, 47431, "Vancouver", "Burrard Acura"),
        (2025, "EV6 GT-Line AWD (low km)", 63495, 5143, "North Vancouver", "North Shore Kia"),
    ],
    "ioniq6": [
        (2024, "IONIQ 6 Ultimate RWD", 38991, 25891, "Surrey", "Murray Hyundai White Rock"),
        (2024, "IONIQ 6 Preferred AWD Long Range", 34188, 17848, "Abbotsford", "OpenRoad Toyota Abbotsford"),
        (2025, "IONIQ 6 Preferred AWD LR w/Ultimate", 41500, 5887, "Victoria", "Volvo Cars Victoria"),
        (2025, "IONIQ 6 Ultimate LR Sunroof (local trade)", 49999, 3796, "Coquitlam", "Go Kia West Coquitlam"),
    ],
    "bolt": [
        (2022, "Bolt EUV Premier", 26950, 28036, "Kamloops", "Dearborn Ford"),
        (2023, "Bolt EUV LT", 24998, 91654, "Kamloops", "River City Nissan"),
        (2023, "Bolt EUV LT", 29988, 39636, "Kamloops", "Bannister Chevrolet Cadillac"),
        (2022, "Bolt EUV", 21995, 44566, "Richmond", "Dueck Richmond"),
        (2023, "Bolt EUV Premier", 29940, 29690, "Victoria", "Wheaton Chevrolet"),
        (2023, "Bolt EUV", 26498, 26188, "Vancouver", "Dueck Downtown"),
        (2023, "Bolt EUV Premier", 30980, 35019, "Kelowna", "Kelowna Chevrolet"),
        (2022, "Bolt EUV Premier", 26488, 84367, "Coquitlam", "Eagle Ridge GM"),
    ],
    "id4": [
        (2024, "ID.4 Pro S RWD", 35995, 32000, "Langley", "Acura of Langley"),
        (2024, "ID.4 Pro S (Red)", 44780, 17378, "Abbotsford", "Abbotsford Volkswagen"),
        (2024, "ID.4 Pro", 49000, 5639, "Abbotsford", "Abbotsford Volkswagen"),
        (2025, "ID.4 Pro S AWD", 52995, 4318, "North Vancouver", "Capilano Volkswagen"),
        (2025, "ID.4 Pro S (low km)", 54115, 8095, "Chilliwack", "Chilliwack Volkswagen"),
    ],
}
# model -> vehicle id(s). New + used of the same model share the market.
MAP = {
    "model-y": ["tesla-model-y-used", "tesla-model-y-new"],
    "model-3": ["tesla-model-3-used", "tesla-model-3-new"],
    "ioniq5":  ["ioniq5-new"],
    "ev6":     ["ev6-used"],
    "ioniq6":  ["ioniq6-new"],
    "bolt":    ["bolt-euv-used"],
    "id4":     ["id4-used"],
}

def listing(row, url):
    yr, title, price, km, city, dealer = row
    return {"source": "AutoTrader", "source_icon": "🚗",
            "title": f"{yr} {title}", "year": yr, "price": f"${price:,}",
            "km": f"{km:,} km", "location": f"{city}, BC", "seller": dealer,
            "url": url, "thumb": "", "fetched_at": FETCHED}

def main():
    out = {"_doc": "Manually curated listings (live AutoTrader BC scan 2026-06-10), "
                   "keyed by vehicle_id. Same shape as the live scrape; the app MERGES "
                   "manual + live. BEVs only so far — filtered to BC, Kamloops-priority."}
    for model, ids in MAP.items():
        rows = DATA[model]; url = SEARCH[model]
        listings = [listing(r, url) for r in rows]
        for vid in ids:
            new = vid.endswith("-new")
            note = (f"Live AutoTrader BC scan 2026-06-10 for this model ({len(listings)} BC "
                    "listings, Kamloops-priority). " +
                    ("Shown as the used-market value reference vs buying new." if new
                     else "BC used market."))
            out[vid] = {"scope": "bc", "scope_label": "BC (Kamloops-priority)",
                        "fetched_at": FETCHED, "count_at": len(listings), "count_cl": 0,
                        "blocked_warning": False, "curated_note": note, "listings": listings}
    p = Path(__file__).parent / "manual_listings.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"wrote {p}: {len(out)-1} vehicle entries, "
          f"{sum(len(v['listings']) for k,v in out.items() if k!='_doc')} listing rows")

if __name__ == "__main__":
    main()
