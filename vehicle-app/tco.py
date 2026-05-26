"""
NPV-based TCO computation.

Given base energy prices, annual escalation rates, and a discount rate,
returns the present-value cost of consuming 1 unit/yr over the horizon.
Used to translate a flat-rate per-vehicle `fuel_10yr` figure into the
NPV-equivalent under a new rate model, preserving the per-vehicle
consumption mix that the analyst originally assumed.

This module is rates-agnostic — the actual gas/hydro/DCFC numbers live
in the per-family data directory (e.g. `user-<family>/tco_research.md`
and any `tco_inputs.json` derived from it). This file just does the
arithmetic.
"""

from dataclasses import dataclass


@dataclass
class FuelRate:
    """One energy carrier's pricing assumption for a TCO model."""
    base: float          # CAD per unit (L or kWh) in year 0
    escalation: float    # annual nominal escalation, e.g. 0.035 for 3.5%/yr
    name: str = ""       # "gas", "hydro", "dcfc" — for diagnostics only


def npv_per_unit(rate: FuelRate, discount: float, years: int = 10) -> float:
    """Present value of consuming 1 unit/yr for `years` at `rate`,
    discounted at `discount` (nominal annual). Returns CAD per unit-year-of-flow."""
    r = (1 + rate.escalation) / (1 + discount)
    if r == 1:
        return rate.base * years
    return rate.base * (1 - r**years) / (1 - r)


# Per-powertrain consumption mix assumed by the original analyst when
# producing each vehicle's `fuel_10yr` bucket. We keep those mixes so a
# rate change adjusts dollar amounts without re-asserting consumption.
POWERTRAIN_MIXES = {
    "ice":    {"gas": 1.00},
    "hybrid": {"gas": 1.00},
    "phev":   {"gas": 0.50, "hydro": 0.50},
    "bev":    {"hydro": 0.85, "dcfc": 0.15},
}


def adjust_fuel_10yr(old_total, powertrain_type, old_mults, new_mults):
    """Re-scale an existing `fuel_10yr` total from one set of per-unit
    multipliers to another, holding the powertrain's consumption mix
    constant.

    `old_mults` / `new_mults` are dicts of {fuel: CAD per unit-year-of-flow}
    (the output of `npv_per_unit` for each fuel under the respective
    rate model). Returns the new dollar total, unrounded."""
    mix = POWERTRAIN_MIXES.get(powertrain_type, {"gas": 1.00})
    new_total = 0.0
    for fuel, share in mix.items():
        quantity = (old_total * share) / old_mults[fuel]
        new_total += quantity * new_mults[fuel]
    return new_total


# ---------------------------------------------------------------------------
# Variable-horizon recomputation
# ---------------------------------------------------------------------------
#
# Per-family rates that back the existing 10-year totals in vehicles.json.
# When the user shifts the horizon, we re-derive fuel/maint/ins/residual at
# the new N using these rates. The numbers here mirror what's documented in
# user-kaan-and-tess/tco_research.md and were applied when vehicles.json was
# rebuilt under the NPV methodology. If you fork for a new family with
# different rates, update tco_research.md and refresh these constants in
# parallel — they should not drift apart.

BASE_HORIZON   = 10           # the horizon at which fuel_10yr etc. are stored
DISCOUNT       = 0.055        # nominal annual

# Maintenance two-rate factors. The 1:3 ratio reflects the rough
# observation that out-of-warranty repair years cost ~3× in-warranty
# years (no covered failures, plus the failures cluster in the post-
# warranty tail). The absolute values are arbitrary — only the ratio
# matters because the stored `maint_10yr` is preserved at N=10 via the
# `now_units / base_units` rescaling in `recompute_tco`. Tightening or
# widening the cliff is a matter of tuning the ratio, not these
# constants.
MAINT_IN_WARRANTY_FACTOR  = 0.5
MAINT_OUT_OF_WARRANTY_FACTOR = 1.5

_FUEL_RATES = {
    "gas":   FuelRate(base=1.79,   escalation=0.035, name="gas"),
    "hydro": FuelRate(base=0.1172, escalation=0.045, name="hydro"),
    "dcfc":  FuelRate(base=0.40,   escalation=0.035, name="dcfc"),
}


def _powertrain_npv_scale(powertrain_type, years):
    """Mix-weighted ratio of NPV-per-CAD-of-fuel-spend at `years` vs at
    BASE_HORIZON. Multiplying fuel_10yr by this gives the NPV-adjusted
    fuel cost at the new horizon, holding the analyst's per-vehicle
    consumption mix constant.

    Concretely: each fuel's NPV factor (`$1 base × sum (1+e)^t / (1+d)^t`)
    grows with N; the *ratio* of factors at N vs 10 tells us how to
    rescale a 10-year bucket."""
    mix = POWERTRAIN_MIXES.get(powertrain_type, {"gas": 1.00})
    new_weighted = 0.0
    base_weighted = 0.0
    for fuel, share in mix.items():
        rate = _FUEL_RATES[fuel]
        new_weighted  += share * npv_per_unit(rate, DISCOUNT, years)
        base_weighted += share * npv_per_unit(rate, DISCOUNT, BASE_HORIZON)
    return new_weighted / base_weighted


def residual_at(pretax, resid_at_base, years, base_horizon=BASE_HORIZON):
    """Exponential interpolation of residual value between `pretax` at
    t=0 and `resid_at_base` at t=base_horizon. Smooth, monotonically
    decreasing, correctly front-loads depreciation.

    `pretax × (resid/pretax)^(years/base)`."""
    if pretax <= 0 or resid_at_base <= 0:
        # Fall back to linear if we can't anchor the exponential.
        return pretax + (resid_at_base - pretax) * (years / base_horizon)
    return pretax * (resid_at_base / pretax) ** (years / base_horizon)


def _maint_units(warranty_years_remaining, years):
    """Two-rate maintenance unit count: in-warranty years × IN_FACTOR +
    out-of-warranty years × OUT_FACTOR. The cliff falls at
    `warranty_years_remaining` years from purchase."""
    in_yrs  = min(years, warranty_years_remaining)
    out_yrs = max(0, years - warranty_years_remaining)
    return in_yrs * MAINT_IN_WARRANTY_FACTOR + out_yrs * MAINT_OUT_OF_WARRANTY_FACTOR


def recompute_tco(vehicle, horizon):
    """Re-derive every TCO component at the given horizon. Returns a
    dict of {fuel, maint, ins, resid, tco_value} in CAD. Does not
    mutate `vehicle`."""
    n = int(horizon)
    scale = _powertrain_npv_scale(vehicle["powertrain_type"], n)
    fuel  = vehicle["fuel_10yr"] * scale
    # Maintenance: two-rate model. The stored `maint_10yr` is preserved
    # when N == BASE_HORIZON because we rescale by (now_units / base_units),
    # not by a hard-coded constant. Vehicles missing the warranty field
    # default to BASE_HORIZON warranty remaining → no cliff (back-compat).
    warranty = vehicle.get("warranty_years_remaining", BASE_HORIZON)
    now_units  = _maint_units(warranty, n)
    base_units = _maint_units(warranty, BASE_HORIZON)
    maint = vehicle["maint_10yr"] * (now_units / base_units) if base_units > 0 else 0.0
    # Insurance: flat-rate, scale linearly.
    ins   = vehicle["ins_10yr"]   * n / BASE_HORIZON
    resid = residual_at(vehicle["pretax"], vehicle["resid_10yr"], n)
    tco_value = vehicle["on_road"] + fuel + maint + ins - resid
    return {
        "fuel":  round(fuel),
        "maint": round(maint),
        "ins":   round(ins),
        "resid": round(resid),
        "tco_value": round(tco_value),
    }
