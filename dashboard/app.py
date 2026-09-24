"""
Credit Portfolio Analytics — dashboard
--------------------------------------
An executive view a product/credit team would actually open: portfolio health,
where risk concentrates, the unit-economics by risk band, and the customer
segments. Reads the same SQLite DB and report CSVs the analysis produced.

Run: streamlit run dashboard/app.py
"""

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "credit.db"
REPORTS = ROOT / "reports"

st.set_page_config(page_title="Credit Portfolio Analytics", layout="wide")


@st.cache_data
def load():
    con = sqlite3.connect(DB)
    acc = pd.read_sql_query("SELECT * FROM accounts", con)
    con.close()
    return acc


acc = load()

st.title("Credit Portfolio Analytics")
st.caption("Consumer credit book — risk, unit economics, and segmentation. "
           "Illustrative data (UCI Default of Credit Card Clients, NT$).")

# --- Sidebar filter ----------------------------------------------------------
grade = st.sidebar.multiselect("Risk grade", sorted(acc["risk_grade"].unique()),
                               default=sorted(acc["risk_grade"].unique()))
view = acc[acc["risk_grade"].isin(grade)]

# --- Headline KPIs -----------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Accounts", f"{len(view):,}")
c2.metric("Default rate", f"{view['default_next_month'].mean():.1%}")
c3.metric("Avg credit limit", f"{view['credit_limit'].mean():,.0f}")
c4.metric("Avg utilization", f"{view['utilization'].mean():.0%}")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Default rate by risk grade")
    by_grade = (view.groupby("risk_grade")["default_next_month"]
                .agg(["mean", "size"]).rename(columns={"mean": "default_rate", "size": "accounts"}))
    st.bar_chart(by_grade["default_rate"])
    st.dataframe(by_grade.style.format({"default_rate": "{:.1%}", "accounts": "{:,}"}))

with right:
    st.subheader("Default rate by credit-limit tier")
    by_tier = view.groupby("limit_tier")["default_next_month"].mean()
    st.bar_chart(by_tier)

st.divider()
st.subheader("Unit economics by risk decile  @ 22% APR")
if (REPORTS / "risk_return_deciles.csv").exists():
    dec = pd.read_csv(REPORTS / "risk_return_deciles.csv")
    st.bar_chart(dec.set_index("risk_decile")["profit_per_acct"])
    st.dataframe(dec)
    st.image(str(REPORTS / "figures" / "decile_profit.png"))
else:
    st.info("Run src/03_risk_return.py to generate decile economics.")

st.divider()
st.subheader("Customer segments")
if (REPORTS / "segments.csv").exists():
    seg = pd.read_csv(REPORTS / "segments.csv")
    st.dataframe(seg)
    st.image(str(REPORTS / "figures" / "segments.png"))
else:
    st.info("Run src/04_segmentation.py to generate segments.")
