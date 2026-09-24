# Executive Summary — Credit Portfolio Risk & Pricing Review

**Audience:** Credit product leadership · **Prepared by:** Portfolio Analytics
**Data:** 30,000-account consumer credit book (illustrative; UCI Default of Credit Card Clients, NT$)

---

## The headline

The book carries a **22.1% next-month default rate**, but risk is highly
concentrated. **The riskiest 40% of accounts are unprofitable at the current
22% APR and drag total expected profit down by roughly two-thirds.** Declining
or repricing those accounts lifts modeled portfolio profit **+184%**
(NT$52.7M → NT$149.6M).

## What the data says

1. **Delinquency history is the dominant signal.** Accounts current on payments
   default 11.7% of the time; accounts already 3+ months late default 62.9%.
   The most recent month's status alone (September) separates a 12.8% cohort
   from a 69% cohort.

2. **Small, low-limit accounts are the loss center.** The under-50k limit tier
   defaults at 31.8% vs 13.3% for the 300k+ tier, and runs at 63% utilization —
   maxed-out, thin-file accounts.

3. **A behavioral scorecard ranks risk well.** An XGBoost model on
   behavior/financials only (no protected attributes) reaches **AUC 0.767,
   KS 0.41** — strong enough to cut the book into actionable risk bands.

4. **Four customer archetypes:**

   | Segment | Share | Default | Profit / acct | Action |
   |---|---|---|---|---|
   | Prime (high limit, low util) | 19% | 10% | +NT$9,963 | Grow / upsell |
   | Revolvers (carry balance) | 36% | 17% | +NT$4,997 | Core — protect |
   | Transactors (pay in full) | 27% | 17% | +NT$146 | Monetize via fees/interchange |
   | Distressed (high default) | 17% | 55% | −NT$14,153 | Reprice / exit |

## Recommendation

- **Reprice or decline the bottom 4 risk deciles** (break-even APR > 22%). Modeled profit lift **+184%**.
- **Grow Prime and protect Revolvers** — 55% of accounts, all profit-positive.
- **Do not underwrite on sex, marital status, or age** (ECOA/Reg B). The model
  is built to be fair-lending compliant; mean predicted PD differs <2pts by sex.

## Caveats

Single-currency illustrative dataset, one-month default horizon, and a
simplified unit-economics model (LGD 0.90, 22% blended APR, NT$120 servicing).
Assumptions are documented and swappable in `sql/04_risk_return_pricing.sql`.
Directional conclusions are robust to reasonable changes in these inputs.
