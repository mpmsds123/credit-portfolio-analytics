"""
00_build_database.py
--------------------
Load the raw UCI "Default of Credit Card Clients" CSV into a clean SQLite
database and engineer the behavioral features the rest of the analysis uses.

Why SQLite: it lets the whole project run with zero setup (no server), while
the analysis is still written in real SQL (sql/*.sql) exactly as it would be
against a production warehouse like Snowflake/BigQuery. Swap the connection
string and the same queries run against a warehouse.

Run:  python src/00_build_database.py
Output: data/credit.db  (tables: accounts_raw, accounts)
"""

import sqlite3
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
CSV_PATH = DATA_DIR / "UCI_Credit_Card.csv"
DB_PATH = DATA_DIR / "credit.db"

# --- Column dictionary (see README) -----------------------------------------
# PAY_0..PAY_6 : repayment status for Sep..Apr. -2/-1/0 = paid or no balance,
#                1..9 = number of months the payment is past due.
# BILL_AMT1..6 : bill statement amount (NT$) for Sep..Apr.
# PAY_AMT1..6  : amount actually paid (NT$) for Sep..Apr.
# default.payment.next.month : 1 = defaulted next month, 0 = did not.


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    # The public mirror sometimes names the target with a dot; normalize it.
    df = df.rename(columns={"default.payment.next.month": "default_next_month",
                            "PAY_0": "PAY_1"})  # PAY_0 is Sept; rename to PAY_1 for a clean 1..6 sequence
    return df


def engineer(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame()
    out["account_id"] = df["ID"]
    out["credit_limit"] = df["LIMIT_BAL"]
    out["age"] = df["AGE"]

    # Protected attributes are kept ONLY for population/fairness monitoring,
    # never fed to the risk model (see src/02_default_model.py and the
    # fair-lending note in the README).
    out["sex"] = df["SEX"].map({1: "male", 2: "female"})
    out["education"] = df["EDUCATION"].map(
        {1: "grad_school", 2: "university", 3: "high_school", 4: "other"}
    ).fillna("unknown")
    out["marriage"] = df["MARRIAGE"].map(
        {1: "married", 2: "single", 3: "other"}
    ).fillna("unknown")

    pay_cols = [f"PAY_{i}" for i in range(1, 7)]
    bill_cols = [f"BILL_AMT{i}" for i in range(1, 7)]
    amt_cols = [f"PAY_AMT{i}" for i in range(1, 7)]

    # --- Behavioral / financial features (these ARE allowed for underwriting) --
    # Worst delinquency observed over the 6-month window.
    out["max_delinquency"] = df[pay_cols].max(axis=1)
    # How many of the 6 months the account was past due (PAY >= 1).
    out["months_delinquent"] = (df[pay_cols] >= 1).sum(axis=1)
    # Most recent bill (Sept) as the current exposure proxy.
    out["current_balance"] = df["BILL_AMT1"]
    out["avg_bill"] = df[bill_cols].mean(axis=1)
    out["avg_payment"] = df[amt_cols].mean(axis=1)

    # Utilization = current balance / credit limit. Capped at 1.5 to tame a few
    # accounts billed above their limit; clipped at 0 (some bills are negative
    # from refunds/credits).
    util = (df["BILL_AMT1"] / df["LIMIT_BAL"]).clip(lower=0, upper=1.5)
    out["utilization"] = util

    # Payment ratio = paid / billed over the window. 1.0+ means they pay in full.
    total_bill = df[bill_cols].sum(axis=1)
    total_paid = df[amt_cols].sum(axis=1)
    out["payment_ratio"] = (total_paid / total_bill.where(total_bill > 0)).clip(0, 2).fillna(1.0)

    out["default_next_month"] = df["default_next_month"]

    # --- Business segmentation buckets (used all over the SQL layer) ----------
    out["limit_tier"] = pd.cut(
        out["credit_limit"],
        bins=[0, 50_000, 140_000, 300_000, 10_000_000],
        labels=["Tier1_<50k", "Tier2_50-140k", "Tier3_140-300k", "Tier4_300k+"],
    ).astype(str)

    out["util_band"] = pd.cut(
        out["utilization"],
        bins=[-0.01, 0.10, 0.30, 0.60, 1.6],
        labels=["0-10%", "10-30%", "30-60%", "60%+"],
    ).astype(str)

    # Behavioral risk grade from delinquency history — this is the underwriting
    # spine of the whole analysis.
    def grade(row):
        if row["max_delinquency"] <= 0:
            return "A_current"
        if row["max_delinquency"] == 1:
            return "B_1mo_late"
        if row["max_delinquency"] == 2:
            return "C_2mo_late"
        return "D_3mo+_late"

    out["risk_grade"] = out.apply(grade, axis=1)
    return out


def main() -> None:
    raw = pd.read_csv(CSV_PATH)
    feat = engineer(load_raw())

    con = sqlite3.connect(DB_PATH)
    raw.to_sql("accounts_raw", con, if_exists="replace", index=False)
    feat.to_sql("accounts", con, if_exists="replace", index=False)
    con.commit()

    n, d = feat.shape[0], feat["default_next_month"].mean()
    print(f"Built {DB_PATH}")
    print(f"  accounts: {n:,} rows, {feat.shape[1]} columns")
    print(f"  portfolio default rate: {d:.2%}")
    con.close()


if __name__ == "__main__":
    main()
