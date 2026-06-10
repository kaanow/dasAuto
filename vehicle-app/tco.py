"""
NPV-based TCO computation.

Given base energy prices, annual escalation rates, and a discount rate,
returns the present-value cost of consuming 1 unit/yr over a chosen
horizon. The base-horizon fuel/insurance/residual figures stored on each
vehicle are anchored at BASE_HORIZON years; `recompute_tco` rescales them
to any horizon in [HORIZON_MIN, HORIZON_MAX].

This module is rates-agnostic — the actual gas/hydro/DCFC numbers live
in the per-family data directory (e.g. `user-<family>/tco_research.md`).
This file just does the arithmetic.
"""

import json
from dataclasses import dataclass
from pathlib import Path


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


# Per-powertrain consumption mix assumed when producing each vehicle's
# base-horizon fuel bucket. Held constant when the user shifts horizons
# so a horizon change adjusts NPV-weighted dollars without re-asserting
# consumption.
POWERTRAIN_MIXES = {
    "ice":    {"gas": 1.00},
    "hybrid": {"gas": 1.00},
    "phev":   {"gas": 0.50, "hydro": 0.50},
    "bev":    {"hydro": 0.85, "dcfc": 0.15},
}


# ---------------------------------------------------------------------------
# Variable-horizon recomputation
# ---------------------------------------------------------------------------
#
# Per-family rates that back the base-horizon totals stored in vehicles.json
# (the `fuel_10yr` / `ins_10yr` / `resid_10yr` fields — named for the
# anchor year, not the user's chosen horizon). When the user shifts the
# horizon, we re-derive fuel/maint/ins/residual at the new N using these
# rates. The numbers here mirror user-<family>/tco_research.md and were
# applied when vehicles.json was rebuilt under the NPV methodology. If
# you fork for a new family with different rates, update tco_research.md
# and refresh these constants in parallel — they should not drift apart.

BASE_HORIZON   = 10           # the anchor year of the stored base totals
DISCOUNT       = 0.055        # nominal annual

# Maintenance per-year rates. Each vehicle carries two per-year cost
# inputs (CAD):
#   `maint_in_per_year`  — scheduled maintenance while covered by the
#                          cost-dominant warranty (oil/filters/brakes
#                          for ICE; minimal items for BEV; small for
#                          Toyota hybrid)
#   `maint_oow_per_year` — per-year cost once the cost-dominant
#                          warranty has expired. Includes the expected
#                          value of out-of-warranty repairs +
#                          scheduled work; varies by brand repair-tail.
#
# Per-year rates are vehicle-intrinsic (not horizon-dependent), so
# horizon math is a direct sum, not a rescaling. Multi-tier warranty
# extends naturally by adding more rates.
#
# Defaults are conservative — used only when a vehicle's data is
# incomplete. Real vehicles should specify both fields explicitly.
MAINT_IN_PER_YEAR_DEFAULT  = 1500
MAINT_OOW_PER_YEAR_DEFAULT = 4500   # 3× the in-warranty rate (industry baseline)

# Brand × powertrain repair-tail ratios. Loaded once. Used ONLY to derive
# maint_oow_per_year when a vehicle omits it — an explicit field always
# wins (that's where per-vehicle age/km premiums live). See
# docs/brand_repair_tail.md and repair_ratios.json.
_RATIOS_PATH = Path(__file__).resolve().parent / "repair_ratios.json"
try:
    _REPAIR_RATIOS = json.loads(_RATIOS_PATH.read_text())
except (OSError, ValueError):
    _REPAIR_RATIOS = {"by_make_powertrain": {}, "by_powertrain_default": {}, "fallback": 3.0}


def repair_ratio(make, powertrain_type):
    """Default OOW multiplier for a make+powertrain. Falls back to a
    powertrain-level default, then a flat constant. Only consulted when a
    vehicle has no explicit maint_oow_per_year."""
    by_mp = _REPAIR_RATIOS.get("by_make_powertrain", {})
    make_map = by_mp.get(make, {})
    if powertrain_type in make_map:
        return make_map[powertrain_type]
    pt_default = _REPAIR_RATIOS.get("by_powertrain_default", {})
    if powertrain_type in pt_default:
        return pt_default[powertrain_type]
    return _REPAIR_RATIOS.get("fallback", 3.0)

_FUEL_RATES = {
    "gas":   FuelRate(base=1.79,   escalation=0.035, name="gas"),
    "hydro": FuelRate(base=0.1172, escalation=0.045, name="hydro"),
    "dcfc":  FuelRate(base=0.40,   escalation=0.035, name="dcfc"),
}


def _powertrain_npv_scale(powertrain_type, years):
    """Mix-weighted ratio of NPV-per-CAD-of-fuel-spend at `years` vs at
    BASE_HORIZON. Multiplying the base-horizon fuel total by this gives
    the NPV-adjusted fuel cost at the new horizon, holding the analyst's
    per-vehicle consumption mix constant.

    Concretely: each fuel's NPV factor (`$1 base × sum (1+e)^t / (1+d)^t`)
    grows with N; the *ratio* of factors at N vs BASE_HORIZON tells us
    how to rescale the stored bucket."""
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


def maint_at_horizon(vehicle, years):
    """Direct per-year computation. Returns CAD maintenance cost over
    `years` of ownership, using the vehicle's per-year in-warranty and
    out-of-warranty rates and its remaining warranty at point of
    purchase.

    `maint(N) = in_yrs × maint_in_per_year + out_yrs × maint_oow_per_year`

    where `in_yrs = min(N, warranty_years_remaining)`. No rescaling,
    no anchor — the rates ARE the model. Vehicles missing per-year
    fields fall back to the module defaults."""
    warranty = vehicle.get("warranty_years_remaining", BASE_HORIZON)
    p_in     = vehicle.get("maint_in_per_year",  MAINT_IN_PER_YEAR_DEFAULT)
    # Explicit oow wins (carries per-vehicle age/km premiums). Otherwise
    # derive from the brand×powertrain repair-tail ratio.
    if "maint_oow_per_year" in vehicle:
        p_oow = vehicle["maint_oow_per_year"]
    else:
        ratio = repair_ratio(vehicle.get("make"), vehicle.get("powertrain_type"))
        p_oow = p_in * ratio
    in_yrs   = min(years, warranty)
    out_yrs  = max(0, years - warranty)
    return in_yrs * p_in + out_yrs * p_oow


def recompute_tco(vehicle, horizon):
    """Re-derive every TCO component at the given horizon. Returns a
    dict of {fuel, maint, ins, resid, tco_value} in CAD. Does not
    mutate `vehicle`."""
    n = int(horizon)
    scale = _powertrain_npv_scale(vehicle["powertrain_type"], n)
    fuel  = vehicle["fuel_10yr"] * scale
    maint = maint_at_horizon(vehicle, n)
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
