"""
03_risk_return.py
-----------------
Turn the PD score into a portfolio decision. Instead of trusting the model's
raw probabilities (which are rank-accurate but not calibrated because we
class-weighted the trainer), we bucket the book into PD deciles and use the
EMPIRICAL default rate in each decile — calibrated by construction and the
way scorecards are actually cut into risk bands in industry.

For each decile we run the same unit-economics as sql/04, then simulate a
policy: "decline the riskiest deciles" and measure the profit lift.

Run: python src/03_risk_return.py
Outputs: reports/risk_return_deciles.csv, reports/policy_simulation.json,
         reports/figures/decile_profit.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Economics assumptions (identical to sql/04_risk_return_pricing.sql).
LGD = 0.90
APR = 0.22
SERVICING = 120.0


def main():
    df = pd.read_csv(ROOT / "data" / "scored_accounts.csv")

    # Rank into 10 risk bands by predicted PD (band 1 = safest).
    df["risk_decile"] = pd.qcut(df["pd_hat"], 10, labels=False, duplicates="drop") + 1

    g = df.groupby("risk_decile")
    tbl = pd.DataFrame({
        "accounts": g.size(),
        "empirical_pd": g["default_next_month"].mean(),
        "avg_exposure": g["current_balance"].mean(),
    }).reset_index()

    tbl["expected_loss"] = tbl["empirical_pd"] * tbl["avg_exposure"] * LGD
    tbl["expected_revenue"] = APR * tbl["avg_exposure"]
    tbl["profit_per_acct"] = tbl["expected_revenue"] - tbl["expected_loss"] - SERVICING
    tbl["total_profit"] = tbl["profit_per_acct"] * tbl["accounts"]
    tbl["breakeven_apr"] = (tbl["expected_loss"] + SERVICING) / tbl["avg_exposure"].where(tbl["avg_exposure"] > 0)
    tbl = tbl.round({"empirical_pd": 4, "avg_exposure": 0, "expected_loss": 0,
                     "expected_revenue": 0, "profit_per_acct": 0, "total_profit": 0,
                     "breakeven_apr": 4})
    tbl.to_csv(ROOT / "reports" / "risk_return_deciles.csv", index=False)

    # --- Policy simulation: decline deciles that lose money at current APR -----
    baseline_profit = tbl["total_profit"].sum()
    keep = tbl[tbl["profit_per_acct"] > 0]
    declined = tbl[tbl["profit_per_acct"] <= 0]
    policy_profit = keep["total_profit"].sum()

    sim = {
        "current_apr": APR,
        "baseline_total_profit": float(baseline_profit),
        "declined_deciles": declined["risk_decile"].tolist(),
        "accounts_declined": int(declined["accounts"].sum()),
        "pct_book_declined": round(100 * declined["accounts"].sum() / tbl["accounts"].sum(), 1),
        "profit_after_policy": float(policy_profit),
        "profit_lift": float(policy_profit - baseline_profit),
        "profit_lift_pct": round(100 * (policy_profit - baseline_profit) / abs(baseline_profit), 1),
    }
    (ROOT / "reports" / "policy_simulation.json").write_text(json.dumps(sim, indent=2))

    # --- Figure --------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = ["#59A14F" if p > 0 else "#E15759" for p in tbl["profit_per_acct"]]
    ax.bar(tbl["risk_decile"], tbl["profit_per_acct"], color=colors)
    ax.axhline(0, color="k", lw=0.8)
    ax.set_xlabel("Risk decile (1 = safest, 10 = riskiest)")
    ax.set_ylabel("Expected profit per account (NT$)")
    ax.set_title(f"Unit economics by risk band @ {APR:.0%} APR")
    plt.tight_layout(); plt.savefig(ROOT / "reports" / "figures" / "decile_profit.png", dpi=120)

    print(tbl.to_string(index=False))
    print("\nPolicy simulation:")
    print(json.dumps(sim, indent=2))


if __name__ == "__main__":
    main()
