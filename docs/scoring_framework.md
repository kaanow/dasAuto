# Scoring Framework

> Family-agnostic. The criteria, formula, and 1–5 rubric apply to every
> deployment. Only the *weights* are family-specific (per `weights.json`).

## The 9 criteria

| key            | label                | what it measures                                                |
|----------------|----------------------|-----------------------------------------------------------------|
| `tco`          | Net TCO              | Continuous score (1–5) derived from the cohort's TCO range      |
| `car_seat_fit` | Car Seat Fit         | Room for the family's car seats across one row                  |
| `cargo`        | Cargo Utility        | Behind-3rd-row volume; full-fold-flat volume                    |
| `third_row`    | 3rd Row Comfort      | Adult-friendliness of the 3rd row (absent / kid-only / adult)   |
| `corridor`     | Corridor Performance | Highway range, refuel cadence, NVH on long trips                |
| `hitch`        | Hitch / Bike Rack    | Towing capacity + factory/aftermarket hitch availability        |
| `reliability`  | Reliability          | Consumer Reports + JD Power + recall history                    |
| `winter`       | Winter Capability    | AWD/4WD + ground clearance for snow/Coquihalla driving          |
| `fsr`          | FSR Capability       | Ground clearance + AWD/4WD for light off-pavement use           |

8 criteria are 1–5 qualitative scores set per-vehicle. 1 (`tco`) is a
continuous score derived from the cohort's net TCO range.

## How `tco` is computed

`tco` is special. It's recomputed at every horizon change and every cohort
edit:

```
tco_value(vehicle) = on_road + fuel(N) + maint(N) + ins(N) − residual(N)
                     where N is the user's chosen horizon
                     and the components are derived per the TCO methodology

cohort_range = [min(tco_values), max(tco_values)] across active vehicles
tco_score(vehicle) = 1 + 4 × (max − tco_value) / (max − min)
                     (lowest TCO = 5, highest = 1)
```

See `tco_methodology.md` for `fuel(N)` / `maint(N)` / `residual(N)`
derivations.

## The 1–5 rubric

| score | meaning                                                                 |
|------:|-------------------------------------------------------------------------|
|     5 | Class-leading on this criterion; a real strength                        |
|     4 | Above average; meets the family's standard with margin                  |
|     3 | Acceptable; in the middle of the field                                  |
|     2 | Below standard; a tolerable weakness if balanced by strengths elsewhere |
|     1 | Disqualifying without weighting compensation                            |

For the `tco` criterion, the 1–5 score is mechanical (cohort-normalised, no
judgment). For the other 8, the score is a calibrated judgment against the
1–5 rubric. **Document the judgment in `research/cohort_rationale.md`** so
future sessions don't second-guess silently.

### Scoring `corridor` for BEVs (calibration rule)

`corridor` blends three things — highway **range**, **recharge cadence**, and
**NVH** (noise/vibration/harshness). For a BEV, score the range+cadence half
against the family's **one-way winter corridor leg** (for the BC families,
Vancouver↔Kamloops, ~355 km over the Coquihalla), NOT a summer one-way rated
figure and NOT a round trip:

- Use **real winter range ≈ rated × ~0.65** (cold + cabin heat + the mountain
  climb cut 30–40% off rated).
- The trip is **one-way per day** (drive up, drive back another day), so
  round-trip range is not the test.
- **Charge speed matters as much as range**: a car that needs a top-up but
  fast-charges in a few minutes beats one that "just makes it" but crawls.

Resulting bands (NVH already favours BEVs, so it nudges the rest up):

| corridor | BEV profile |
|---:|---|
| 5 | Does the winter leg on one charge, or needs only a brief (~5–10 min) fast-charge splash. Long-range Tesla / 800 V Hyundai-Kia (Model Y, Model 3, IONIQ 6/9). |
| 4 | Makes it with one moderate (~15 min) stop on a fast (≥200 kW) charger. Mid-range 800 V (Ioniq 5, EV6, EV9). |
| 3 | Marginal winter range needing a real stop on a moderate (~135–200 kW) charger. ID.4, ID. Buzz. |
| 2 | Slow charging (≤100 kW) makes any required stop long — the killer. Bolt EUV (55 kW), bZ4X (100 kW). |

ICE/hybrids with 800–1,000 km range and 5-minute refuels remain the natural
corridor leaders; a BEV earns a 5 by matching that *effortlessness* via
single-charge range or quick fast-charging, not by scraping the distance.

## Weights

Weights are family-specific and live in `weights.json`:

```json
{
  "tco":          3.0,
  "car_seat_fit": 2.0,
  "reliability":  2.0,
  "corridor":     1.5,
  "winter":       1.3,
  "cargo":        1.0,
  "third_row":    1.0,
  "hitch":        0.5,
  "fsr":          0.5
}
```

The kaan-and-tess defaults are a reasonable starting point for a BC family
with kids. For a new family, *adjust each weight against an explicit
statement in `family.md`* and record the adjustment rationale in
`research/cohort_rationale.md`.

## Final weighted score

```
score(vehicle) = sum over k in criteria of  weights[k] × scores[vehicle][k]
```

Rendered in the UI rounded to 2 decimal places.

## What changes per family and what doesn't

| Part                       | Per-family | Architectural |
|----------------------------|-----------|---------------|
| The 9 criterion keys       |           | ✓             |
| The 1–5 rubric             |           | ✓             |
| The weighted-sum formula   |           | ✓             |
| The `tco` derivation       |           | ✓             |
| The weights                | ✓         |               |
| Per-vehicle scores         | ✓         |               |

If a deployment ever needs to add or remove a criterion, that's an
architectural change (touches `vehicle-app/scoring.py`), not a
family-specific one. Discuss before doing it.

## The criterion set is a fixed superset (multi-family decision)

The 9 keys (`tco`, `car_seat_fit`, `cargo`, `third_row`, `corridor`,
`hitch`, `reliability`, `winter`, `fsr`) are a **shared superset across all
families** — they are NOT re-chosen per family. Some keys are obviously
kaan-and-tess-flavoured (`corridor` = the Vancouver↔Interior runs; `fsr` =
forest-service-road use), but a family for whom they're irrelevant simply
**sets that weight to ~0 in their `weights.json`** rather than removing the
criterion.

Why a superset instead of per-family criteria:

- The formula, rubric, and `vehicle-app/scoring.py` stay identical for every
  family — one code path, no per-family branching.
- A zero weight makes a criterion invisible to the ranking without deleting
  the data, so it can be re-enabled later by editing one number.
- Adding a genuinely new dimension (a criterion no existing key approximates)
  is the only case that touches code — and per the row above, that's an
  architectural change to be discussed, not a quiet per-family edit.

So for Theo: keep all 9 keys; set `corridor`/`fsr` (and anything else that
doesn't apply) low or zero in his `weights.json`. Don't fork the criterion
list.
