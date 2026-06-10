# Multi-Family Generalisation — status

> Tracks the work to take the app from "kaan-and-tess + BC + Sienna" to
> "any BC family". Born from the Theo onboarding. Architectural, not
> family-specific. Update as items land.

## Standing assumption: every family is in BC

The tax engine (BC PST tiers, `docs/tax_math_canada.md`), the AutoTrader
listing-scope filter (`app.py`, ON/NS/AB exclusion), and insurance
references are all BC-specific. We **assume BC for all families** and guard
it: `app.py` emits a startup WARNING if a family's `site.json` has
`region_code != "BC"`. A non-BC family is the trigger to generalise items 4–5
below — until then they stay BC-coded on purpose.

## Done

1. **Brand×powertrain ratio map** — `vehicle-app/repair_ratios.json` +
   `tco.py repair_ratio()`. Derives `maint_oow_per_year` from
   `maint_in_per_year × ratio` when a vehicle omits it; an explicit
   `maint_oow_per_year` always wins (per-vehicle age/km premiums). Fixed the
   doc/data drift found along the way (VW was 4.8× in the doc but 4.0× in
   data; doc now keyed by make×powertrain). kaan's numbers unchanged — every
   existing vehicle has an explicit oow override.
2. **Site identity config** — `user-<family>/site.json` (site_name,
   short_name, region_label, region_code, insurance_ref, data_sources).
   `app.py` injects it via context processor; templates read `{{ site.* }}`.
   Removed all hardcoded "BC Family Vehicle Browser" / "Vancouver, BC" /
   "ICBC Territory D…" strings.
3. **BC guard** — non-BC `region_code` → loud startup warning (see standing
   assumption).
4. **Criterion-set decision** — the 9 keys are a fixed superset; families
   zero-weight irrelevant criteria rather than forking the list. Documented
   in `docs/scoring_framework.md`.

## Deferred (with rationale)

5. **Cross-shop generalisation** — `/siennas` → `/cross-shop/<vehicle-id>`,
   and the `_sienna_residual / _sienna_maint / _sienna_5_10` helper family →
   nameplate-parameterised. **Deferred until Theo converges on a nameplate.**
   Rationale: today there is exactly one concrete cross-shop (Sienna). Building
   the abstraction from a single example bakes in Sienna assumptions about
   residual curves and trim tiers; the second real nameplate is what reveals
   the right parameters. Build it over two cases, not one. It's also unused
   surface until a family converges.
6. **Region/tax generalisation** — BC PST → province-parameterised tax engine,
   and the AutoTrader scope filter → region-driven. **Deferred until a non-BC
   family shows up** (the guard in item 3 will announce it). Note: tax math
   currently runs only in the cross-shop path; the main board uses pre-baked
   on-road prices, so this is coupled to item 5, not the main cohort.

## When Theo's family.md lands

Run `docs/new_family_playbook.md` end-to-end for `user-theo/`. His criterion
weights should keep all 9 keys but set `corridor`/`fsr` low/zero if they
don't apply. His vehicles can omit `maint_oow_per_year` and lean on the ratio
map; only set it explicitly for per-vehicle premiums.
