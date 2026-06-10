# New-Family Buildout Playbook

> **Purpose.** Going from a family's `family.md` brief to a working cohort, a
> live ranked list, and ongoing decision support is a substantial AI research
> project. We did it for kaan-and-tess over many sessions and hit drift,
> redo's, and architectural lessons along the way. This playbook captures the
> sequence and the lessons so the next deployment lands faster and avoids the
> mistakes we've already paid for.

This document is **architectural** (skill-level, not family-specific). It
applies to every new deployment of the dasAuto skill. Read it end-to-end
before starting a new family. Reference it during the work.

---

## 0. What you're building

For every family, the deliverables are:

- A `family.md` (the user's input — they hand you this)
- A `weights.json` (default importance weights for the 9 scoring criteria)
- A `vehicles.json` (the candidate cohort with per-criterion scores)
- A `tco_research.md` (the family-specific cost rates and assumptions)
- An `image_seeds.json` (curated image URLs per vehicle)
- An `images/` folder (downloaded galleries)
- A live deployment on Railway (`family.alti2.de` or similar)
- Ongoing per-decision artifacts (`dealer_quotes/`, `manual_listings.json`,
  `research/cohort_rationale.md`, `research/decisions_log.md`)

The **app code** in `vehicle-app/` is family-agnostic. You write **zero** code
per family. Everything family-specific lives in `user-<label>/`.

---

## 1. Intake (one session)

### 1.1 Read `family.md` end-to-end

It contains: household composition, driving profile, requirements, criteria
intent, geography, insurance baseline. **Confirm these facts are captured:**

- [ ] Number of adults + children, ages
- [ ] Number of car seats / booster seats needed
- [ ] **Annual km/yr** ← this anchors the entire TCO model; if missing, ask
- [ ] Typical trip profile (urban-only vs corridor trips)
- [ ] EV charging available at home?
- [ ] Hard requirements vs. nice-to-haves
- [ ] Powertrain openness (EV / hybrid / PHEV / ICE)
- [ ] Geography for sourcing
- [ ] ICBC class + driver factor (BC-specific; replace with equivalent
      elsewhere)
- [ ] Current vehicle (the "do nothing" baseline)
- [ ] Decision horizon (default 10 years)

### 1.2 Flag ambiguities back to the family BEFORE proceeding

This is the lesson from the kaan-and-tess "AWD as hard filter vs. scored
criterion" drift. **If the brief says one thing and the natural cohort
interpretation says another, surface the conflict explicitly.** Don't
silently resolve it.

### 1.3 Save the brief verbatim

Whatever the family writes is the *canonical record* of original intent. Do
not edit it. If you need to capture clarifications, put them in
`research/decisions_log.md`, not by amending the brief.

---

## 2. Selection criteria & weights (one session)

### 2.1 Hard filters vs. scored criteria — the structural rule

A trait is a HARD filter **only if** it would make the vehicle structurally
infeasible (the family does not fit in it at all). A trait that varies by
degree is a SCORED criterion — never both. See `selection_principle.md` for
the full rule and the AWD-minivan story that taught it.

Typical hard filters:
- Seats ≥ household size
- In-market availability (you can actually buy one in the family's region)

Typical scored criteria (the 9-criterion framework — see
`scoring_framework.md`):
- `tco`, `car_seat_fit`, `cargo`, `third_row`, `corridor`, `hitch`,
  `reliability`, `winter`, `fsr`

### 2.2 Tune weights to the brief's stated priorities

Start from the defaults in `vehicle-app/briefs/`. Adjust each weight based on
explicit statements in `family.md`. Document any non-default weight in
`research/cohort_rationale.md` so the reasoning is preserved.

Example: if the family says "FSR use is occasional summer only," `fsr`
should land at ~0.5 (lowest band), not at 1.5+. If they say "we drive the
Coquihalla in winter," `winter` lands at ~1.3+. Don't guess — quote the
brief.

### 2.3 Write `weights.json`

Just the JSON dict. The narrative explanation goes in
`research/cohort_rationale.md`.

---

## 3. Cohort building (multiple sessions)

### 3.1 Body-style brainstorming

Based on household size + driving profile, identify which body styles
qualify. For 5+ people:
- Minivans (Sienna, Pacifica, Odyssey, Carnival, ID. Buzz)
- 3-row SUVs (Grand Highlander, Telluride, Palisade, Ascent, Pilot, etc.)
- Large SUVs (Sequoia, Suburban, etc.)
- Wagons (rare, but Outback if 5-only)

For 4 or fewer:
- Compact SUVs, sedans, hatchbacks open up

### 3.2 Powertrain diversity is a cohort-shape goal

Aim to represent ICE / hybrid / PHEV / BEV so the family can see
cost/utility trade-offs across the matrix. This isn't a per-vehicle filter
— it shapes selection. Honest representation lets the math speak.

### 3.3 New vs. used spread

For each strong nameplate, consider including both a new and a used variant
(usually one or two model years old). The new-vs-used comparison is one of
the most useful decision lenses.

### 3.4 Target cohort size: 15–25 entries

Smaller than 12: too sparse, no variety. Larger than 30: hard to scan, the
matrix gets noisy.

### 3.5 Per-vehicle research

For each entry, capture:

- **Specs:** fuel economy, range, towing, cargo, seats, 3rd-row legroom,
  ground clearance
- **Pricing:** MSRP for new, market range for used (use AutoTrader,
  CarGurus, Kijiji)
- **Warranty:** basic, powertrain, hybrid system, traction battery — each
  has a time AND a km cap; the cost-dominant one is your
  `warranty_years_remaining`
- **Reliability:** Consumer Reports rating, JD Power, recall completion
- **Score** against the 9 criteria (1–5 each)

### 3.6 Write `vehicles.json` entries

Schema in `docs/cohort_schema.md` (TODO — extract from current vehicles.json
shape). Key fields:

- `id`, `rank` (placeholder; runtime computes), `name`, `short_name`,
  `make`, `model`, `powertrain`, `powertrain_type`, `new_used`, `years`
- `on_road`, `pretax`, `fuel_10yr`, `ins_10yr`, `resid_10yr`
- `scores` (dict of 9 criterion → 1-5)
- `specs` (dict — fuel_economy, range_km, clearance_mm, towing_lbs, cargo_l,
  seats, third_row_legroom)
- `why`, `tradeoffs`, `caution`
- `at_make`, `at_model`, `at_years`, `cr_url` (for listings deep-links)
- `warranty_years_remaining`, `maint_in_per_year`, `maint_oow_per_year`
- `active` (true/false — soft flag for archive without deleting)

---

## 4. TCO methodology (one session)

### 4.1 Family-specific rate research

Create `tco_research.md` in `research/`. Capture:

- Fuel prices (gas, electricity, DCFC) in the family's region, with
  escalation rates
- Insurance rates (BC ICBC class + driver factor in our case)
- Discount rate (we used 5.5% nominal = 3.0% real + 2.5% CPI)

See kaan-and-tess's `research/tco_research.md` for the BC reference
implementation.

### 4.2 Wire the rates into `vehicle-app/tco.py`

If the family is in a region we haven't deployed before, the constants
inside `tco.py` (`_FUEL_RATES`, `MAINT_IN_PER_YEAR_DEFAULT`) may need
adjustment. **This is the only place skill-level code touches family-specific
constants — and ideally we lift them to family JSON config later.**

### 4.3 Maintenance rates per vehicle

Each vehicle's `maint_in_per_year` and `maint_oow_per_year` come from
brand-level repair-tail ratios. See `brand_repair_tail.md` for the table:

| ratio | brand                                | rationale                          |
|------:|--------------------------------------|------------------------------------|
| 2.0×  | Toyota (all hybrids)                 | Best OOW repair tail               |
| 2.5×  | Honda, Mazda CX-90 PHEV              | Above-average reliability          |
| 3.0×  | Subaru, Hyundai/Kia ICE              | Industry baseline                  |
| 3.5×  | Korean BEV/PHEV, Tesla Model Y       | Battery tail bounded but expensive |
| 4.0×  | Stellantis Pacifica Hybrid           | Documented OOW electrical issues   |
| 4.8×  | VW (Atlas)                           | Below-average brand reliability    |

### 4.4 Run the recompute

```python
from scoring import normalize_tco_score
from tco import recompute_tco
# loop vehicles, compute tco_value, normalize across cohort
```

See the recompute script pattern in any of the early commits.

---

## 5. Image fetching (one session)

### 5.1 Wikimedia first

It's CC-licensed and reliable. Use the API to find category members for
each vehicle's generation/category. See
`vehicle-app/briefs/image_research_brief.md` for the per-vehicle research
template.

### 5.2 Image seeds in `image_seeds.json`

Per vehicle: 5–7 URLs covering exterior, interior, key detail shots.

### 5.3 Run `fetch_images.py`

It downloads, letterbox-resizes to 900×600 on `#14181e`, MD5-dedups. Uses a
contact-bearing User-Agent because Wikimedia 429s generic Chrome strings.

---

## 6. Deployment (one session)

### 6.1 Railway

One service per family. Same repo. Each service:

- Sets `VEHICLE_DATA_DIR=user-<label>` env var
- Sets `VEHICLE_DB_PATH=/data/cache.db` env var
- Has a 1 GB persistent volume mounted at `/data`
- Has a generated domain + (optional) custom domain CNAME

See `README.md` § "Deploying to Railway" for the full walkthrough.

### 6.2 Custom domain pattern

We use `<family>.alti2.de`:
- `dasauto.alti2.de` → kaan-and-tess
- `brudersauto.alti2.de` → theo

Add the custom domain in Railway → it provisions a Let's Encrypt cert
within a few minutes.

---

## 7. Iteration with the family (ongoing)

### 7.1 Live tuning via the sidebar

The app exposes weight sliders and a horizon slider. URLs preserve state
via query params, so families can share specific rerank views.

### 7.2 Archive vehicles via the web UI

Soft-deactivate from the detail page or the index card. State persists on
the Railway volume's `active_overrides` table. See `archive_layer.md`
(TODO) for details.

### 7.3 Refresh listings via Claude

The autoscraper is rate-limited by AutoTrader's Incapsula on Railway IPs
(returns mostly 0 results). The current pattern: when the family wants
fresh listings, the user asks the AI to re-scour, and the AI updates
`manual_listings.json` directly. Mid-stage and late-stage decision support
is an **AI + human collab loop**, not an autonomous scrape.

### 7.4 Test drives + dealer quotes

Capture dealer quotes in `dealer_quotes/<vehicle-id>.json`. Surface them on
the vehicle's cross-shop page (`/cross-shop/<vehicle-id>`).

---

## 8. Late-stage: vehicle-specific cross-shop (one session, per converged vehicle)

When the family has narrowed to a single nameplate:

### 8.1 Create the cross-shop page data

- Drop a `dealer_quotes/<vehicle-id>.json` if there's an active new-vehicle
  quote
- Curate `manual_listings.json` for that vehicle aggressively (FB
  Marketplace + AutoTrader + Kijiji; ~10–20 listings)

### 8.2 The cross-shop page is generic

`/cross-shop/<vehicle-id>` route renders for any vehicle. Top-picks cards
auto-compute. No per-vehicle code.

### 8.3 Run it as a working document

Refresh listings weekly. Update dealer quotes when negotiated.

---

## 9. Lessons learned (the hard-won knowledge)

These are the mistakes we paid for in kaan-and-tess. Future families
should avoid them.

### 9.1 Lost-brief drift

> **Don't silently work around a missing brief.** If you can't find the
> original requirements doc, ASK. We lost the original PROJECT_BRIEF.md
> during handoff and spent multiple sessions drifting from original intent
> (most consequentially: AWD-as-hard-filter became AWD-as-scored-criterion
> without explicit consultation).

Mitigation: **The first thing every session must do** is verify the brief
is present in `user-<family>/family.md`. If absent, ask the user.

### 9.2 Hard-filter vs scored-criterion confusion

> **A trait is a HARD filter only if it would make the vehicle structurally
> infeasible.** A trait that varies by degree must be a scored criterion,
> never both. The earlier mistake of using "AWD/4WD available" as a hard
> filter silently excluded every FWD minivan despite `winter` already
> existing as a scored criterion.

See `selection_principle.md`.

### 9.3 Anchor-vs-horizon naming

> **Don't use horizon-specific suffixes (`_10yr`) on display fields when
> the value is computed at a variable horizon.** It misled both code
> readers and prose authors. Use unsuffixed names for computed fields;
> reserve `_10yr` for the stored *base-horizon anchor* values.

### 9.4 Per-year vs aggregated maintenance

> **Store maintenance as per-year rates (`maint_in_per_year`,
> `maint_oow_per_year`), not 10-year aggregates.** The aggregate form
> required denominator gymnastics to back out per-year rates and was hard
> to source/validate. Per-year rates are vehicle-intrinsic and trivially
> extend to multi-tier warranties.

### 9.5 Soft-archive instead of delete

> **Use `active: bool` + a SQLite override table.** When a family narrows
> their cohort, archived entries should remain accessible via direct
> `/vehicle/<id>` URLs (bookmarks survive). Hard-deleting from
> vehicles.json loses the research investment.

### 9.6 Listings scraping is a losing game

> **AutoTrader's Incapsula blocks Railway IPs.** Don't waste effort on
> autonomous scrapers in production. The live AT scraper is essentially
> non-functional. The working pattern: AI + human curation. The user asks
> for a refresh, the AI runs WebFetch (which avoids the bot wall via a
> different network path), and writes `manual_listings.json`. The app
> reads that file as a baseline and merges with any live cache results.

### 9.7 Mobile rendering: `position: sticky` is hostile inside column-grids

> **On phones (under 900px), set sidebar/detail-sidebar to `position:
> static`.** iOS Safari has long-standing rendering bugs where sticky
> elements visually overlay scrolling content in column-direction layouts.

### 9.8 BC PST is tiered, not flat

> **The tax math has steep thresholds at $55k / $56k / $57k / $125k.**
> Negotiating a sale below $55k saves *both* the negotiation amount AND
> the PST tier (7% vs 10%). This double-dip effect was decision-relevant
> in the kaan-and-tess Sienna negotiation.

### 9.9 Don't quote stale TCO numbers in prose

> **Prose in `why` / `tradeoffs` / `caution` fields should be
> horizon-agnostic.** Don't say "10-year net TCO of $X" because that
> number shifts when the cohort changes or the horizon slider moves. Use
> "over the planning horizon" and let the live table show the actual
> dollars.

### 9.10 The current car is a baseline, not a candidate

> **Include the family's current vehicle in the cohort with `on_road`
> = current resale value.** This makes "keep what we have" an explicit
> option with computed forward cost. Every upgrade has to justify its
> premium over zero.

---

## 10. Anti-drift checklist

Run through this list at the start of any new session on an existing
family. If any item fails, fix it before proceeding.

- [ ] `user-<family>/family.md` exists and is unedited from original input
- [ ] Architectural docs in `docs/` are not referenced by family code
- [ ] Family-specific JSON files in `user-<family>/` (not in `docs/` or
      `vehicle-app/`)
- [ ] `vehicles.json` `active` field matches the family's current scope
- [ ] `weights.json` matches the criteria emphasis in `family.md`
- [ ] Recent decisions are recorded in
      `user-<family>/research/decisions_log.md` (so future sessions can
      replay the why)
- [ ] No code in `vehicle-app/` names a specific family

---

## 11. Templates & scaffolding

To start a new family:

1. Create `user-<label>/` (e.g., `user-theo/`)
2. Copy `vehicle-app/briefs/family_brief_template.md` → `user-<label>/family.md`
3. Have the family fill it out
4. Read it end-to-end (Step 1 above)
5. Proceed through Steps 2–6
6. Create Railway service, point at `user-<label>/`
7. Add custom domain CNAME

The brother (`user-theo/`) is currently at the stub stage. Once his
`family.md` arrives, proceed from Step 1.
