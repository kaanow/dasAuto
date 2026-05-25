# Research Brief: Vancouver BC Fuel & Electricity Price Projections for TCO Model

## Context

This research feeds a 10-year Total Cost of Ownership (TCO) model for a family vehicle
purchase decision in Vancouver BC (Metro Vancouver / Lower Mainland). The model currently
uses flat rates with no price escalation and no time-value-of-money discounting. We need
to replace that with credible forward projections.

Current flat-rate assumptions in the model:
- Gasoline: **$1.65/L** (Vancouver pump price)
- Home electricity: **$0.125/kWh** (BC Hydro residential, Step 1 rate approx)
- DC fast charging (DCFC): **$0.38/kWh**
- Model year: 2025–2026 purchase, project costs over **years 1–10** (calendar ~2026–2035)

---

## Research Tasks

### 1. Gasoline — Vancouver pump price trajectory

**Find:**
- Confirmed current average Vancouver pump price (April 2026) in CAD/L
- Historical annual average pump prices for Vancouver for as many years as available
  (ideally 2015–2025). GasBuddy historical data or NRCan pump price surveys are good sources.
- Any government or credible analyst projection for Vancouver/BC gasoline prices 2026–2035.
  Key factors to capture:
  - BC carbon tax trajectory (note: federal consumer carbon tax was paused for consumers
    in early 2025 — clarify current BC-specific carbon levy status and any scheduled changes)
  - BC Motor Fuel Tax (fixed cents/L — document current rate)
  - TransLink levy (Metro Vancouver specific — document current rate)
  - Underlying crude/refining component trend

**Sources to check:**
- Natural Resources Canada (NRCan) pump price data: `www2.nrcan.gc.ca/eneene/sources/pripri`
- GasBuddy historical Vancouver data
- BC government carbon tax schedule
- Canada Energy Regulator (CER) Canada's Energy Future report (latest edition)
- RBC / TD / BMO commodity research if accessible

---

### 2. BC Hydro residential electricity — rate trajectory

**Find:**
- Confirmed current BC Hydro Tier 1 and Tier 2 residential rates (¢/kWh) as of April 2026
- Historical rate changes: document each approved rate increase since ~2015, with effective date
  and percentage change. BCUC (BC Utilities Commission) rate decisions are the authoritative source.
- BC Hydro's approved rate schedule or rate application forecasts for 2026–2030 if available
- Any independent forecast for BC residential electricity rates 2026–2035
  (BCUC rate applications typically include 10-year forecasts)

**Sources to check:**
- BC Hydro rate schedule: `www.bchydro.com/accounts-billing/rates-energy-use/electricity-rates`
- BCUC rate decisions database: `www.bcuc.com`
- BC Hydro Integrated Resource Plan (IRP) — contains long-term demand/cost projections

---

### 3. DCFC (DC Fast Charge) public charging rate trajectory

**Find:**
- Current rates charged by major DCFC networks in BC: ChargePoint, Electrify Canada, FLO, Tesla Supercharger
  (confirmed ¢/kWh or $/min as of April 2026)
- Any trend or projection for public DCFC rates 2026–2035
- Note: DCFC rates are loosely tied to BC Hydro commercial/demand rates, which follow a different
  trajectory than residential. Document if a clear escalation pattern exists.

---

### 4. Suggested escalation model

Based on the data found, recommend **one of these approaches** (or justify a different one):

**Option A — Constant real price** (no escalation): prices stay flat in real terms, inflate with CPI.
**Option B — Piecewise linear**: use distinct escalation rates for different sub-periods
  (e.g. 2026–2030 vs 2031–2035) if the data shows a clear inflection.
**Option C — Scenario-based**: provide a low/mid/high annual escalation rate for each fuel type.

For each fuel type, provide the recommended annual nominal escalation rate(s) (%) with justification.

---

## Output Format

Respond with a single markdown block structured **exactly** as follows so it can be
copy-pasted directly into the TCO model update:

```
## RESEARCH RESULTS

### Gasoline (Vancouver pump price)
- Current price (confirmed, April 2026): X.XX CAD/L
- Source: [name + URL]
- Historical data points (year: avg $/L):
  - 2015: X.XX
  - 2016: X.XX
  ... (as many years as found)
- BC carbon tax / levy schedule (if any scheduled changes post-2026):
  - [date]: [change description]
- Recommended nominal escalation rate: X.X% / yr  (or piecewise — see below)
- Escalation model: [A/B/C] — [one-paragraph justification]
- Piecewise rates (if B): 2026–2030: X.X%/yr, 2031–2035: X.X%/yr

### BC Hydro Residential Electricity
- Current Tier 1 rate (confirmed, April 2026): X.XX ¢/kWh
- Current Tier 2 rate (confirmed, April 2026): X.XX ¢/kWh
- Source: [name + URL]
- Historical approved rate increases since 2015:
  - [effective date]: +X.X% — [BCUC decision reference]
  ... (all found)
- Approved future rate schedule (if known):
  - [effective date]: +X.X%
- Recommended nominal escalation rate: X.X% / yr
- Escalation model: [A/B/C] — [one-paragraph justification]

### DCFC Public Charging
- Current rate (confirmed, April 2026): X.XX ¢/kWh (network: [name])
- Source: [name + URL]
- Trend / trajectory notes: [paragraph]
- Recommended nominal escalation rate: X.X% / yr
- Escalation model: [A/B/C] — [one-paragraph justification]

### Suggested Discount Rate for NPV
- Recommended real discount rate: X.X%
- Recommended nominal discount rate: X.X%  (= real + CPI assumption of X.X%)
- Justification: [one paragraph — e.g. opportunity cost of capital, consumer rate, etc.]

### Data Quality Notes
- [Any caveats about data freshness, gaps, or conflicting sources]
```

---

## Validation Checks (perform before submitting)

1. All prices are in **CAD**, not USD.
2. Vancouver pump price is Metro Vancouver / Lower Mainland average, not national average.
3. BC Hydro rates are residential Schedule 1199 (not commercial or industrial).
4. Carbon tax figures reflect **BC-specific** levies — clarify if federal consumer carbon
   tax is currently applied in BC or paused (as of April 2026).
5. At least **3 historical data points** exist for each fuel type before recommending an escalation rate.
6. Each URL cited is confirmed accessible (not a 404).

---

## What NOT to include

- Do not include vehicle-specific calculations — just the price/rate data.
- Do not summarize or editorialize beyond what's asked.
- Do not suggest changing the vehicles under consideration.
- Provide sources for every number.
