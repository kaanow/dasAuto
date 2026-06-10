# Brand Repair-Tail Ratios

> The `maint_oow_per_year / maint_in_per_year` ratio per brand. Used to
> derive each vehicle's out-of-warranty maintenance rate from its
> in-warranty rate. Family-agnostic — these are brand-level patterns from
> Consumer Reports and industry repair-cost data.

## The table

| ratio | brands                                              | rationale                                                                                                                                  |
|------:|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
|  2.0× | Toyota (all hybrids)                                | Best OOW repair tail — parts ubiquity, simplest planetary hybrid drivetrain, lowest major-failure rate in CR data                           |
|  2.5× | Honda, Mazda CX-90 PHEV                             | Above-average reliability; deep parts networks                                                                                             |
|  3.0× | Subaru, Hyundai/Kia ICE                             | Industry baseline                                                                                                                          |
|  3.5× | Korean BEV/PHEV (EV9, IONIQ 9, Sorento PHEV), Tesla | 8yr battery bounds the worst tail but post-warranty traction-battery replacement is the cost-tail driver; Tesla service network adds friction |
|  4.0× | Stellantis Pacifica Hybrid                          | Documented OOW electrical / hybrid-software issues; brand-wide complex-system reliability concerns                                          |
|  4.8× | VW (Atlas, ID. Buzz)                                | Below-average brand reliability; electronics repair tail                                                                                   |

## How to apply it

For each vehicle, set:

1. `maint_in_per_year` — what you'd pay per year while the cost-dominant
   warranty is active. Typical: $700 (Toyota hybrid), $1,400 (mid-size
   ICE), $1,600 (large ICE/SUV).
2. `maint_oow_per_year = maint_in_per_year × ratio_for_brand`

Example for a Toyota hybrid: in = $1,500, ratio = 2.0×, oow = $3,000.

Example for a VW Atlas: in = $1,600, ratio = 4.8×, oow = $7,700. The math
crushes Atlas's TCO in the cohort accurately.

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
