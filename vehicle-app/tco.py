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
