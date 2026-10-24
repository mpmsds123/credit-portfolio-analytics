# Credit Portfolio Analytics — Risk, Pricing & Segmentation

**An end-to-end business-analytics case study on a consumer credit book:** find
where risk concentrates, decide which accounts to approve and at what price, and
segment customers into actionable archetypes — delivered as SQL, a scored model,
a dashboard, and a one-page executive recommendation.

> Built to mirror the day-to-day of a consumer-credit business/strategy analyst:
> SQL on business metrics → risk-return / pricing model → user segmentation →
> dashboard + executive presentation.

**Headline result:** the riskiest 40% of the book is unprofitable at the current
22% APR; declining or repricing it lifts modeled portfolio profit **+184%**.
[Read the 1-page executive summary →](reports/EXECUTIVE_SUMMARY.md)
· [PDF version](reports/Executive_Summary.pdf)

---

## What's in here

| Layer | Files | What it does |
|---|---|---|
| **SQL analytics** | [`sql/`](sql/) | Portfolio health, segment default rates, delinquency migration, and a unit-economics/pricing model — all in auditable SQL |
| **Modeling** | [`src/02_default_model.py`](src/02_default_model.py) | PD model (logistic + XGBoost), AUC/KS, fair-lending check |
| **Risk-return** | [`src/03_risk_return.py`](src/03_risk_return.py) | Decile economics + a policy simulation (decline/reprice) |
| **Segmentation** | [`src/04_segmentation.py`](src/04_segmentation.py) | KMeans customer archetypes with profit profiles |
| **Dashboard** | [`dashboard/app.py`](dashboard/app.py) | Streamlit executive view |
| **Deliverable** | [`reports/`](reports/) | Executive summary (MD + PDF), figures, metrics |

## Key findings

- **Delinquency history dominates.** Current accounts default 11.7%; 3+ months
  late, 62.9%. The most recent month's status splits a 12.8% cohort from a 69% one.
- **Low-limit, maxed-out accounts are the loss center** — sub-50k tier defaults
  31.8% at 63% utilization vs 13.3% for the 300k+ tier.
- **A behavioral scorecard ranks risk well** — XGBoost **AUC 0.767, KS 0.41**,
  using no protected attributes.
- **Four customer archetypes** — Prime, Revolvers, Transactors, Distressed —
  with per-account profit from +NT$9,963 to −NT$14,153.

## Run it

```bash
pip install -r requirements.txt
python src/00_build_database.py     # CSV -> SQLite + engineered features
python src/01_run_sql.py            # runs every sql/*.sql and prints results
python src/02_default_model.py      # PD model, metrics, fairness check
python src/03_risk_return.py        # decile economics + policy simulation
python src/04_segmentation.py       # customer segments
python src/05_make_pdf.py           # one-page executive PDF
streamlit run dashboard/app.py      # interactive dashboard
```

## Fair-lending note

Sex, marital status, and age are **excluded from the model** — under US
fair-lending law (ECOA / Reg B) these cannot drive credit decisions. They are
retained only to test the model for disparate impact (mean predicted PD differs
2.05 points by sex: 41.37% female vs. 43.42% male). Underwriting features are behavioral/financial only.

## Data & assumptions

Illustrative public dataset: [UCI "Default of Credit Card Clients"](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients)
— 30,000 accounts, one-month default horizon, amounts in NT$. Unit economics use
LGD 0.90, 22% blended APR, NT$120/yr servicing; all assumptions are documented
and swappable in [`sql/04_risk_return_pricing.sql`](sql/04_risk_return_pricing.sql).
Conclusions are directional and robust to reasonable changes in these inputs.
