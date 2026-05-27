# kaan-and-tess — Vehicle Situation

The family-specific inputs that drive what makes a "good" candidate for us.
This file is the seed for everything else in this directory.

## Household

- Two adults + three kids (car-seat era).
- Vancouver, BC. ICBC Territory D, class 003, CDF 0.528.
- Long-hold decision. Default planning horizon is **10 years** but the
  app exposes a slider (4–15) — see "Time horizon" below.

## Driving profile

- Mostly Metro Vancouver day-to-day; regular Vancouver↔Interior corridor
  trips (so range / refuel cadence and highway comfort matter).
- Garage with home charging access (Tier 1 BC Hydro residential).
- Occasional Forest Service Road (FSR) use — not hardcore overlanding,
  but enough that ground clearance / AWD capability scores.
- Winter capability matters (Coquihalla, snow tires assumed).
- Hitch + bike-rack compatibility is a nice-to-have, not a deal-breaker.

## Budget & financial framing

- TCO is weighted heaviest of any single criterion (3.0).
- 10-year net TCO modelled in present-value dollars (CAD), not nominal.
  Methodology: see `tco_research.md` — Apr 2026 BC base rates with
  escalation (gas 3.5%/yr, hydro 4.5%/yr blended, DCFC 3.5%/yr) and
  5.5% nominal discount.
- Residual value at year 10 is a Canadian Black Book projection;
  treated as a real credit against TCO but flagged as model risk for
  first-year vehicles.

## Time horizon

The 10-year default is our planning baseline but the right horizon is
not fixed — and it materially shifts which candidate wins. Three reasons
to test shorter horizons:

1. **Powertrain warranty exposure.** Toyota's 10yr/240k hybrid battery
   warranty is the structural moat for the three Toyota hybrids.
   A used 2023 example bought in 2026 has 7 years remaining. At an
   8-year ownership horizon you exit warranty one year before sale;
   at 10 years you exit three years before sale, and the year-9–10
   battery-failure tail risk is on you.
2. **Residual front-loading.** Depreciation is steepest early. At
   year 8 the credit-side of TCO is bigger as a share of purchase
   price; at year 12 it asymptotes near scrap value. Shorter horizons
   make expensive-to-buy vehicles look relatively better.
3. **PHEV / BEV traction-battery warranty** has a similar cliff
   (Kia/Hyundai 8yr/160k; Toyota 10yr/240k). At horizons under the
   warranty period, the battery risk is the manufacturer's, not yours.

The slider in the app sidebar re-ranks every vehicle live. URL is
preserved (`?horizon=N`), so a shared link captures the horizon under
which the ranking was generated.

### Warranty cliff in maintenance

Maintenance uses a two-rate model: in-warranty years cost less, out-
of-warranty years cost more. Each vehicle has
`warranty_years_remaining` — years of the *cost-dominant* powertrain
warranty left at point of purchase. Seed values:

- 2026 new Toyota Grand Highlander Hybrid / Sienna Hybrid: 10 (full
  hybrid battery)
- 2023–24 used Grand Highlander Hybrid (bought 2026): 7
- 2022–23 used Toyota Highlander/Sienna Hybrid (bought 2026): 7
- 2022–23 used Chrysler Pacifica Hybrid: 7 (10yr battery − 3yr age)
- 2022–23 used Kia Sorento PHEV: 5 (8yr battery − 3yr age)
- 2024 used Kia EV9 / Mazda CX-90 PHEV: 6
- 2023–24 used Tesla Model Y: 6; 2026 new: 8 (8yr traction battery)
- 2026 new Hyundai IONIQ 9: 8 (BEV traction battery)
- 2022–23 used Subaru Ascent: 2 (5yr powertrain − 3yr age)
- 2022–23 used Hyundai Palisade / Kia Telluride / Honda Odyssey /
  Kia Carnival: 2
- 2023–24 used Honda Pilot: 3

Each vehicle carries two per-year maintenance rate inputs:
- `maint_in_per_year` — CAD/yr while covered. Mostly scheduled work
  (oil/filters/brakes for ICE; minimal items for BEV).
- `maint_oow_per_year` — CAD/yr once the cost-dominant warranty has
  expired. Scheduled work + expected value of out-of-warranty
  repairs. Varies by brand repair-tail.

Typical ratios (oow/in) observed in this cohort:

| ratio | who | why |
|-------|-----|-----|
| 2.0× | Toyota (all hybrids) | Best OOW repair tail — parts ubiquity, simplest planetary hybrid drivetrain, lowest major-failure rate in Consumer Reports data |
| 2.5× | Honda, Mazda CX-90 PHEV | Above-average reliability; deep parts networks |
| 3.0× | Subaru, Hyundai/Kia ICE | Industry baseline |
| 3.5× | Korean BEV/PHEV (EV9, IONIQ 9, Sorento PHEV), Tesla Model Y | 8yr battery bounds the worst tail but post-warranty traction-battery replacement is the cost-tail driver; Tesla service network adds friction |
| 4.0× | Stellantis Pacifica Hybrid | Documented out-of-warranty electrical / hybrid-software issues; brand-wide complex-system reliability concerns |

Formula at horizon N — direct sum, no anchor, no rescaling:

  `in_yrs    = min(N, warranty_years_remaining)`
  `out_yrs   = max(0, N − warranty_years_remaining)`
  `maint(N)  = in_yrs × maint_in_per_year + out_yrs × maint_oow_per_year`

Effect (warranty=7yr, in=$1,400/yr, varying only the OOW rate):
- oow=$2,800 (Toyota):    N=7 $9,800 → N=10 $18,200 → N=15 $32,200
- oow=$4,200 (default):   N=7 $9,800 → N=10 $22,400 → N=15 $40,400
- oow=$5,600 (Pacifica):  N=7 $9,800 → N=10 $26,600 → N=15 $48,800

Pre-cliff years are identical across these (same in-rate). Post-
cliff years diverge linearly with the OOW rate. The brand repair-
tail advantage shows up exactly when the warranty expires — which
is the whole point.

## Scoring criteria & default weights

Nine criteria. TCO is continuous (1–5, derived from the 12-vehicle
TCO range). The other eight are 1–5 qualitative scores.

| key            | label                | default weight | rationale for weight                                            |
|----------------|----------------------|----------------|-----------------------------------------------------------------|
| `tco`          | 10yr Net TCO         | 3.0            | Largest cash-flow driver over the horizon                       |
| `car_seat_fit` | Car Seat Fit         | 2.0            | Three car seats today; structural family-of-five constraint     |
| `reliability`  | Reliability          | 2.0            | 10-year hold rewards low-risk powertrains                       |
| `corridor`     | Corridor Performance | 1.5            | Vancouver↔Interior runs are routine                             |
| `winter`       | Winter Capability    | 1.3            | Coquihalla in winter; AWD + clearance important                 |
| `cargo`        | Cargo Utility        | 1.0            | Family + gear; weighted but not dominant                        |
| `third_row`    | 3rd Row Comfort      | 1.0            | Kids fit anywhere; adults-in-3rd is a "nice to have"            |
| `hitch`        | Hitch / Bike Rack    | 0.5            | Useful but not load-bearing on the decision                     |
| `fsr`          | FSR Capability       | 0.5            | Light off-pavement use only                                     |

Default weights live in `weights.json` (this directory). They can be
re-tuned live in the app sidebar; the URL preserves customised weights
via `?w_<key>=<val>` so a shared link captures your reranked view.

## Vehicle shortlist

The 18 candidates and their per-criterion scores live in `vehicles.json`
(this directory).

### Selection principle

The cohort is the set of vehicles that are *structurally feasible* for
this family — anything beyond that is captured by the scored criteria,
not pre-filtered. Re-stating that principle plainly:

> A trait is a HARD filter only if it would make the vehicle structurally
> infeasible (the family does not fit in it at all). A trait that varies
> by degree is a SCORED criterion (it shapes the ranking) — never both,
> never one masquerading as the other.

We learned this the hard way: an earlier draft used "AWD or 4WD
available" as a hard filter, which silently excluded every minivan
format (Pacifica, Odyssey, Carnival are FWD only — only Sienna offers
AWD) and biased the cohort toward SUVs. But the framework already has
`winter` (Coquihalla / snow-tires) and `fsr` (light off-pavement) as
scored 1–5 criteria — adding AWD as a hard filter on top double-counts
drivetrain and arbitrarily kills valid candidates. Same shape of error
nearly excluded the Tesla Model Y (5-seat from 2023+) under a 7-seat
hard filter, even though a family of five *does* fit (with zero
overflow).

### Hard filters (this household)

- **Seats ≥ household size.** Five people in this family → vehicle must
  seat ≥5. Extra seats are scored via `car_seat_fit` (room for the
  three car seats across one row) and `third_row` (whether the bench
  is adult-friendly, kid-only, or absent). A 5-seater is structurally
  feasible but penalised on `car_seat_fit` and `third_row`.
- **In-market.** Available used in BC at a sensible price, OR new from
  a Lower Mainland dealer in the target year. Vehicles that can't
  actually be bought here within the planning window are excluded.

### Cohort-shape goals (not per-vehicle filters)

- **Span of powertrains.** ICE, hybrid, PHEV, and BEV should all be
  represented so cost/utility/risk trade-offs are legible across the
  matrix. This drives candidate selection but isn't a per-vehicle
  test.
- **Body-style diversity.** SUVs, minivans, and at least one efficient
  outlier (Tesla Model Y) so format-vs-format choices surface honestly.

### Scored, not filtered

Drivetrain (AWD/FWD), ground clearance, hitch availability, factory
warranty length — all of these are real trade-offs but they're handled
by the 1–5 scoring criteria (`winter`, `fsr`, `hitch`, `reliability`)
and the warranty-cliff TCO model. They don't pre-exclude candidates.

## TCO methodology

Detailed rate research, escalation curves, NPV discounting choice, and
data-quality caveats: `tco_research.md`.
