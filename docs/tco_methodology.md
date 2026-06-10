# TCO Methodology

> Family-agnostic. The math applies to every deployment. Family-specific
> rates (fuel prices, electricity, insurance baseline) live in each family's
> `research/tco_research.md`.

## What gets modelled

```
TCO(N) = on_road                            (the day-1 cost)
       + fuel(N)                            (NPV of fuel/energy spend)
       + maint(N)                           (warranty-tier-sensitive)
       + ins(N)                             (linear over horizon)
       − residual(N)                        (resale value at year N)
```

`N` is the user's chosen horizon (default 10 years, slider range 4–15).

## Variable-horizon recomputation

Each vehicle's stored fields are anchored at `BASE_HORIZON = 10`:

- `fuel_10yr`, `ins_10yr`, `resid_10yr` — values that sit on the year-10
  anchor and get rescaled to other horizons by the math below
- `pretax`, `on_road` — capital outlay at day 1 (horizon-independent)
- `warranty_years_remaining`, `maint_in_per_year`, `maint_oow_per_year` —
  vehicle-intrinsic inputs used by the per-year maintenance model

When the user picks a horizon other than 10, the route reframes each
vehicle's components live (see `scoring.reframe_for_horizon`).

### Fuel

```
fuel(N) = fuel_10yr × NPV_factor_fuel(N) / NPV_factor_fuel(10)
```

The NPV factor uses each fuel type's price escalation rate and the
discount rate (5.5% nominal default). For each powertrain type, a fixed
*consumption mix* preserves the analyst's per-vehicle assumption when
horizons or rates change:

| powertrain | mix                              |
|-----------|----------------------------------|
| ICE       | 100% gas                         |
| Hybrid    | 100% gas                         |
| PHEV      | 50% gas, 50% home electricity    |
| BEV       | 85% home electricity, 15% DCFC   |

### Maintenance (per-year, warranty-cliff-sensitive)

Each vehicle carries `maint_in_per_year` and `maint_oow_per_year`. The
horizon-N formula is a direct sum, no rescaling:

```
in_yrs  = min(N, warranty_years_remaining)
out_yrs = max(0, N − warranty_years_remaining)
maint(N) = in_yrs × maint_in_per_year + out_yrs × maint_oow_per_year
```

Per-year rates come from brand-level repair-tail ratios. See
`brand_repair_tail.md` for the table.

This replaced an earlier `maint_10yr + maint_oow_multiplier` schema (a
10-year aggregate input back-solved into per-year rates) which was hard to
source and validate. **Per-year rates are vehicle-intrinsic** — easier to
extend to multi-tier warranties later.

### Insurance

Linearly scaled by horizon (flat-rate methodology, no NPV escalation):

```
ins(N) = ins_10yr × N / 10
```

### Residual

Exponential interpolation between `pretax` (day-0 value) and `resid_10yr`
(year-10 future value):

```
residual(N) = pretax × (resid_10yr / pretax) ^ (N / 10)
```

Correctly front-loads depreciation.

## NPV defaults

Family-agnostic constants in `vehicle-app/tco.py`:

- `BASE_HORIZON = 10` — anchor for stored values
- `DISCOUNT = 0.055` — nominal annual

Family-specific fuel rates currently live in `_FUEL_RATES` in `tco.py`
(BC-specific). For a new family in a different region, override these per
family by reading from the family's `tco_research.md` JSON (TODO; currently
hardcoded for BC).

## Known model simplifications (deliberate caricatures)

These are intentional and documented; don't pre-fix them.

1. **Single cost-dominant warranty boundary per vehicle.** The model
   collapses bumper-to-bumper (3yr), powertrain (5yr), and battery (8–10yr)
   into one `warranty_years_remaining`. A multi-tier model would capture
   gentle ramps at 3yr/5yr that precede the big cliff at 10yr. Worth it
   only if a future family's situation is driven by mid-tier failures, not
   the battery tail.

2. **Cliff is a hard step, not a ramp.** Real maintenance ramps gradually.
   The step is a useful caricature because the warranty boundary is the
   *decision-relevant* signal.

3. **Residual doesn't model the warranty cliff.** Out-of-warranty cars
   depreciate faster, but `residual_at` decays smoothly between `pretax`
   and `resid_10yr`. The CBB projections used as `resid_10yr` already bake
   in typical 10yr-old post-warranty discount, so the bias only shows up
   at short horizons (N=5–8).

4. **Time anchoring.** `warranty_years_remaining` figures assume a
   purchase date matching the planning baseline. If the actual purchase
   slides 6 months, every figure should shrink by 0.5. Not parameterised.
