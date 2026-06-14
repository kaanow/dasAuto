# Decisions Log — kaan-and-tess

> Append-only narrative of the journey. New sessions add entries at the
> bottom. Older entries don't get edited (they're the historical record).

## 2026-04-03 — Session 1 (intake)

Original brief delivered (now at `family.md`). Family of 5 (2 adults + 3
kids, baby due August 2025), Vancouver BC, ICBC class 003. Annual km
~15,300/yr. 12 corridor trips/yr (Vancouver↔Kamloops↔100 Mile House).
Open to ICE / hybrid / PHEV / BEV. AWD listed as a requirement (note: this
became contested later — see 2026-05 below). 10-year TCO is the primary
metric. Light FSR; clearance not top priority.

## 2026-04 to 2026-05 — Cohort buildout

Initial 12-vehicle cohort, expanded to 18, then 20, then 24, then 28.

Notable additions:
- Toyota Grand Highlander Hybrid (new + used) — anchor pick
- Sienna Hybrid (new + used + 2011 AWD vintage)
- Pacifica Hybrid PHEV (used) and gas AWD (new) and PHEV FWD (new)
- Kia Sorento PHEV
- Mazda CX-90 PHEV
- Tesla Model Y (new + used)
- Kia EV9
- Hyundai IONIQ 9
- Toyota bZ4X (new + used)
- VW ID. Buzz (new + used)
- 2007 Honda CR-V (the household's current vehicle, as the "keep what
  we have" baseline at $6,000 opportunity cost)
- Carnival Hybrid (new) — the missing hybrid minivan
- Honda Odyssey (new gas) and Kia Carnival (new gas) as gas-minivan
  comparison

Historical adds dropped or replaced:
- 2021 Toyota RAV4 Hybrid — initially in as the 5-yr vintage entry,
  dropped when family confirmed 3-row required
- 2006 Toyota 4Runner — initially in as the 20-yr vintage entry,
  dropped for the same reason; replaced by 2006 Toyota Sequoia (8-seat,
  V8, BOF)

## 2026-05 — The AWD-as-hard-filter bug

Earlier cohort selection had used "AWD or 4WD available" as a hard filter,
which silently excluded every FWD-only minivan format (Pacifica, Odyssey,
Carnival are FWD; only Sienna offers AWD). The cohort got biased toward
SUVs without anyone explicitly deciding minivans were out. Caught when the
family-of-five decision frame surfaced minivan capability questions that
the cohort couldn't answer.

Resolution: AWD became a **scored criterion** through `winter` and `fsr`
(both 1–5). The selection principle (`docs/selection_principle.md`) was
written up as a hard rule to prevent recurrence.

This is the lesson that drove the lost-brief discussion later.

## 2026-05 — Toyota bZ4X and 2026 Palisade Hybrid added

Late additions for completeness. bZ4X (new + used) confirmed Toyota's BEV
warranty is 8yr/160k, NOT the 10yr/240k hybrid moat — important
distinction to keep buyers from over-anchoring on the Toyota brand.

2026 Palisade Hybrid (full redesign) added at $74,500 on-road. Lands
#19 — Hyundai brand reliability + new-platform + ~$12k premium vs
Grand Highlander Hybrid hurt it on the matrix despite genuine quality.

## 2026-05 — Variable-horizon TCO ships

Replaced the legacy 10-year aggregate model with NPV-per-unit + per-year
maintenance rates. Horizon slider 4–15 yrs goes live. Each vehicle's TCO
components re-derive at any horizon. See `docs/tco_methodology.md`.

## 2026-05-29 — Web UI for archive/restore

Added `active: bool` flag + SQLite override layer so the family could
deactivate vehicles from the web UI without editing `vehicles.json`.
Bookmarks to archived vehicles still resolve (the detail page renders
"Archived — not in active cohort"). The override table is on the Railway
volume so web edits survive deploys without conflicting with git pushes.

## 2026-05-30 — Family converges on minivans

After test drives, family explicitly narrowed to minivans only. Every
non-minivan in the cohort was soft-archived via the web UI. Added three
new minivans I'd been missing: Kia Carnival Hybrid (the genuinely missing
hybrid), Honda Odyssey new gas, Kia Carnival new gas.

Final active set: 13 minivans.

## 2026-06-01 to 2026-06-09 — Sienna cross-shop + dealer quote

Family narrowed further to Toyota Sienna AWD Hybrid (any vintage 2021+).
Manual listings curated weekly from AutoTrader, Kijiji, Facebook
Marketplace. The AutoTrader live scraper is essentially blocked by
Incapsula on Railway IPs — relying on AI + human collab for late-stage
listing curation.

Active dealer quote captured in `dealer_quotes/sienna-new.json` for a
2026 LE AWD 8-pass at $58,250 sale → ~$67,038 all-in.

`/siennas` cross-shop page built (vehicle-specific generalization
follow-up: `/cross-shop/<vehicle-id>`).

Top-of-board:
- **2024 Limited @ 43k km (Jim Pattison Northshore)** — net 10yr
  ~$88,800, value leader by $8k+
- **2025 LE Silver @ 34.9k km (Juju FB)** — net 10yr ~$97,100
- **2026 LE dealer quote** — net 10yr ~$97,100 (essentially tied)
- **2025 LE White @ 6.3k km (OpenRoad Lexus)** — net 10yr ~$100,400

## 2026-06-09 — Lost-brief recovery + architectural reset

Discovered the original PROJECT_BRIEF.md had been dropped from the
project handoff. Restored verbatim. The annual km (15,300) had been
lost; folded back into the situation file. Family noted that this drift
was the *real* cause of the AWD-as-hard-filter confusion: sessions had
worked from `situation.md` alone, which had silently drifted from
original intent.

Architectural restructure followed:
- `PROJECT_BRIEF.md` → `family.md` (canonical input)
- `situation.md` deprecated — content split between `family.md`
  (input), `docs/` (methodology), and `research/` (this family's
  research)
- `sienna_quote_2026.json` → `dealer_quotes/sienna-new.json` (typed
  path that generalises)
- `tco_research.md` → `research/tco_research.md` (clearly an artifact)
- `decisions_log.md` (this file) created — session story moves here
  out of CLAUDE.md
- `docs/` created at repo root with all family-agnostic methodology
- `CLAUDE.md` rewritten as architecture-only

This was also the session where the multi-family deployment plan
solidified: brother (Theo) joins with `user-theo/` and his own Railway
service at `brudersauto.alti2.de`. The repo structure now supports
both.

## 2026-06-13 — Decision reached: Sienna purchased. Project parked.

**The family bought a Toyota Sienna AWD Hybrid** — the conclusion of the
whole search (28-vehicle cohort → minivans-only → Sienna AWD Hybrid → the
`/siennas` cross-shop). The board's value leader was the **2024 Sienna
Limited AWD (~43k km, North Vancouver, $48,995)** at ~$88.8k net 10-yr TCO.

Insurance was estimated at **~$1,300/yr** (ICBC Basic + comprehensive with a
high deductible, Territory D / class 003 / CDF 0.528) — about $300/yr under
the model's full-coverage assumption.

The tool did its job: from a broad powertrain/body survey down to a specific
used vehicle, with TCO as the throughline. **Parking the kaan-and-tess
project here.** The repo, the cross-shop page, listings, and all research
remain live for reference; the deployment stays up. (Theo's project under
`user-theo/` is independent and continues.)
