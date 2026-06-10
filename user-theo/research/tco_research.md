# TCO Research — theo (Kamloops, BC)

> Family-specific cost rates and the per-vehicle anchor formulas used to
> populate `vehicles.json`. The escalation/discount *shape* lives in
> `vehicle-app/tco.py` and is BC-wide (shared with kaan-and-tess); only the
> absolute price levels and insurance below are Theo-specific. See
> `docs/tco_methodology.md` for how the app re-derives each component at any
> horizon.

## Region

Kamloops (BC Interior), with sourcing across the Okanagan and Lower
Mainland. Same province as kaan-and-tess, so BC Hydro electricity, the BCUC
DCFC network, and the 5.5% nominal discount rate (3.0% real + 2.5% CPI) are
unchanged. The two Theo-specific differences are **gasoline** (cheaper in
the Interior) and **insurance** (different ICBC territory + driver factor).

## Gasoline — Kamloops adjustment

- Kamloops pump price runs **~10% below Metro Vancouver** because there is no
  TransLink 18.5 ¢/L motor-fuel levy and Interior marketing margins are
  thinner. Vancouver base (kaan-and-tess) is 1.79 CAD/L; **Kamloops base used
  here: 1.62 CAD/L** (Apr 2026).
- Escalation: same BC mid-case **3.5%/yr nominal** as the Vancouver model
  (carbon-tax pause + crude outlook are province-level). No change to
  `tco.py`'s gas escalation.

## Electricity & DCFC — unchanged from BC reference

- Home charging blended **0.125 CAD/kWh** (BC Hydro Tier 1 11.72 ¢/kWh, some
  Tier 2 spillover for an EV household), escalation 4.5%/yr.
- Public DCFC **0.40 CAD/kWh** (BC Hydro network), escalation 3.5%/yr. Theo's
  corridor (Kamloops↔Vancouver / Okanagan) and the 1–2× annual 800 km trip
  add modest DCFC for BEVs; budget ~15% of BEV energy at DCFC, 85% home.

## Per-vehicle anchor formulas

These produce the stored base-horizon (10-yr) anchors in `vehicles.json`.
The app rescales them to any horizon; at N=10 the stored value is used as-is.

### `fuel_10yr`

```
annual_fuel = (annual_km / 100) × consumption × unit_price
fuel_10yr   = round(annual_fuel × 9.0, -2)      # 9.0 ≈ 10-yr NPV sum at
                                                #  ~3.5% escalation vs 5.5% discount
```
- `annual_km` = **15,300** (from `family.md`).
- ICE/HEV: consumption in L/100km × **1.62 CAD/L**.
- BEV: kWh/100km × blended **0.142 CAD/kWh** (0.85×0.125 home + 0.15×0.40 DCFC).
- PHEV: blend by utility factor — with home charging + mostly-city use, treat
  **~65% of km as electric** (home rate) and 35% as gas (1.62). Dual-drive vs
  series-electric noted per vehicle in `powertrain`.

### `ins_10yr` — Theo's ICBC Territory L, class 003, CDF 0.686

Anchored to Theo's **real quote: 2018 Corolla full coverage = $1,764/yr**
(basic + $5M 3PL + collision + comprehensive). Collision/comprehensive scale
with vehicle value:

```
ins_annual = 1450 + 0.020 × pretax        # pretax = pre-tax vehicle price (CAD)
ins_10yr   = round(ins_annual × 10, -2)
```
- Calibration check (Corolla, pretax ≈ $16,500): 1450 + 330 = **$1,780/yr** ≈
  the $1,764 quote. ✓
- Cross-check vs kaan-and-tess (CDF 0.528): Theo's factor is 0.686/0.528 =
  **1.30× kaan**. kaan's $65k Model Y = $2,150/yr; ×1.30 = $2,795. This model
  gives 1450 + 0.020×65000 = **$2,750/yr**. ✓ Consistent on both anchors.

### `resid_10yr` (base-horizon residual)

Exponential decay from `pretax` to the 10-yr residual; the app interpolates
intermediate horizons. Per-vehicle residual judged from segment depreciation:
- Strong-residual nameplates (Toyota hybrid/PHEV, Tesla): 30–40% of pretax.
- Average (Hyundai/Kia, Honda, Mazda, Subaru): 22–32%.
- Weak (VW, early-gen BEVs like Bolt with battery-age discount): 12–22%.
- Current 2018 Corolla baseline: `on_road` = current resale; 10-yr residual
  of a then-18-yr-old Corolla ≈ $3,000.

### `warranty_years_remaining`

The cost-dominant warranty at point of purchase (drives the maintenance
cliff). New BEV/PHEV traction battery = 8 yr; Toyota/Lexus hybrid battery =
10 yr; new ICE powertrain = 5 yr; used = remaining of those minus age. See
`docs/brand_repair_tail.md`.

### Maintenance

`maint_in_per_year` set per vehicle (BEV lowest ~$400–600; Toyota hybrid
~$700–900; ICE/PHEV ~$900–1,400). `maint_oow_per_year` left to the
brand×powertrain ratio map (`vehicle-app/repair_ratios.json`) unless a
specific car warrants an explicit age/km premium.

## EV / PHEV purchase rebates (researched 2026-06-10)

**Net effect on this cohort: ~$0.** Both programs that could apply exclude
essentially every entry. Captured here so it isn't re-litigated.

### BC provincial — CleanBC Go Electric

**Ended November 2025.** No provincial purchase rebate is available to BC
buyers in 2026. (Was up to $4,000 BEV / $2,000 lower-range PHEV, income-tested.)

### Federal — Electric Vehicle Affordability Program (EVAP)

Launched 2026-02-16; runs to 2031 or until funds run out (first-come basis).
- **Amounts (2026):** $5,000 BEV/FCEV · **$2,500 PHEV** (both decline yearly).
- **New only** — used purchases do not qualify.
- **Final-transaction-value cap $50,000** (base + options + fees, excl. tax/
  incentives). Canadian-built vehicles are exempt from the cap.
- **Country of manufacture:** must be built in Canada or an FTA partner. China
  is not an FTA partner, so Chinese-built EVs are excluded.
- **Curated list** (Transport Canada EVAP vehicle list) — a model qualifies
  only if explicitly listed. **Tesla is not on the list at all.**

### Applying the rules to Theo's cohort

| Reason excluded | Vehicles |
|---|---|
| Used (EVAP is new-only) | Model Y used, Model 3 used, EV6, Bolt EUV, ID.4, Niro PHEV, Tucson PHEV |
| Not a BEV/PHEV (conventional hybrid/ICE) | RAV4 Hybrid, CR-V Hybrid, Corolla Hybrid, Prius, CX-5 |
| New BEV over the $50k cap | Model Y AWD ($65k), Ioniq 5 AWD ($60k), Ioniq 6 ($54k), RAV4 Prime ($58k) |
| Tesla not on the EVAP list / China-built | Model 3 new |

**The one to watch: Prius Prime (new).** It's the only cohort entry that fits
the rules on paper — new PHEV, Japan-built (CPTPP FTA), trims ($34k–47k) under
the $50k cap → would be worth **$2,500**. But Toyota's presence on the EVAP
list is unconfirmed, so the rebate is **not** baked into its TCO. If a buyer
confirms the Prius Prime (or a new sub-$50k Niro PHEV) is EVAP-listed at
purchase, subtract $2,500 from its net cost. The only cohort *nameplate* on
the current list is the new 2027 Chevrolet Bolt ($5,000 BEV) — but Theo's Bolt
is used, so it doesn't apply.
