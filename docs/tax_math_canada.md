# Tax & Fee Math (Canada / BC)

> Family-agnostic for BC; for other provinces, replace the PST tier table.

## BC (kaan-and-tess, theo)

### PST tiers (vehicle purchase from a dealer)

BC PST on vehicles is a **flat rate** applied to the entire sale price,
tiered by purchase price:

| Sale price          | PST rate |
|---------------------|---------:|
| under $55,000       | 7%       |
| $55,000 – $55,999   | 8%       |
| $56,000 – $56,999   | 9%       |
| $57,000 – $124,999  | 10%      |
| $125,000 – $149,999 | 15%      |
| $150,000 and up     | 20%      |

GST is always 5%, applied to the same sale price.

### All-in formula

```
all_in = sale × (1 + 0.05 + pst_rate) + license_fee
       ≈ sale × 1.12 to sale × 1.25
       + ~$50 BC licensing
```

### Tier-threshold leverage

The flat-tier structure means a $1 reduction across the $55k boundary
saves both the negotiation amount *and* the PST tier jump. Example:

- $58,250 sale → 10% PST → $5,825 PST
- $54,999 sale → 7% PST → $3,850 PST
- Savings: $1,975 in PST alone, on top of the $3,251 price reduction

This is the decision-relevant detail in any BC vehicle negotiation. Surface
it explicitly in deal coaching.

## Mandatory dealer fees that get taxed

All of these add to the sale price *before* tax is calculated:

| Fee                          | Typical       | Notes                              |
|------------------------------|--------------:|------------------------------------|
| Documentation                | $495 – $990   | Industry norm in BC is $500–895    |
| Preparation / PDI            | $0 – $700     | Often separate line                |
| Tire / road hazard           | $0 – $1,500   | Optional but pushed; often refusable |
| Weather package              | $0 – $2,000   | Mostly markup; aim to refuse        |
| Dash cam                     | $0 – $600     | Dealer-installed; aftermarket cheaper |
| Acquisition / origination    | $0 – $295     | Only if financing through dealer   |

Toyota Canada freight (and most OEM freight) is **not** negotiable — fixed
by the manufacturer across all dealers in Canada.

GST and PST also apply to:
- Air Conditioning Tax ($100 — federal excise on AC, mandatory)
- Tire Levy ($30–35 — provincial)

## Reference implementation

The all-in calculator lives in `vehicle-app/app.py`:

```python
def _bc_pst_rate(sale_price): ...
def _bc_all_in(sale_price, license_fee=50): ...
```

For non-BC deployments, replace the function body with the local tax
schedule. Keep the function name so callers don't have to change.
