# kaan-and-tess — Vehicle Situation

The family-specific inputs that drive what makes a "good" candidate for us.
This file is the seed for everything else in this directory.

## Household

- Two adults + three kids (car-seat era).
- Vancouver, BC. ICBC Territory D, class 003, CDF 0.528.
- 10-year ownership horizon: this is a long-hold decision.

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

The 12 candidates and their per-criterion scores live in `vehicles.json`
(this directory). Selection was based on:
- ≥7 seats or genuine 3-row capability
- AWD or 4WD available in Canada in the target years
- Available used in BC at sensible price or new from a Lower Mainland dealer
- Span of powertrains (ICE, hybrid, PHEV, BEV) so the cost/utility
  trade-offs are visible across the matrix

## TCO methodology

Detailed rate research, escalation curves, NPV discounting choice, and
data-quality caveats: `tco_research.md`.
