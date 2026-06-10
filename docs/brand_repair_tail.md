# Brand Repair-Tail Ratios

> The `maint_oow_per_year / maint_in_per_year` ratio, keyed by **make ×
> powertrain**. Used to derive each vehicle's out-of-warranty maintenance
> rate from its in-warranty rate. Family-agnostic — brand-level patterns
> from Consumer Reports and industry repair-cost data. The machine-readable
> table lives in `vehicle-app/repair_ratios.json`; keep the two in sync.

## The table

Ratio varies by powertrain *within* a make — a Toyota hybrid is not a
Toyota BEV. Key on both.

| make × powertrain        | ratio | rationale                                                                                       |
|--------------------------|------:|-------------------------------------------------------------------------------------------------|
| Toyota hybrid            |  2.0× | Best OOW tail — parts ubiquity, simple planetary hybrid, lowest major-failure rate in CR data   |
| Toyota BEV / PHEV / ICE  |  2.5× | Still strong, but without the hybrid drivetrain's exceptional simplicity                          |
| Honda / Mazda (any)      |  2.5× | Above-average reliability; deep parts networks                                                   |
| Subaru, Hyundai/Kia ICE & hybrid | 3.0× | Industry baseline                                                                       |
| Hyundai/Kia BEV & PHEV, Tesla    | 3.5× | 8yr battery bounds the worst tail, but post-warranty traction-battery replacement is the driver  |
| VW BEV (ID. Buzz)        |  4.0× | Below-average brand reliability; electronics repair tail                                          |
| Stellantis Pacifica PHEV |  4.0× | Documented OOW electrical / hybrid-software issues                                               |
| VW ICE (Atlas)           |  3.0× | Baseline ICE; the electronics tail bites harder on the BEV                                        |

## How it's applied (two layers)

1. **Default (the map).** When a vehicle in `vehicles.json` omits
   `maint_oow_per_year`, `tco.py` derives it as
   `maint_in_per_year × ratio(make, powertrain_type)` from
   `repair_ratios.json`. Unknown make → powertrain-level default; unknown
   powertrain → flat 3.0×.
2. **Override (per vehicle).** An explicit `maint_oow_per_year` on a
   vehicle **always wins**. This is where per-vehicle premiums live — the
   map gives the brand baseline; the override captures the specific car.

So: set `maint_in_per_year`, and only set `maint_oow_per_year` when the
vehicle deviates from its brand baseline (see Caveats).

Example — Toyota hybrid, in = $1,500: omit oow → derived $3,000 (2.0×).
Example — 2007 high-km CR-V: Honda baseline is 2.5×, but age+km push it to
3.0× → set `maint_oow_per_year` explicitly to override the map.

## Caveats

These ratios are *baseline brand averages*. Adjust per-vehicle when:

- A specific model has a known recurring expensive failure (e.g., 2007
  Honda Odyssey transmission)
- A specific model is unusually robust within an otherwise weak brand
- The vehicle is past 200,000 km — add a +$500 high-km premium regardless
  of brand
- The vehicle is past age 10 — add a +$300 age premium

These adjustments are encoded in `vehicle-app/app.py` `_sienna_maint()` for
the Sienna cross-shop and should be lifted to a general helper if other
nameplates need cross-shops.

## Sourcing

Source: Consumer Reports brand reliability rankings (10-year average),
J.D. Power Vehicle Dependability Study, and per-brand recall histories.
Not a defensible academic methodology — it's a working approximation. The
relative ordering is robust; the absolute multipliers carry uncertainty
of roughly ±0.5×.
