"""Build user-theo/manual_listings.json from the 2026-06-10 AutoTrader BC scan.
Keyed by vehicle_id so NEW entries get new dealer inventory and USED entries
get the used market (new+used no longer share a pool). km 0 renders as "New".
Re-run after a fresh scan with updated ENTRIES below.
"""
import json
from pathlib import Path

FETCHED = "2026-06-10T12:00:00"
AT = "https://www.autotrader.ca/cars"
BC = "prv=British+Columbia&loc=BC&prx=-2&srt=9"
def used_url(make, mdl):  return f"{AT}/{make}/bc/?mdl={mdl}&loc=Kamloops%2C+BC&prx=500&srt=9"
def new_url(make, mdl):   return f"{AT}/{make}/bc/?{BC}&mdl={mdl}&yRng=2025%2C2026"

# vehicle_id -> {search, note, rows[(year,title,price,km,city,dealer)]}
# km == 0 -> rendered "New". Empty rows -> note explains why.
ENTRIES = {
  # ── Tesla: sold direct — show current Tesla Canada MSRP by trim ──────────
  "tesla-model-y-new": {"search": "https://www.tesla.com/en_ca/modely",
    "source": "Tesla.com", "icon": "⚡", "direct": True,
    "note": "Tesla sells new direct — current Tesla Canada MSRP (Tesla.com, June 2026), "
            "before tax/fees. Matched to the AWD trim that fits the brief; new Teslas "
            "aren't on AutoTrader. See the used Model Y entry for the resale market.",
    "rows": [
      (2026, "Model Y Premium AWD (Long Range) — 542 km", 64990, 0, "Tesla.com — direct order", "Tesla Canada")]},
  "tesla-model-y-used": {"search": used_url("tesla","Model+Y"), "note": None, "rows": [
      (2024, "Model Y Long Range Dual Motor", 43997, 47425, "Surrey", "Go North Surrey GM"),
      (2022, "Model Y Performance AWD", 42995, 74383, "New Westminster", "Key West Ford"),
      (2021, "Model Y Long Range AWD", 38798, 51954, "Vancouver", "Go Downtown Kia")]},
  "tesla-model-3-new": {"search": "https://www.tesla.com/en_ca/model3",
    "source": "Tesla.com", "icon": "⚡", "direct": True,
    "note": "Tesla sells new direct — current Tesla Canada MSRP (Tesla.com, June 2026), "
            "before tax/fees. Matched to the AWD trim that fits the brief. Tesla is not on "
            "the federal EVAP rebate list. See the used Model 3 entry for the resale market.",
    "rows": [
      (2026, "Model 3 Premium AWD (Long Range) — 572 km", 49990, 0, "Tesla.com — direct order", "Tesla Canada")]},
  "tesla-model-3-used": {"search": used_url("tesla","Model+3"), "note": None, "rows": [
      (2024, "Model 3 Premium RWD", 41998, 37623, "Burnaby", "Destination Toyota"),
      (2023, "Model 3 RWD (local 1-owner)", 32995, 51130, "Richmond", "Volvo Cars Richmond"),
      (2023, "Model 3 RWD Leather/Navi/Glass roof", 33888, 41235, "Surrey", "Go Dodge Surrey"),
      (2022, "Model 3 Long Range AWD", 34990, 62159, "Coquitlam", "Infinite Ride Auto"),
      (2019, "Model 3 Standard Range RWD", 19888, 116016, "Burnaby", "Pioneer Motors Boundary")]},
  # ── Hyundai/Kia/VW BEVs ─────────────────────────────────────────────────
  "ioniq5-new": {"search": new_url("hyundai","IONIQ+5"),
    "note": "New 2026 dealer inventory — four units right in Kamloops (Bannister Hyundai).",
    "rows": [
      (2026, "IONIQ 5 Preferred", 60649, 0, "Kamloops", "Bannister Hyundai Kamloops"),
      (2026, "IONIQ 5 Preferred", 60899, 16, "Kamloops", "Bannister Hyundai Kamloops"),
      (2026, "IONIQ 5 Preferred", 62149, 17, "Kamloops", "Bannister Hyundai Kamloops"),
      (2026, "IONIQ 5 Preferred AWD Long Range", 59799, 0, "Surrey", "Murray Hyundai White Rock"),
      (2026, "IONIQ 5 Preferred AWD LR w/Ultimate", 65799, 0, "Surrey", "Murray Hyundai White Rock"),
      (2026, "IONIQ 5 Preferred", 59799, 15, "Surrey", "Murray Hyundai White Rock")]},
  "ioniq6-new": {"search": new_url("hyundai","IONIQ+6"),
    "note": "Limited new IONIQ 6 stock in BC at scan — newest low-km 2025 examples shown.",
    "rows": [
      (2025, "IONIQ 6 Ultimate LR Sunroof (local trade)", 49999, 3796, "Coquitlam", "Go Kia West Coquitlam"),
      (2025, "IONIQ 6 Preferred AWD LR w/Ultimate", 41500, 5887, "Victoria", "Volvo Cars Victoria")]},
  "ev6-used": {"search": used_url("kia","EV6"), "note": None, "rows": [
      (2024, "EV6 Land", 29999, 150967, "Coquitlam", "Go Kia West Coquitlam"),
      (2024, "EV6 Land AWD GT-Line Pkg 2", 45302, 47431, "Vancouver", "Burrard Acura"),
      (2025, "EV6 GT-Line AWD (low km)", 63495, 5143, "North Vancouver", "North Shore Kia")]},
  "bolt-euv-used": {"search": used_url("chevrolet","Bolt+EUV"), "note": None, "rows": [
      (2022, "Bolt EUV Premier", 26950, 28036, "Kamloops", "Dearborn Ford"),
      (2023, "Bolt EUV LT", 24998, 91654, "Kamloops", "River City Nissan"),
      (2023, "Bolt EUV LT", 29988, 39636, "Kamloops", "Bannister Chevrolet Cadillac"),
      (2022, "Bolt EUV", 21995, 44566, "Richmond", "Dueck Richmond"),
      (2023, "Bolt EUV Premier", 29940, 29690, "Victoria", "Wheaton Chevrolet"),
      (2023, "Bolt EUV", 26498, 26188, "Vancouver", "Dueck Downtown"),
      (2023, "Bolt EUV Premier", 30980, 35019, "Kelowna", "Kelowna Chevrolet"),
      (2022, "Bolt EUV Premier", 26488, 84367, "Coquitlam", "Eagle Ridge GM")]},
  "id4-used": {"search": used_url("volkswagen","ID.4"), "note": None, "rows": [
      (2024, "ID.4 Pro S RWD", 35995, 32000, "Langley", "Acura of Langley"),
      (2024, "ID.4 Pro S (Red)", 44780, 17378, "Abbotsford", "Abbotsford Volkswagen"),
      (2024, "ID.4 Pro", 49000, 5639, "Abbotsford", "Abbotsford Volkswagen"),
      (2025, "ID.4 Pro S AWD", 52995, 4318, "North Vancouver", "Capilano Volkswagen"),
      (2025, "ID.4 Pro S (low km)", 54115, 8095, "Chilliwack", "Chilliwack Volkswagen")]},
  # ── Toyota / Honda / Mazda / Subaru / Kia ───────────────────────────────
  "rav4-hybrid-new": {"search": new_url("toyota","RAV4"),
    "note": "New 2026 dealer inventory.", "rows": [
      (2026, "RAV4 LE Hybrid AWD", 47348, 0, "Maple Ridge", "Maple Ridge Volkswagen"),
      (2026, "RAV4 XLE Hybrid AWD", 52587, 0, "Maple Ridge", "Maple Ridge Chrysler"),
      (2026, "RAV4 Woodland Hybrid AWD", 57995, 0, "Burnaby", "Destination Honda Burnaby"),
      (2026, "RAV4 XSE Technology Hybrid AWD", 61900, 0, "Prince George", "Private seller")]},
  "rav4-prime-new": {"search": f"{AT}/toyota/bc/?{BC}&mdl=RAV4+Prime", "rows": [],
    "note": "No Toyota RAV4 Prime (plug-in) in BC at scan 2026-06-10 — AutoTrader returned 0 "
            "BC results; supply is very tight. New RAV4 Hybrids are the closest in-market option."},
  "prius-new": {"search": new_url("toyota","Prius"),
    "note": "New 2026 dealer inventory (the hybrid Prius; most Prius stock in BC is the Prime PHEV).",
    "rows": [(2026, "Prius Limited (hybrid)", 46440, 0, "Courtenay", "Comox Valley Toyota")]},
  "prius-prime-new": {"search": new_url("toyota","Prius"),
    "note": "New 2026 dealer inventory.", "rows": [
      (2026, "Prius Prime SE", 33860, 0, "Langley", "Langley Toyota"),
      (2026, "Prius Prime SE", 36686, 0, "Burnaby", "Destination Toyota"),
      (2026, "Prius Prime SE", 38143, 0, "Pitt Meadows", "West Coast Toyota"),
      (2026, "Prius Prime XSE", 40368, 0, "Pitt Meadows", "West Coast Toyota"),
      (2026, "Prius Prime XSE", 41645, 0, "Courtenay", "Comox Valley Toyota"),
      (2026, "Prius Prime XSE Premium", 46978, 0, "Pitt Meadows", "West Coast Toyota")]},
  "corolla-hybrid-new": {"search": new_url("toyota","Corolla"),
    "note": "New 2026 dealer inventory (limited; recent used/CPO also listed).", "rows": [
      (2026, "Corolla Hybrid LE", 29882, 0, "Kelowna", "Kelowna Toyota"),
      (2026, "Corolla Hybrid SE AWD", 33678, 0, "Kelowna", "Kelowna Toyota"),
      (2025, "Corolla Hybrid XSE AWD (CPO)", 35990, 16424, "Abbotsford", "OpenRoad Toyota Abbotsford"),
      (2025, "Corolla Hybrid SE AWD (CPO)", 35995, 14264, "Burnaby", "Destination Honda Burnaby")]},
  "crv-hybrid-new": {"search": new_url("honda","CR-V"),
    "note": "New 2026 dealer inventory.", "rows": [
      (2026, "CR-V Hybrid TrailSport AWD", 49975, 0, "Burnaby", "Destination Honda Burnaby"),
      (2026, "CR-V Hybrid Sport AWD", 51425, 0, "Surrey", "White Rock Honda"),
      (2026, "CR-V Hybrid EX-L AWD", 50624, 0, "Vancouver", "Kingsway Honda"),
      (2026, "CR-V Hybrid Touring AWD", 53325, 0, "Burnaby", "Destination Honda Burnaby"),
      (2026, "CR-V Hybrid Touring AWD", 54296, 0, "Surrey", "Jonker Honda")]},
  "mazda-cx5-new": {"search": new_url("mazda","CX-5"),
    "note": "New 2025-2026 dealer inventory.", "rows": [
      (2025, "CX-5 GS Comfort AWD", 37395, 0, "Campbell River", "Island Owl Mazda"),
      (2026, "CX-5 GS AWD", 41795, 0, "Pitt Meadows", "West Coast Mazda"),
      (2026, "CX-5 GT AWD", 46695, 0, "Pitt Meadows", "West Coast Mazda")]},
  "niro-phev-used": {"search": used_url("kia","Niro"), "note": None, "rows": [
      (2022, "Niro Plug-In Hybrid EX (~42 km EV)", 22812, 104971, "North Vancouver", "North Shore Kia")]},
  "tucson-phev-used": {"search": used_url("hyundai","Tucson"), "rows": [],
    "note": "No Hyundai Tucson Plug-in Hybrid in the BC used market at scan 2026-06-10 — "
            "only gas and regular-hybrid Tucsons were listed."},
  "outback-used": {"search": used_url("subaru","Outback"), "note": None, "rows": [
      (2025, "Outback Limited XT", 47595, 19371, "Kamloops", "Kamloops Honda"),
      (2024, "Outback Onyx", 36166, 40203, "Surrey", "Go Langley Subaru"),
      (2024, "Outback Wilderness", 40998, 53290, "Burnaby", "Destination Toyota"),
      (2023, "Outback Touring", 35990, 55505, "Duncan", "Galaxy Motors Duncan"),
      (2023, "Outback Premier XT", 39995, 47914, "Burnaby", "Destination Honda Burnaby"),
      (2023, "Outback Convenience", 28995, 94486, "Vancouver", "Docksteader Subaru"),
      (2022, "Outback Touring", 30994, 59985, "North Vancouver", "Carter GM North Shore"),
      (2021, "Outback Premier XT", 32578, 102052, "Quesnel", "Regency Chrysler")]},
}

def listing(row, e):
    yr, title, price, km, city, dealer = row
    src = e.get("source", "AutoTrader")
    loc = city if e.get("direct") else f"{city}, BC"
    return {"source": src, "source_icon": e.get("icon", "🚗"), "title": f"{yr} {title}",
            "year": yr, "price": f"${price:,}", "km": "New" if km == 0 else f"{km:,} km",
            "location": loc, "seller": dealer, "url": e["search"], "thumb": "",
            "fetched_at": FETCHED}

def main():
    out = {"_doc": "Manually curated listings (AutoTrader BC scan 2026-06-10; Tesla shows "
                   "Tesla.com MSRP since it sells direct), keyed by vehicle_id. NEW entries "
                   "hold new dealer inventory; USED entries hold the used market. The app "
                   "MERGES manual + any live scrape. BC, Kamloops-priority."}
    for vid, e in ENTRIES.items():
        rows = e.get("rows", [])
        listings = [listing(r, e) for r in rows]
        note = e.get("note")
        if note is None:
            note = f"BC used market (scan 2026-06-10), Kamloops-priority, {len(listings)} listings."
        count_at = sum(1 for l in listings if l["source"] == "AutoTrader")
        out[vid] = {"scope": "bc", "scope_label": "BC (Kamloops-priority)", "fetched_at": FETCHED,
                    "count_at": count_at, "count_cl": 0, "blocked_warning": False,
                    "curated_note": note, "listings": listings}
    p = Path(__file__).parent / "manual_listings.json"
    p.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    nrows = sum(len(v["listings"]) for k, v in out.items() if k != "_doc")
    print(f"wrote {p}: {len(out)-1} entries, {nrows} listing rows")

if __name__ == "__main__":
    main()
