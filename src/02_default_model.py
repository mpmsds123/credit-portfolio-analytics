"""
02_default_model.py
-------------------
Predict probability of default (PD) from behavioral/financial features only,
then turn PD into an account-level approve/price decision.

Two deliberate choices a reviewer will ask about (answers in INTERVIEW_DEFENSE.md):
  1. Protected attributes (sex, marriage, age) are EXCLUDED from the model.
     Under US fair-lending law (ECOA/Reg B) these cannot drive credit
     decisions. We keep them aside only to test the model for disparate impact.
  2. We report AUC and KS (not just accuracy). On a 22% base-rate problem,
     accuracy is a trap — always predicting "no default" scores 78%.

Run: python src/02_default_model.py
Outputs: reports/model_metrics.json, reports/figures/*.png,
         data/scored_accounts.csv
"""

import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "credit.db"
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

# Features allowed for underwriting — behavior and financials only.
FEATURES = [
    "credit_limit", "utilization", "payment_ratio",
    "max_delinquency", "months_delinquent", "avg_bill", "avg_payment",
]
PROTECTED = ["sex", "marriage", "age"]  # held out of the model, used for fairness only
TARGET = "default_next_month"


def ks_statistic(y_true, y_score):
    """KS = max separation between the cumulative distributions of scores for
    defaulters vs non-defaulters. Standard credit-scorecard metric."""
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(tpr - fpr))


def main():
    con = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM accounts", con)
    con.close()

    X = df[FEATURES]
    y = df[TARGET]
    X_tr, X_te, y_tr, y_te, idx_tr, idx_te = train_test_split(
        X, y, df.index, test_size=0.30, random_state=42, stratify=y
    )

    # --- Model 1: Logistic regression (the interpretable baseline underwriters
    #     trust — each coefficient is a signed, explainable driver). ------------
    logit = Pipeline([("scale", StandardScaler()),
                      ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])
    logit.fit(X_tr, y_tr)
    p_logit = logit.predict_proba(X_te)[:, 1]

    # --- Model 2: XGBoost (captures the risk_grade x utilization interaction the
    #     SQL layer flagged; used as the production scorer). --------------------
    xgb = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.9, colsample_bytree=0.9, eval_metric="auc",
        scale_pos_weight=(y_tr == 0).sum() / (y_tr == 1).sum(), random_state=42,
    )
    xgb.fit(X_tr, y_tr)
    p_xgb = xgb.predict_proba(X_te)[:, 1]

    metrics = {
        "base_default_rate": float(y.mean()),
        "logistic": {"auc": float(roc_auc_score(y_te, p_logit)), "ks": ks_statistic(y_te, p_logit)},
        "xgboost": {"auc": float(roc_auc_score(y_te, p_xgb)), "ks": ks_statistic(y_te, p_xgb)},
    }

    # --- Fairness check: does the model score protected groups differently? ----
    fair = {}
    scored_te = df.loc[idx_te].copy()
    scored_te["pd_hat"] = p_xgb
    for col in ["sex", "marriage"]:
        grp = scored_te.groupby(col)["pd_hat"].mean().round(4).to_dict()
        fair[col] = grp
    metrics["fairness_mean_pd_by_group"] = fair

    (ROOT / "reports" / "model_metrics.json").write_text(json.dumps(metrics, indent=2))

    # --- Figure: ROC curves ----------------------------------------------------
    plt.figure(figsize=(5, 5))
    for name, p in [("Logistic", p_logit), ("XGBoost", p_xgb)]:
        fpr, tpr, _ = roc_curve(y_te, p)
        plt.plot(fpr, tpr, label=f"{name} (AUC={roc_auc_score(y_te, p):.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.4)
    plt.xlabel("False positive rate"); plt.ylabel("True positive rate")
    plt.title("Default model — ROC"); plt.legend()
    plt.tight_layout(); plt.savefig(FIG / "roc.png", dpi=120); plt.close()

    # --- Figure: feature importance --------------------------------------------
    imp = pd.Series(xgb.feature_importances_, index=FEATURES).sort_values()
    plt.figure(figsize=(6, 4))
    imp.plot.barh(color="#4C78A8")
    plt.title("XGBoost feature importance (PD)")
    plt.tight_layout(); plt.savefig(FIG / "feature_importance.png", dpi=120); plt.close()

    # --- Score the FULL book and save for the risk-return step -----------------
    df["pd_hat"] = xgb.predict_proba(X)[:, 1]
    df.to_csv(ROOT / "data" / "scored_accounts.csv", index=False)

    print("Model metrics:")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
