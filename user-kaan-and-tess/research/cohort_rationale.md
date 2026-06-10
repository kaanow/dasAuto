# Cohort Rationale — kaan-and-tess

> Why this family's cohort looks the way it does. The methodology that
> applies to every family is in `docs/`; this file captures the
> kaan-and-tess-specific decisions.

## Hard filters applied (from `family.md`)

- **Seats ≥ 5** (family of 5)
- **In-market in BC** (used available in Lower Mainland at sensible price,
  or new from a Lower Mainland dealer in the target year)

That's it. Drivetrain (AWD vs FWD), ground clearance, hitch availability,
warranty length, FSR capability — all of these are real trade-offs but
they're handled by scored criteria, not filters. See
`docs/selection_principle.md` for the rule and the AWD-bug history.

## Cohort-shape goals (drive selection, not per-vehicle tests)

- **Span of powertrains.** ICE, hybrid, PHEV, and BEV all represented so
  the cost/utility/risk trade-offs are legible across the matrix.
- **Body-style diversity.** SUVs, minivans, and at least one efficient
  outlier (Tesla Model Y) so format-vs-format choices surface honestly.

These shaped the original 12-vehicle cohort and every expansion since.

## Weight tuning (vs `weights.json` defaults)

Defaults are tuned for this family's stated priorities:

| key            | weight | why                                                             |
|----------------|-------:|-----------------------------------------------------------------|
| `tco`          |    3.0 | Largest cash-flow driver over the horizon                       |
| `car_seat_fit` |    2.0 | Three car seats today; structural family-of-five constraint     |
| `reliability`  |    2.0 | 10-year hold rewards low-risk powertrains                       |
| `corridor`     |    1.5 | Vancouver↔Interior runs are routine (~12 trips/yr @ 400–500 km) |
| `winter`       |    1.3 | Coquihalla in winter; AWD + clearance important                 |
| `cargo`        |    1.0 | Family + gear; weighted but not dominant                        |
| `third_row`    |    1.0 | Kids fit anywhere; adults-in-3rd is a "nice to have"            |
| `hitch`        |    0.5 | Useful but not load-bearing on the decision                     |
| `fsr`          |    0.5 | Light off-pavement use only (per `family.md`)                   |

## Warranty-years-remaining seed values

For the BC 2026 market window, the cost-dominant warranty for each
candidate (at point of purchase):

- 2026 new Toyota Grand Highlander Hybrid / Sienna Hybrid: **10** (hybrid
  battery)
- 2023–24 used Grand Highlander Hybrid (bought 2026): **7**
- 2022–23 used Toyota Highlander/Sienna Hybrid: **7**
- 2022–23 used Chrysler Pacifica Hybrid: **7** (10yr battery − 3yr age)
- 2022–23 used Kia Sorento PHEV: **5** (8yr battery − 3yr age)
- 2024 used Kia EV9 / Mazda CX-90 PHEV: **6**
- 2023–24 used Tesla Model Y: **6**; 2026 new: **8**
- 2026 new Hyundai IONIQ 9: **8**
- 2022–23 used Subaru Ascent: **2** (5yr powertrain − 3yr age)
- 2022–23 used Hyundai Palisade / Kia Telluride / Honda Odyssey / Kia
  Carnival: **2**
- 2023–24 used Honda Pilot: **3**

These are the per-vehicle inputs to the maintenance-cliff model
(`docs/tco_methodology.md` § Maintenance).

## Final cohort scope (post-convergence)

After test drives and family discussion, the active set was narrowed to
**minivans only** (sliding doors + 7–8 seats + family ergonomics). All
non-minivan entries soft-archived but retained in `vehicles.json` so
prior research isn't lost. See `decisions_log.md` for the full timeline.
