# Cohort Rationale — theo

> Why this family's cohort looks the way it does. Family-agnostic
> methodology is in `docs/`; this captures the theo-specific decisions.
> Inputs from `family.md`; numeric methodology in `research/tco_research.md`.

## Hard filters applied (from `family.md`)

- **Seats ≥ 5** (family of 4 — every 5-seater fits comfortably; this only
  excludes 2-seaters and the like).
- **In-market in BC** (new from a BC dealer in the target year, or used
  available in the Interior / Okanagan / Lower Mainland at sensible price).

That's it. **Drivetrain is NOT a filter.** The brief explicitly says "AWD or
FWD" — both acceptable — so AWD is handled by the scored `winter`/`fsr`
criteria, never as a hard filter. This is the kaan-and-tess AWD-minivan
lesson applied from the start (see `docs/selection_principle.md`). Cargo,
range, and charging are likewise scored, not filtered.

## Weight tuning (vs `weights.json` defaults / kaan-and-tess)

| key            | theo | kaan | why (quotes `family.md`)                                           |
|----------------|-----:|-----:|--------------------------------------------------------------------|
| `tco`          |  3.0 |  3.0 | "TCO is primary metric"; capital cost subordinate                  |
| `cargo`        |  2.0 |  1.0 | "Cargo space (trunk, folding seats; frunk a bonus)" — headline need |
| `corridor`     |  1.5 |  1.5 | 12 trips/yr of 400–500 km + occasional 800 km                      |
| `reliability`  |  1.5 |  2.0 | 10-yr hold rewards low-risk powertrains (but feeds TCO already)     |
| `winter`       |  1.3 |  1.3 | Kamloops / Interior winters + Coquihalla corridor                  |
| `car_seat_fit` |  0.5 |  2.0 | Two **teens**, no car seats — near-irrelevant                      |
| `hitch`        |  0.3 |  0.5 | Not mentioned                                                      |
| `third_row`    |  0.2 |  1.0 | Family of 4; no third row needed (all entries score 1 = absent)    |
| `fsr`          |  0.2 |  0.5 | No off-pavement use mentioned                                      |

Net effect: cargo and TCO dominate; family-fit / third-row / off-road are
near-zero. This is the inverse emphasis of the kaan-and-tess minivan search.

## Cohort-shape goals

- **Powertrain span (home charging is the swing factor).** 8 BEV, 4 PHEV,
  4 HEV, 2 ICE, + the current car. Home charging + a city-heavy duty cycle
  makes BEV/PHEV running costs the story; the matrix lets the family see how
  much the electric advantage is worth against cargo/range/capital.
- **Cargo focus.** Cargo-strong SUVs/wagons (RAV4, CR-V, CX-5, Outback,
  Tucson PHEV, Ioniq 5, Model Y) anchor the top; efficient-but-small sedans
  (Ioniq 6, Corolla/Prius family, Model 3) are included as honest
  efficiency benchmarks that the cargo weight then penalises.
- **New vs used spread.** Teslas, RAV4, Niro, Tucson, Outback, EV6, ID.4,
  Bolt all appear used; the strong nameplates also appear new — the
  new-vs-used delta is one of the clearest TCO lenses.
- **The current 2018 Corolla as baseline** (`on_road` = ~$17k resale, the
  opportunity cost of keeping it). Every upgrade must beat "do nothing."

## Scoring notes (per-criterion judgment)

- `third_row` = **1 for every entry** (none have a third row; the family
  doesn't need one — weight is 0.2 so it's near-invisible).
- `car_seat_fit` measures "fits the family across a row"; with teens this is
  trivially met (mostly 5; small rear seats score 4). Low weight.
- `cargo` (the heavy weight) follows behind-seat + fold-flat volume, with a
  conceptual frunk bonus: Tesla/Ioniq frunks help; sedans (Ioniq 6 401 L,
  Corolla 371 L) score 2.
- `corridor` rewards effortless 400–800 km range: ICE/HEV/PHEV score 4–5;
  long-range BEVs (Ioniq 6 580 km, Model Y/3 ~500 km) 4; mid BEVs 3; the
  Bolt 2 (slow 55 kW DCFC makes the long trips painful).
- `winter` is AWD + clearance: AWD entries 4 (Outback 5 on clearance);
  FWD/RWD 2–3.

## Warranty-years-remaining (maintenance-cliff inputs)

New BEV/PHEV traction battery **8 yr**; Toyota/Lexus hybrid battery **10 yr**
(RAV4 Hybrid, Corolla Hybrid, Prius); new ICE powertrain **5 yr** (CX-5);
used entries carry the remainder (e.g. used Outback **2**, used Niro/Tucson
PHEV **5**, used Teslas **6**). The current Corolla is **0** (out of
warranty) with an explicit `maint_oow_per_year` premium for its age.

## Honest-tradeoff outcomes worth showing the family

- **Bolt EUV** has the outright lowest TCO (tco_score 5.0) yet ranks low —
  its cargo/corridor/winter limits are the price of that cheapness.
- **Ioniq 6** is the efficiency/range champion but lands last: the small
  trunk collides with the cargo priority. Kept precisely to make that
  trade visible.
- **Gas-only CX-5 / Outback** rank below their electrified peers under a
  TCO-primary, city-heavy profile — the running-cost gap is the lesson.
