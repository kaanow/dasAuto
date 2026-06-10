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
