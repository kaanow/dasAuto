"""One-shot builder for user-theo/vehicles.json.

Encodes the per-vehicle anchor formulas from research/tco_research.md so the
stored fuel_10yr / ins_10yr / resid_10yr / on_road are internally consistent.
Per-vehicle research inputs (price, consumption, scores, specs) are in COHORT.
Re-run to regenerate vehicles.json after editing the table.
"""
import json
from pathlib import Path

ANNUAL_KM = 15300
GAS = 1.62                      # Kamloops CAD/L
ELEC_BEV = 0.142                # blended home+DCFC CAD/kWh
ELEC_HOME = 0.125               # PHEV electric km
NPV_FUEL = 9.0                  # 10-yr NPV sum factor
PHEV_E_SHARE = 0.65             # share of PHEV km driven electric

def fuel_10yr(pt, cons):
    """cons: L/100km for ice/hybrid, kWh/100km for bev, (kWh/100, L/100) for phev."""
    k = ANNUAL_KM / 100
    if pt == "bev":
        annual = k * cons * ELEC_BEV
    elif pt == "phev":
        kwh, lp = cons
        annual = k * (PHEV_E_SHARE * kwh * ELEC_HOME + (1 - PHEV_E_SHARE) * lp * GAS)
    else:                       # ice, hybrid
        annual = k * cons * GAS
    return round(annual * NPV_FUEL, -2)

def ins_10yr(pretax):
    return round((1450 + 0.020 * pretax) * 10, -2)

def bc_tax_mult(pretax):
    gst = 0.05
    if pretax < 55000:   pst = 0.07
    elif pretax < 56000: pst = 0.08
    elif pretax < 57000: pst = 0.09
    elif pretax < 125000: pst = 0.10
    else: pst = 0.15
    return 1 + gst + pst

def on_road(pretax, fees=700):
    return int(round(pretax * bc_tax_mult(pretax) + fees, -1))

def resid_10yr(pretax, factor):
    return int(round(pretax * factor, -2))

# DC fast-charge per BEV: (minutes to add 200 km, peak DC rate kW) at the
# optimal BC fast charger. "Optimal" = a Tesla Supercharger for Teslas, or a
# 350 kW Electrify Canada / BC Hydro unit for the rest — the car draws up to
# its own peak. The 800V Hyundai/Kia (235 kW) and Teslas (250 kW) are quickest;
# the Bolt (55 kW) is the cohort's slow outlier; the ID.4 sits in between.
CHARGE_200KM = {
    "tesla-model-y-new":  (12, 250), "tesla-model-y-used": (13, 250),
    "tesla-model-3-new":  (12, 250), "tesla-model-3-used": (13, 250),
    "ioniq5-new": (11, 235), "ev6-used": (11, 235), "ioniq6-new": (10, 235),
    "bolt-euv-used": (38, 55), "id4-used": (25, 135),
}

# Per-vehicle research table. cons units per fuel_10yr(). scores: 8 qualitative
# (tco is computed at runtime). resid = 10-yr residual as fraction of pretax.
COHORT = [
  # ── BEV ───────────────────────────────────────────────────────────────
  dict(id="tesla-model-y-new", name="Tesla Model Y Long Range AWD", short="Model Y LR (new)",
       make="Tesla", model="Model Y", pt="bev", ptl="BEV (dual-motor AWD)", nu="New", yrs="2026",
       pretax=64990, cons=16.9, resid=0.38, warr=8, maint=550,
       scores=dict(car_seat_fit=5,cargo=5,third_row=1,corridor=4,hitch=4,reliability=4,winter=4,fsr=3),
       specs=dict(fuel_economy="16.9 kWh/100km",range_km="~500 km",clearance_mm=167,towing_lbs=3500,cargo_l=854,seats=5,third_row_legroom="none"),
       why="Best all-round BEV value for a cargo-focused family with home charging: a deep 854 L hold plus a sizable frunk, dual-motor AWD for Kamloops winters, and the cheapest charging network in Canada (Tesla Supercharger). Strong residual support over the hold.",
       tradeoffs="Build-quality variance and a firm ride. No CarPlay/Android Auto. The 800 km trip needs one fast-charge stop.",
       caution=None, at_make="tesla", at_model="model+y", at_years="2024,2026"),
  dict(id="tesla-model-y-used", name="Tesla Model Y AWD (2022-23)", short="Model Y (used)",
       make="Tesla", model="Model Y", pt="bev", ptl="BEV (dual-motor AWD)", nu="Used", yrs="2022-2023",
       pretax=44000, cons=16.9, resid=0.34, warr=6, maint=600,
       scores=dict(car_seat_fit=5,cargo=5,third_row=1,corridor=4,hitch=4,reliability=4,winter=4,fsr=3),
       specs=dict(fuel_economy="16.9 kWh/100km",range_km="~480 km",clearance_mm=167,towing_lbs=3500,cargo_l=854,seats=5,third_row_legroom="none"),
       why="The value sweet spot of the cohort: most of the new Model Y's utility — frunk, 854 L cargo, AWD, Supercharger access — at a steep depreciation discount, with battery/drive warranty still running.",
       tradeoffs="Out-of-warranty body/suspension repairs carry Tesla service friction. Battery degradation varies by prior charging habits.",
       caution=None, at_make="tesla", at_model="model+y", at_years="2022,2023"),
  dict(id="tesla-model-3-used", name="Tesla Model 3 Long Range (2022-23)", short="Model 3 (used)",
       make="Tesla", model="Model 3", pt="bev", ptl="BEV (RWD/AWD)", nu="Used", yrs="2022-2023",
       pretax=36000, cons=14.7, resid=0.32, warr=6, maint=550,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=4,hitch=1,reliability=4,winter=3,fsr=1),
       specs=dict(fuel_economy="14.7 kWh/100km",range_km="~510 km",clearance_mm=140,towing_lbs=0,cargo_l=561,seats=5,third_row_legroom="none"),
       why="The efficiency leader of the used BEVs — lowest kWh/100km means the lowest running cost in the cohort, plus a frunk and a trunk that swallow more than the sedan shape suggests. Excellent for the mostly-city duty cycle.",
       tradeoffs="Sedan cargo and low clearance limit it for gear-hauling and snow. RWD variants want winter tires for Kamloops.",
       caution=None, at_make="tesla", at_model="model+3", at_years="2022,2023"),
  dict(id="tesla-model-3-new", name="Tesla Model 3 Long Range AWD", short="Model 3 LR (new)",
       make="Tesla", model="Model 3", pt="bev", ptl="BEV (dual-motor AWD)", nu="New", yrs="2026",
       pretax=49990, cons=14.7, resid=0.34, warr=8, maint=550,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=4,hitch=1,reliability=4,winter=4,fsr=1),
       specs=dict(fuel_economy="14.7 kWh/100km",range_km="~520 km",clearance_mm=138,towing_lbs=0,cargo_l=594,seats=5,third_row_legroom="none"),
       why="The efficiency benchmark, brought new: the updated 'Highland' Model 3 is the lowest-consumption car in the cohort, so the cheapest to run on home charging, with a frunk, a deep trunk, dual-motor AWD for winter and Supercharger access. The most efficient way into a brand-new EV.",
       tradeoffs="Sedan cargo and low clearance work against the cargo priority and rough-road use. No CarPlay/Android Auto. The 800 km trip needs one fast-charge stop. Costs more than the very-similar used Model 3.",
       caution=None, at_make="tesla", at_model="model+3", at_years="2024,2026"),
  dict(id="ioniq5-new", name="Hyundai Ioniq 5 AWD", short="Ioniq 5 (new)",
       make="Hyundai", model="Ioniq 5", pt="bev", ptl="BEV (dual-motor AWD)", nu="New", yrs="2026",
       pretax=59800, cons=18.0, resid=0.30, warr=8, maint=550,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=3,hitch=3,reliability=4,winter=4,fsr=3),
       specs=dict(fuel_economy="18.0 kWh/100km",range_km="~410 km",clearance_mm=160,towing_lbs=2300,cargo_l=770,seats=5,third_row_legroom="none"),
       why="800V architecture gives the fastest 10-80% charging in the cohort (~18 min), easing the corridor and the 800 km trip. Flat floor, sliding console, 770 L cargo and a small frunk. AWD for winter.",
       tradeoffs="Higher consumption than the Teslas, so home-charging cost is a touch higher. Range trails the long-range Teslas. 5-yr battery degradation TBD.",
       caution=None, at_make="hyundai", at_model="ioniq+5", at_years="2025,2026"),
  dict(id="ev6-used", name="Kia EV6 AWD (2022-23)", short="EV6 (used)",
       make="Kia", model="EV6", pt="bev", ptl="BEV (dual-motor AWD)", nu="Used", yrs="2022-2023",
       pretax=42000, cons=17.8, resid=0.26, warr=6, maint=550,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=3,hitch=3,reliability=4,winter=4,fsr=2),
       specs=dict(fuel_economy="17.8 kWh/100km",range_km="~420 km",clearance_mm=160,towing_lbs=2300,cargo_l=520,seats=5,third_row_legroom="none"),
       why="EV6 shares the Ioniq 5's 800V fast-charging and AWD but in a sportier, lower body; a strong used-BEV value with warranty remaining.",
       tradeoffs="Tighter rear headroom and less cargo than the Ioniq 5. Firmer ride.",
       caution=None, at_make="kia", at_model="ev6", at_years="2022,2023"),
  dict(id="ioniq6-new", name="Hyundai Ioniq 6 Long Range RWD", short="Ioniq 6 (new)",
       make="Hyundai", model="Ioniq 6", pt="bev", ptl="BEV (RWD)", nu="New", yrs="2026",
       pretax=54000, cons=14.3, resid=0.28, warr=8, maint=520,
       scores=dict(car_seat_fit=4,cargo=2,third_row=1,corridor=5,hitch=1,reliability=4,winter=3,fsr=1),
       specs=dict(fuel_economy="14.3 kWh/100km",range_km="~580 km",clearance_mm=150,towing_lbs=0,cargo_l=401,seats=5,third_row_legroom="none"),
       why="Longest BEV range in the cohort (~580 km) and the lowest consumption — the best electric answer to the 800 km trip, doing it with a single short stop. 800V charging.",
       tradeoffs="Streamliner sedan: small 401 L trunk and tight rear headroom work against the cargo priority. RWD wants winter tires.",
       caution="Cargo is the weak point for a family that ranked cargo highly — included as the efficiency/range benchmark.",
       at_make="hyundai", at_model="ioniq+6", at_years="2025,2026"),
  dict(id="bolt-euv-used", name="Chevrolet Bolt EUV (2022-23)", short="Bolt EUV (used)",
       make="Chevrolet", model="Bolt EUV", pt="bev", ptl="BEV (FWD)", nu="Used", yrs="2022-2023",
       pretax=27500, cons=16.0, resid=0.22, warr=6, maint=500,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=2,hitch=1,reliability=3,winter=3,fsr=1),
       specs=dict(fuel_economy="16.0 kWh/100km",range_km="~400 km",clearance_mm=160,towing_lbs=0,cargo_l=462,seats=5,third_row_legroom="none"),
       why="The lowest purchase price and one of the lowest running costs in the cohort — the pure-value BEV. Battery packs were replaced under the recall, resetting that clock on many used examples.",
       tradeoffs="Slow 55 kW DCFC makes the 400-500 km corridor and 800 km trip painful (long stops). FWD, no frunk. GM discontinued the line.",
       caution="Confirm the recall battery replacement was completed on any specific used car.",
       at_make="chevrolet", at_model="bolt", at_years="2022,2023"),
  dict(id="id4-used", name="Volkswagen ID.4 AWD (2022-23)", short="ID.4 (used)",
       make="Volkswagen", model="ID.4", pt="bev", ptl="BEV (dual-motor AWD)", nu="Used", yrs="2022-2023",
       pretax=38000, cons=18.5, resid=0.20, warr=6, maint=650,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=3,hitch=2,reliability=2,winter=4,fsr=3),
       specs=dict(fuel_economy="18.5 kWh/100km",range_km="~400 km",clearance_mm=175,towing_lbs=2700,cargo_l=543,seats=5,third_row_legroom="none"),
       why="Roomy, conventional SUV packaging with AWD and good ground clearance for winter; cheap on the used market.",
       tradeoffs="VW's electronics/software repair tail is the worst in the cohort (4.0× OOW), early-software glitches common, and residual is weak — the depreciation is the warning and the opportunity.",
       caution="VW BEV repair tail (4.0×) and soft residual make the out-of-warranty years the risk.",
       at_make="volkswagen", at_model="id.4", at_years="2022,2023"),
  # ── PHEV ──────────────────────────────────────────────────────────────
  dict(id="rav4-prime-new", name="Toyota RAV4 Plug-in Hybrid AWD", short="RAV4 Prime (new)",
       make="Toyota", model="RAV4 Plug-in Hybrid", pt="phev", ptl="PHEV (dual-drive, AWD)", nu="New", yrs="2026",
       pretax=58000, cons=(20.0, 6.0), resid=0.40, warr=8, maint=750,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=5,hitch=4,reliability=5,winter=4,fsr=3),
       specs=dict(fuel_economy="~68 km EV + 6.0 L/100km",range_km="~68 km EV / ~900 km total",clearance_mm=203,towing_lbs=2500,cargo_l=975,seats=5,third_row_legroom="none"),
       why="The cohort's best of both worlds: ~68 km electric range covers the daily school/commute runs on home power, while the gas engine erases range anxiety on the 800 km trip. Dual-drive AWD, Toyota reliability and 10-yr/240k hybrid-battery warranty, and a big 975 L hold.",
       tradeoffs="Highest PHEV purchase price and supply is tight. Charges slowly on AC only (no useful DCFC).",
       caution=None, at_make="toyota", at_model="rav4+prime", at_years="2024,2026"),
  dict(id="prius-prime-new", name="Toyota Prius Prime", short="Prius Prime (new)",
       make="Toyota", model="Prius Prime", pt="phev", ptl="PHEV (dual-drive, FWD)", nu="New", yrs="2026",
       pretax=40000, cons=(16.0, 4.3), resid=0.36, warr=8, maint=700,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=5,hitch=1,reliability=5,winter=3,fsr=1),
       specs=dict(fuel_economy="~70 km EV + 4.3 L/100km",range_km="~70 km EV / ~1000 km total",clearance_mm=135,towing_lbs=0,cargo_l=569,seats=5,third_row_legroom="none"),
       why="Lowest-running-cost PHEV: ~70 km EV range plus the most efficient gas engine in the cohort when the battery is depleted. Toyota reliability, and the daily duty cycle is almost entirely electric on home charging.",
       tradeoffs="FWD only (no AWD offered) and low clearance hurt winter scoring. Sedan cargo and a small back seat.",
       caution=None, at_make="toyota", at_model="prius+prime", at_years="2024,2026"),
  dict(id="niro-phev-used", name="Kia Niro PHEV (2022-23)", short="Niro PHEV (used)",
       make="Kia", model="Niro PHEV", pt="phev", ptl="PHEV (series-parallel, FWD)", nu="Used", yrs="2022-2023",
       pretax=30000, cons=(15.0, 5.0), resid=0.28, warr=5, maint=800,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=4,hitch=1,reliability=4,winter=3,fsr=1),
       specs=dict(fuel_economy="~48 km EV + 5.0 L/100km",range_km="~48 km EV / ~900 km total",clearance_mm=155,towing_lbs=0,cargo_l=436,seats=5,third_row_legroom="none"),
       why="Affordable used PHEV with enough EV range (~48 km) to cover most city days on electricity and a frugal hybrid mode beyond it. Long Kia warranty still partly in force.",
       tradeoffs="FWD, modest cargo, and the smallest EV range of the PHEVs. Less engaging to drive.",
       caution=None, at_make="kia", at_model="niro", at_years="2022,2023"),
  dict(id="tucson-phev-used", name="Hyundai Tucson PHEV AWD (2022-23)", short="Tucson PHEV (used)",
       make="Hyundai", model="Tucson PHEV", pt="phev", ptl="PHEV (dual-drive, AWD)", nu="Used", yrs="2022-2023",
       pretax=39000, cons=(18.0, 6.5), resid=0.26, warr=5, maint=850,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=4,hitch=3,reliability=3,winter=4,fsr=3),
       specs=dict(fuel_economy="~53 km EV + 6.5 L/100km",range_km="~53 km EV / ~850 km total",clearance_mm=181,towing_lbs=2000,cargo_l=1095,seats=5,third_row_legroom="none"),
       why="Dual-drive AWD PHEV with the biggest cargo hold of the plug-ins (1095 L) and ~53 km EV range — a genuine cargo+winter+electric combination at a used price.",
       tradeoffs="Hyundai/Kia PHEV out-of-warranty battery tail (3.5×) and a shorter remaining warranty than the new Toyotas.",
       caution=None, at_make="hyundai", at_model="tucson", at_years="2022,2023"),
  # ── HEV ───────────────────────────────────────────────────────────────
  dict(id="rav4-hybrid-new", name="Toyota RAV4 Hybrid AWD", short="RAV4 Hybrid (new)",
       make="Toyota", model="RAV4 Hybrid", pt="hybrid", ptl="Hybrid (parallel, AWD)", nu="New", yrs="2026",
       pretax=47000, cons=6.0, resid=0.38, warr=10, maint=750,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=5,hitch=4,reliability=5,winter=4,fsr=3),
       specs=dict(fuel_economy="6.0 L/100km",range_km="~900 km tank",clearance_mm=203,towing_lbs=1750,cargo_l=1059,seats=5,third_row_legroom="none"),
       why="The no-compromise default: AWD, 1059 L cargo, 6.0 L/100km, Toyota's #1 reliability and 10-yr hybrid-battery warranty, and zero charging logistics for the corridor or the 800 km trip. The benchmark every other entry is measured against.",
       tradeoffs="No plug-in capability, so running cost is higher than the PHEVs/BEVs for the electric-heavy daily commute. Popular, so little discounting.",
       caution=None, at_make="toyota", at_model="rav4+hybrid", at_years="2025,2026"),
  dict(id="crv-hybrid-new", name="Honda CR-V Hybrid AWD", short="CR-V Hybrid (new)",
       make="Honda", model="CR-V Hybrid", pt="hybrid", ptl="Hybrid (series-parallel, AWD)", nu="New", yrs="2026",
       pretax=50000, cons=6.4, resid=0.34, warr=8, maint=800,
       scores=dict(car_seat_fit=5,cargo=5,third_row=1,corridor=5,hitch=3,reliability=4,winter=4,fsr=3),
       specs=dict(fuel_economy="6.4 L/100km",range_km="~850 km tank",clearance_mm=198,towing_lbs=1000,cargo_l=1113,seats=5,third_row_legroom="none"),
       why="Largest cargo hold among the compact hybrids (1113 L) with the most usable rear seat and a refined, quiet highway gait for the corridor. AWD, strong Honda reliability.",
       tradeoffs="Honda's hybrid battery warranty is 8 yr vs Toyota's 10, and the OOW tail is a notch behind Toyota. Slightly thirstier than the RAV4 Hybrid.",
       caution=None, at_make="honda", at_model="cr-v+hybrid", at_years="2025,2026"),
  dict(id="corolla-hybrid-new", name="Toyota Corolla Hybrid AWD", short="Corolla Hybrid (new)",
       make="Toyota", model="Corolla Hybrid", pt="hybrid", ptl="Hybrid (parallel, AWD-e)", nu="New", yrs="2026",
       pretax=33000, cons=4.6, resid=0.34, warr=10, maint=650,
       scores=dict(car_seat_fit=4,cargo=2,third_row=1,corridor=4,hitch=1,reliability=5,winter=3,fsr=1),
       specs=dict(fuel_economy="4.6 L/100km",range_km="~1050 km tank",clearance_mm=130,towing_lbs=0,cargo_l=371,seats=5,third_row_legroom="none"),
       why="The natural like-for-like upgrade from the current 2018 Corolla: same trusted footprint and reliability, now hybrid at 4.6 L/100km with optional AWD-e, at the lowest new-car price in the cohort. Lowest capital outlay with strong TCO.",
       tradeoffs="Small sedan trunk works against the cargo priority. Modest performance and a firmer ride than the SUVs.",
       caution=None, at_make="toyota", at_model="corolla+hybrid", at_years="2025,2026"),
  dict(id="prius-new", name="Toyota Prius AWD-e", short="Prius (new)",
       make="Toyota", model="Prius", pt="hybrid", ptl="Hybrid (parallel, AWD-e)", nu="New", yrs="2026",
       pretax=39000, cons=4.4, resid=0.34, warr=10, maint=680,
       scores=dict(car_seat_fit=4,cargo=3,third_row=1,corridor=5,hitch=1,reliability=5,winter=3,fsr=1),
       specs=dict(fuel_economy="4.4 L/100km",range_km="~1100 km tank",clearance_mm=140,towing_lbs=0,cargo_l=566,seats=5,third_row_legroom="none"),
       why="The most efficient non-plug-in in the cohort (4.4 L/100km) with available AWD-e and a now genuinely good-looking, refined package. Effortless 1000+ km tank range for the corridor and the 800 km trip.",
       tradeoffs="Hatch cargo is mid-pack and rear headroom is tight under the sloping roof. No plug-in option (see Prius Prime).",
       caution=None, at_make="toyota", at_model="prius", at_years="2025,2026"),
  # ── ICE ───────────────────────────────────────────────────────────────
  dict(id="mazda-cx5-new", name="Mazda CX-5 GS-L AWD", short="CX-5 (new)",
       make="Mazda", model="CX-5", pt="ice", ptl="ICE (AWD)", nu="New", yrs="2026",
       pretax=40000, cons=8.9, resid=0.30, warr=5, maint=950,
       scores=dict(car_seat_fit=5,cargo=4,third_row=1,corridor=4,hitch=3,reliability=4,winter=4,fsr=3),
       specs=dict(fuel_economy="8.9 L/100km",range_km="~650 km tank",clearance_mm=193,towing_lbs=2000,cargo_l=875,seats=5,third_row_legroom="none"),
       why="The driver's pick and the value ICE benchmark: standard AWD, a premium interior, and strong reliability at a price well under the electrified SUVs. No charging logistics at all.",
       tradeoffs="Gas-only, so the highest fuel cost of the SUVs given the daily mileage; the city-heavy duty cycle is exactly where it's least efficient. Short 5-yr powertrain warranty.",
       caution=None, at_make="mazda", at_model="cx-5", at_years="2025,2026"),
  dict(id="outback-used", name="Subaru Outback AWD (2022-23)", short="Outback (used)",
       make="Subaru", model="Outback", pt="ice", ptl="ICE (AWD)", nu="Used", yrs="2022-2023",
       pretax=36000, cons=8.7, resid=0.26, warr=2, maint=1000,
       scores=dict(car_seat_fit=5,cargo=5,third_row=1,corridor=4,hitch=4,reliability=4,winter=5,fsr=4),
       specs=dict(fuel_economy="8.7 L/100km",range_km="~800 km tank",clearance_mm=221,towing_lbs=2700,cargo_l=920,seats=5,third_row_legroom="none"),
       why="Best winter/all-road capability in the cohort: 221 mm clearance, symmetrical AWD, wagon cargo (920 L) and a hitch for bikes. Ideal for Interior winters and the Coquihalla corridor.",
       tradeoffs="Gas-only with the shortest remaining warranty (used, 2-yr powertrain left) and a higher maintenance tail than the Toyotas. CVT drone on grades.",
       caution=None, at_make="subaru", at_model="outback", at_years="2022,2023"),
  # ── Baseline ──────────────────────────────────────────────────────────
  dict(id="corolla-2018-current", name="2018 Toyota Corolla LE (current car)", short="2018 Corolla (current)",
       make="Toyota", model="Corolla", pt="ice", ptl="ICE (FWD)", nu="Used", yrs="2018",
       pretax=16500, cons=7.2, resid=0.18, warr=0, maint=900, oow=2000,
       scores=dict(car_seat_fit=4,cargo=2,third_row=1,corridor=3,hitch=1,reliability=5,winter=3,fsr=1),
       specs=dict(fuel_economy="7.2 L/100km",range_km="~700 km tank",clearance_mm=135,towing_lbs=0,cargo_l=371,seats=5,third_row_legroom="none"),
       why="The do-nothing baseline: keep the paid-off, reliable 2018 Corolla. on_road is its current resale value, so every other entry must justify its premium over simply keeping this car. Lowest capital cost by far.",
       tradeoffs="Small trunk against the cargo priority, FWD-only for winter, gas-only running cost, and out of factory warranty. The opportunity cost of keeping it is its ~$17k resale.",
       caution="Baseline only — the reference point, not an upgrade.",
       at_make="toyota", at_model="corolla", at_years="2018"),
]

def build():
    out = []
    for i, v in enumerate(COHORT, 1):
        pretax = v["pretax"]
        entry = {
            "id": v["id"], "rank": i, "name": v["name"], "short_name": v["short"],
            "make": v["make"], "model": v["model"], "powertrain": v["ptl"],
            "powertrain_type": v["pt"], "new_used": v["nu"], "years": v["yrs"],
            "weighted_score": 0.0, "tco_score": 3.0,
            "tco_value": 0,
            "on_road": on_road(pretax, fees=(0 if v["id"]=="corolla-2018-current" else 700)),
            "pretax": pretax,
            "fuel_10yr": fuel_10yr(v["pt"], v["cons"]),
            "ins_10yr": ins_10yr(pretax),
            "resid_10yr": resid_10yr(pretax, v["resid"]),
            "scores": {"tco": 3.0, **v["scores"]},
            "specs": v["specs"],
            "why": v["why"], "tradeoffs": v["tradeoffs"], "caution": v.get("caution"),
            "at_make": v["at_make"], "at_model": v["at_model"], "at_years": v["at_years"],
            "at_status": "",
            "cr_url": f"https://www.craigslist.org/search/cta?query={v['at_make']}+{v['model'].lower().replace(' ','+')}",
            "warranty_years_remaining": v["warr"],
            "maint_in_per_year": v["maint"],
            "active": True,
        }
        if "oow" in v:
            entry["maint_oow_per_year"] = v["oow"]
        if v["id"] in CHARGE_200KM:
            entry["charge_200km_min"], entry["charge_kw"] = CHARGE_200KM[v["id"]]
        # baseline keep-car: on_road IS the resale (opportunity cost), no tax
        if v["id"] == "corolla-2018-current":
            entry["on_road"] = 17000
        out.append(entry)
    return out

if __name__ == "__main__":
    data = build()
    path = Path(__file__).parent / "vehicles.json"
    path.write_text(json.dumps(data, indent=2))
    print(f"wrote {len(data)} vehicles to {path}")
