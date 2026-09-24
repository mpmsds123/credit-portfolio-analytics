"""
04_segmentation.py
------------------
Behavioral user segmentation (KMeans) — the JD asks explicitly for "user
segmentation". We cluster accounts on behavior/financials (NOT protected
attributes), then profile each segment on the metrics a product team cares
about: size, default rate, utilization, and profitability. The point is a
small set of named, actionable customer archetypes, not clusters for their
own sake.

Run: python src/04_segmentation.py
Outputs: reports/segments.csv, reports/figures/segments.png
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]

CLUSTER_FEATURES = ["utilization", "payment_ratio", "max_delinquency",
                    "months_delinquent", "credit_limit"]
K = 4  # four archetypes keeps the story presentable to leadership
APR, LGD, SERVICING = 0.22, 0.90, 120.0


def main():
    df = pd.read_csv(ROOT / "data" / "scored_accounts.csv")
    Xs = StandardScaler().fit_transform(df[CLUSTER_FEATURES])
    df["segment"] = KMeans(n_clusters=K, n_init=10, random_state=42).fit_predict(Xs)

    prof = df.groupby("segment").agg(
        accounts=("account_id", "size"),
        default_rate=("default_next_month", "mean"),
        avg_utilization=("utilization", "mean"),
        avg_payment_ratio=("payment_ratio", "mean"),
        avg_limit=("credit_limit", "mean"),
        avg_balance=("current_balance", "mean"),
    ).reset_index()
    prof["profit_per_acct"] = (APR * prof["avg_balance"]
                               - prof["default_rate"] * prof["avg_balance"] * LGD
                               - SERVICING)

    # Auto-name archetypes from their profile so the labels are defensible.
    # Mutually exclusive rules, checked in priority order, so the four clusters
    # get four distinct, defensible names.
    def name(r):
        if r["default_rate"] > 0.35:
            return "Distressed (high default, reprice/exit)"
        if r["avg_payment_ratio"] > 0.6:
            return "Transactors (pay-in-full, low balance)"
        if r["avg_utilization"] > 0.5:
            return "Revolvers (carry balance, profitable)"
        return "Prime (high limit, low utilization)"

    prof["archetype"] = prof.apply(name, axis=1)
    prof = prof.round({"default_rate": 4, "avg_utilization": 3, "avg_payment_ratio": 3,
                       "avg_limit": 0, "avg_balance": 0, "profit_per_acct": 0})
    prof.to_csv(ROOT / "reports" / "segments.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 5))
    sizes = prof["accounts"] / prof["accounts"].max() * 900 + 100
    sc = ax.scatter(prof["avg_utilization"], prof["default_rate"],
                    s=sizes, c=prof["profit_per_acct"], cmap="RdYlGn", edgecolor="k")
    for _, r in prof.iterrows():
        ax.annotate(r["archetype"].split(" (")[0],
                    (r["avg_utilization"], r["default_rate"]),
                    fontsize=8, ha="center", va="bottom")
    ax.set_xlabel("Avg utilization"); ax.set_ylabel("Default rate")
    ax.set_title("Customer segments (bubble = size, color = profit/acct)")
    plt.colorbar(sc, label="Profit per account (NT$)")
    plt.tight_layout(); plt.savefig(ROOT / "reports" / "figures" / "segments.png", dpi=120)

    print(prof.to_string(index=False))


if __name__ == "__main__":
    main()
