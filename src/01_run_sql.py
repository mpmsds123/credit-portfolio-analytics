"""
01_run_sql.py
-------------
Execute every file in sql/ against data/credit.db and print the results as
tidy tables. This is the "analyst's console" — it proves the SQL layer runs
and lets a reviewer see every business number without opening a notebook.

Run: python src/01_run_sql.py
"""

import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "credit.db"
SQL_DIR = ROOT / "sql"

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", 20)


def split_statements(text: str):
    # Drop comment-only lines, then split on ';'
    cleaned = "\n".join(l for l in text.splitlines() if not l.strip().startswith("--"))
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def main():
    con = sqlite3.connect(DB)
    for path in sorted(SQL_DIR.glob("*.sql")):
        print("\n" + "=" * 78)
        print(f"# {path.name}")
        print("=" * 78)
        for stmt in split_statements(path.read_text()):
            df = pd.read_sql_query(stmt, con)
            label = re.sub(r"\s+", " ", stmt[:70])
            print(f"\n-- {label}...")
            print(df.to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
