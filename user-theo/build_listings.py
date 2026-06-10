"""Build user-theo/manual_listings.json from the 2026-06-10 AutoTrader BC scan
of the cohort's BEVs. Real listings, filtered to BC (Kamloops-priority).
Model-level listings map to that model's vehicle id(s) (new + used share the
market). Re-run after a fresh scan with updated DATA below.
"""
import json
from pathlib import Path

FETCHED = "2026-06-10T12:00:00"
AT = "https://www.autotrader.ca/cars"
BC = "prv=British+Columbia&loc=BC&prx=-2&srt=9"
SEARCH = {
    "model-y":  f"{AT}/tesla/bc/?mdl=Model+Y&loc=Kamloops%2C+BC&prx=500&srt=9",
    "model-3":  f"{AT}/tesla/bc/?mdl=Model+3&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ioniq5":   f"{AT}/hyundai/bc/?mdl=IONIQ+5&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ev6":      f"{AT}/kia/bc/?mdl=EV6&loc=Kamloops%2C+BC&prx=500&srt=9",
    "ioniq6":   f"{AT}/hyundai/bc/?mdl=IONIQ+6&loc=Kamloops%2C+BC&prx=500&srt=9",
    "bolt":     f"{AT}/chevrolet/bc/?mdl=Bolt+EUV&loc=Kamloops%2C+BC&prx=500&srt=9",
    "id4":      f"{AT}/volkswagen/bc/?mdl=ID.4&loc=Kamloops%2C+BC&prx=500&srt=9",
    "rav4-h":   f"{AT}/toyota/bc/?{BC}&mdl=RAV4&yRng=2025%2C2026",
    "rav4-p":   f"{AT}/toyota/bc/?{BC}&mdl=RAV4+Prime",
    "prius":    f"{AT}/toyota/bc/?{BC}&mdl=Prius&yRng=2025%2C2026",
    "prius-p":  f"{AT}/toyota/bc/?{BC}&mdl=Prius&yRng=2025%2C2026",
    "corolla-h":f"{AT}/toyota/bc/?{BC}&mdl=Corolla&yRng=2025%2C2026",
    "crv-h":    f"{AT}/honda/bc/?{BC}&mdl=CR-V&yRng=2024%2C2026",
    "cx5":      f"{AT}/mazda/bc/?{BC}&mdl=CX-5&yRng=2025%2C2026",
    "niro":     f"{AT}/kia/bc/?mdl=Niro&loc=Kamloops%2C+BC&prx=500&srt=9",
    "tucson":   f"{AT}/hyundai/bc/?mdl=Tucson&loc=Kamloops%2C+BC&prx=500&srt=9",
    "outback":  f"{AT}/subaru/bc/?mdl=Outback&loc=Kamloops%2C+BC&prx=500&srt=9",
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
    # ── New-car dealer inventory (km 0 -> rendered "New") ──────────────────
    "rav4-h": [
        (2026, "RAV4 LE Hybrid AWD", 47348, 0, "Maple Ridge", "Maple Ridge Volkswagen"),
        (2026, "RAV4 XLE Hybrid AWD", 52587, 0, "Maple Ridge", "Maple Ridge Chrysler"),
        (2026, "RAV4 Woodland Hybrid AWD", 57995, 0, "Burnaby", "Destination Honda Burnaby"),
        (2026, "RAV4 XSE Technology Hybrid AWD", 61900, 0, "Prince George", "Private seller"),
    ],
    "prius": [
        (2026, "Prius Limited (hybrid)", 46440, 13, "Courtenay", "Comox Valley Toyota"),
    ],
    "prius-p": [
        (2026, "Prius Prime SE", 33860, 0, "Langley", "Langley Toyota"),
        (2026, "Prius Prime SE", 36686, 0, "Burnaby", "Destination Toyota"),
        (2026, "Prius Prime SE", 38143, 0, "Pitt Meadows", "West Coast Toyota"),
        (2026, "Prius Prime XSE", 40368, 0, "Pitt Meadows", "West Coast Toyota"),
        (2026, "Prius Prime XSE", 41645, 0, "Courtenay", "Comox Valley Toyota"),
        (2026, "Prius Prime XSE Premium", 46978, 0, "Pitt Meadows", "West Coast Toyota"),
    ],
    "corolla-h": [
        (2025, "Corolla Hybrid LE", 30999, 25389, "Surrey", "Go Langley Mitsubishi"),
        (2025, "Corolla Hybrid LE CVT AWD", 30999, 29011, "Surrey", "Dams Ford Lincoln"),
        (2025, "Corolla Hybrid LE (CPO)", 31930, 21500, "Langley", "Langley Toyota"),
        (2025, "Corolla Hybrid XSE AWD", 35990, 16424, "Abbotsford", "OpenRoad Toyota Abbotsford"),
        (2025, "Corolla Hybrid SE AWD", 35995, 14264, "Burnaby", "Destination Honda Burnaby"),
    ],
    "crv-h": [
        (2024, "CR-V Hybrid Touring AWD", 36995, 111842, "Vancouver", "Kingsway Honda"),
        (2024, "CR-V Hybrid EX-L AWD", 41895, 28087, "Vancouver", "Carter Honda"),
        (2024, "CR-V Hybrid Touring AWD", 42750, 49057, "North Vancouver", "North Shore Honda Acura"),
        (2025, "CR-V Hybrid EX-L AWD", 43339, 21858, "Prince George", "Northland CJD"),
        (2025, "CR-V Hybrid EX-L AWD", 43500, 48332, "North Vancouver", "North Shore Honda Acura"),
        (2026, "CR-V Hybrid Touring AWD", 52695, 270, "Vancouver", "Vancouver Honda"),
    ],
    "cx5": [
        (2025, "CX-5 GS Comfort AWD", 37395, 0, "Campbell River", "Island Owl Mazda"),
        (2026, "CX-5 GS AWD", 41795, 0, "Pitt Meadows", "West Coast Mazda"),
        (2026, "CX-5 GT AWD", 46695, 0, "Pitt Meadows", "West Coast Mazda"),
    ],
    "niro": [
        (2022, "Niro Plug-In Hybrid EX (~42 km EV)", 22812, 104971, "North Vancouver", "North Shore Kia"),
    ],
    "outback": [
        (2025, "Outback Limited XT", 47595, 19371, "Kamloops", "Kamloops Honda"),
        (2024, "Outback Onyx", 36166, 40203, "Surrey", "Go Langley Subaru"),
        (2024, "Outback Wilderness", 40998, 53290, "Burnaby", "Destination Toyota"),
        (2023, "Outback Touring", 35990, 55505, "Duncan", "Galaxy Motors Duncan"),
        (2023, "Outback Premier XT", 39995, 47914, "Burnaby", "Destination Honda Burnaby"),
        (2023, "Outback Convenience", 28995, 94486, "Vancouver", "Docksteader Subaru"),
        (2022, "Outback Touring", 30994, 59985, "North Vancouver", "Carter GM North Shore"),
        (2021, "Outback Premier XT", 32578, 102052, "Quesnel", "Regency Chrysler"),
    ],
    # Genuinely dry markets at scan (kept as explicit empty-with-note):
    "rav4-p": [],
    "tucson": [],
}
# model -> vehicle id(s). New + used of the same model share the market.
MAP = {
    "model-y":  ["tesla-model-y-used", "tesla-model-y-new"],
    "model-3":  ["tesla-model-3-used", "tesla-model-3-new"],
    "ioniq5":   ["ioniq5-new"],
    "ev6":      ["ev6-used"],
    "ioniq6":   ["ioniq6-new"],
    "bolt":     ["bolt-euv-used"],
    "id4":      ["id4-used"],
    "rav4-h":   ["rav4-hybrid-new"],
    "rav4-p":   ["rav4-prime-new"],
    "prius":    ["prius-new"],
    "prius-p":  ["prius-prime-new"],
    "corolla-h":["corolla-hybrid-new"],
    "crv-h":    ["crv-hybrid-new"],
    "cx5":      ["mazda-cx5-new"],
    "niro":     ["niro-phev-used"],
    "tucson":   ["tucson-phev-used"],
    "outback":  ["outback-used"],
}
# Explanatory notes for genuinely empty markets at scan.
EMPTY_NOTES = {
    "rav4-prime-new": "No Toyota RAV4 Prime (plug-in) in BC at scan 2026-06-10 — "
                      "AutoTrader returned 0 BC results; supply is very tight. "
                      "New RAV4 Hybrids are widely available as the closest in-market option.",
    "tucson-phev-used": "No Hyundai Tucson Plug-in Hybrid in the BC used market at scan "
                        "2026-06-10 — only gas and regular-hybrid Tucsons were listed.",
}

def listing(row, url):
    yr, title, price, km, city, dealer = row
    km_str = "New" if km == 0 else f"{km:,} km"
    return {"source": "AutoTrader", "source_icon": "🚗",
            "title": f"{yr} {title}", "year": yr, "price": f"${price:,}",
            "km": km_str, "location": f"{city}, BC", "seller": dealer,
            "url": url, "thumb": "", "fetched_at": FETCHED}

def main():
    out = {"_doc": "Manually curated listings (live AutoTrader BC scan 2026-06-10), "
                   "keyed by vehicle_id. Same shape as the live scrape; the app MERGES "
                   "manual + live. BEVs only so far — filtered to BC, Kamloops-priority."}
    for model, ids in MAP.items():
        rows = DATA[model]; url = SEARCH[model]
        listings = [listing(r, url) for r in rows]
        for vid in ids:
            if not listings:
                note = EMPTY_NOTES.get(vid, "No BC listings at scan 2026-06-10.")
            elif any(l["km"] == "New" for l in listings):
                note = (f"New-car dealer inventory in BC (AutoTrader scan 2026-06-10), "
                        f"{len(listings)} listings.")
            elif vid.endswith("-new"):
                note = (f"BC used market for this model (scan 2026-06-10), {len(listings)} "
                        "listings — the value reference vs buying new.")
            else:
                note = (f"BC used market (scan 2026-06-10), Kamloops-priority, "
                        f"{len(listings)} listings.")
            out[vid] = {"scope": "bc", "scope_label": "BC (Kamloops-priority)",
                        "fetched_at": FETCHED, "count_at": len(listings), "count_cl": 0,
                        "blocked_warning": False, "curated_note": note, "listings": listings}
    p = Path(__file__).parent / "manual_listings.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"wrote {p}: {len(out)-1} vehicle entries, "
          f"{sum(len(v['listings']) for k,v in out.items() if k!='_doc')} listing rows")

if __name__ == "__main__":
    main()
