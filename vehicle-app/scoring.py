"""
Scoring framework for the vehicle picker.

The framework defines the 9 criteria (TCO + 8 qualitative) and how they
combine into a weighted total. Per-family inputs — the weights, the
vehicles, the per-vehicle 1-5 scores — are loaded from the active data
directory; this module contains only the math.

The TCO criterion is special: it's a continuous score derived from the
post-NPV `tco_value` of every candidate in the cohort. The other eight
are read directly from each vehicle's `scores` block.
"""

CRITERIA_LABELS = {
    "tco":          "10yr Net TCO",
    "car_seat_fit": "Car Seat Fit",
    "cargo":        "Cargo Utility",
    "third_row":    "3rd Row Comfort",
    "corridor":     "Corridor Performance",
    "hitch":        "Hitch / Bike Rack",
    "reliability":  "Reliability",
    "winter":       "Winter Capability",
    "fsr":          "FSR Capability",
}

# Order matters when the UI displays criteria in groups.
CRITERIA_KEYS = list(CRITERIA_LABELS.keys())


def normalize_tco_score(tco_value, lo, hi):
    """Linear 1-5 score for a TCO value within a cohort range [lo, hi].
    Lowest TCO in the cohort scores 5, highest scores 1."""
    if hi == lo:
        return 5.0
    return round(1 + 4 * (hi - tco_value) / (hi - lo), 2)


def compute_score(vehicle, weights):
    """Weighted sum of the per-criterion scores for one vehicle.

    `vehicle["scores"]` is expected to hold a value for every key in
    `weights`. Missing keys score 0 (they contribute nothing)."""
    total = 0.0
    scores = vehicle.get("scores", {})
    for key, wt in weights.items():
        total += scores.get(key, 0) * wt
    return round(total, 2)


def rank_vehicles(vehicles, weights):
    """Return shallow-copied vehicle dicts with `computed_score` and
    `computed_rank` keys, sorted by score descending. Original list
    and dicts are not mutated."""
    scored = [{**v, "computed_score": compute_score(v, weights)} for v in vehicles]
    scored.sort(key=lambda x: x["computed_score"], reverse=True)
    for i, v in enumerate(scored, 1):
        v["computed_rank"] = i
    return scored


def reframe_for_horizon(vehicles, horizon):
    """Return shallow-copied vehicles with TCO fields re-derived at the
    given horizon. The `scores.tco` value for each vehicle is renormalized
    across the cohort's NEW TCO range so it remains 1..5.

    Requires `recompute_tco` from the tco module to do the per-vehicle
    re-derivation. Importing lazily here keeps the scoring module free of
    rate-specific knowledge."""
    from tco import recompute_tco
    refreshed = []
    for v in vehicles:
        new = dict(v)
        new["scores"] = dict(v["scores"])
        comp = recompute_tco(v, horizon)
        new["tco_value"]  = comp["tco_value"]
        new["fuel_10yr"]  = comp["fuel"]    # display field; named for legacy
        new["maint_10yr"] = comp["maint"]
        new["ins_10yr"]   = comp["ins"]
        new["resid_10yr"] = comp["resid"]
        refreshed.append(new)
    tcos = [v["tco_value"] for v in refreshed]
    lo, hi = min(tcos), max(tcos)
    for v in refreshed:
        v["tco_score"] = normalize_tco_score(v["tco_value"], lo, hi)
        v["scores"]["tco"] = v["tco_score"]
    return refreshed
