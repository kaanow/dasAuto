# Selection Principle

> A trait is a HARD filter only if it would make the vehicle structurally
> infeasible (the family does not fit in it at all). A trait that varies by
> degree must be a SCORED criterion (it shapes the ranking) — never both,
> never one masquerading as the other.

## Why this matters

The scoring framework already accounts for trade-offs by degree. Adding a
hard filter on top of a scored criterion double-counts the same trait AND
silently kills entire vehicle categories.

## How we learned it (the AWD-minivan story)

An earlier draft of the kaan-and-tess cohort used "AWD or 4WD available" as
a hard filter. This silently excluded every FWD-only minivan format
(Pacifica, Odyssey, Carnival are FWD; only Sienna offers AWD). The cohort
got biased toward SUVs without anyone explicitly deciding minivans were
out — even though the family later converged on a Sienna minivan as their
top pick.

The bug was invisible. The cohort just *looked smaller and SUV-heavier*
than the family's actual options.

The framework already had:
- `winter` (1–5 scored, for Coquihalla / snow tires)
- `fsr` (1–5 scored, for light off-pavement)
- `reliability` (1–5 scored)

All three of those soak up the AWD trade-off honestly. Adding AWD as a
hard filter was the bug.

The same shape of error nearly killed the Tesla Model Y under a "7-seat
required" hard filter, even though a family of five literally fits in a
5-seater (with zero overflow margin). The right move was to keep Model Y
in the cohort and penalize it on `car_seat_fit` and `third_row` scoring.

## Practical guidance

A new family's `family.md` will typically distinguish:

**Hard filters — structural infeasibility:**
- Seats ≥ household size (a 5-person family can't sit in a 4-seater)
- In-market availability (vehicle can actually be bought in the region
  within the planning window)

**Cohort-shape goals — drive selection but aren't per-vehicle tests:**
- Span of powertrains (ICE, hybrid, PHEV, BEV all represented)
- Body-style diversity (SUVs, minivans, optionally an outlier)

**Scored, not filtered:**
- Drivetrain (AWD/FWD/4WD) → `winter` + `fsr` + `reliability`
- Ground clearance → `winter` + `fsr`
- Hitch availability → `hitch`
- Factory warranty length → `warranty_years_remaining` in TCO model
- Brand reliability → `reliability`

## Verification

When you're about to write a hard filter into `family.md` or the cohort
selection logic, ask: *"Is this trait binary (the vehicle has it or doesn't,
no in-between) AND would I refuse to consider a vehicle that lacks it,
regardless of how good its other traits are?"*

If yes → hard filter.
If "well, depends on how good other things are" → scored, not filtered.
