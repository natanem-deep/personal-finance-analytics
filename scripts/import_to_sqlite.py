"""
import_to_sqlite.py
-------------------
Reads MASTER_DATA from your Excel file and loads it into finance.db (SQLite).
Run this any time you update the Excel file to keep the database in sync.

Usage:
    python scripts/import_to_sqlite.py

Requirements:
    pip install pandas openpyxl
"""

import sqlite3
import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = Path(__file__).parent.parent        # finance_project/ root
XLSX_PATH = BASE_DIR / "clean_data" / "MASTER_DATA.xlsx"
DB_PATH   = BASE_DIR / "database"  / "finance.db"

# ── 1. Load Excel ──────────────────────────────────────────────────────────────
print(f"Reading {XLSX_PATH} ...")
df = pd.read_excel(XLSX_PATH, sheet_name="MASTER_DATA", engine="openpyxl")

# ── 2. Fix column names ────────────────────────────────────────────────────────
df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
# Result: date, payee, address, amount, account, month, cleaned_vendor, category, type

print(f"  Loaded {len(df):,} rows")
print(f"  Columns: {list(df.columns)}")

# ── 3. Fix dates (Excel stores them as serial numbers like 45404) ──────────────
# pd.read_excel with openpyxl usually handles this automatically,
# but if your date column still looks like integers, this line fixes it:
if df["date"].dtype in ["int64", "float64"]:
    df["date"] = pd.to_datetime(df["date"], unit="D", origin="1899-12-30")
else:
    df["date"] = pd.to_datetime(df["date"])

df["date"] = df["date"].dt.strftime("%Y-%m-%d")   # store as clean string: 2024-04-01
print(f"  Date range: {df['date'].min()} → {df['date'].max()}")

# ── 4. Clean amount column ─────────────────────────────────────────────────────
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

# ── 5. Connect to SQLite ───────────────────────────────────────────────────────
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(DB_PATH)
print(f"\nConnected to {DB_PATH}")

# ── 6. Write transactions table ────────────────────────────────────────────────
df.to_sql("transactions", conn, if_exists="replace", index=False)
print(f"  Wrote {len(df):,} rows to table 'transactions'")

# ── 7. Create views ────────────────────────────────────────────────────────────
views = {
    "monthly_summary": """
        SELECT
            month,
            category,
            SUM(amount)   AS total,
            COUNT(*)      AS num_transactions
        FROM transactions
        WHERE type = 'Expense' AND cleaned_vendor NOT IN ('Transfer to Savings', 'Internal Transfer')
        GROUP BY month, category
        ORDER BY month, total ASC
    """,

    "top_vendors": """
        SELECT
            cleaned_vendor,
            category,
            SUM(amount)   AS total_spent,
            COUNT(*)      AS num_transactions
        FROM transactions
        WHERE type = 'Expense' AND cleaned_vendor NOT IN ('Transfer to Savings', 'Internal Transfer')
        GROUP BY cleaned_vendor
        ORDER BY total_spent ASC
        LIMIT 25
    """,

    "category_summary": """
        SELECT
            category,
            SUM(amount)   AS total_spent,
            COUNT(*)      AS num_transactions,
            ROUND(AVG(amount), 2) AS avg_transaction
        FROM transactions
        WHERE type = 'Expense' AND cleaned_vendor NOT IN ('Transfer to Savings', 'Internal Transfer')
        GROUP BY category
        ORDER BY total_spent ASC
    """,

    "income_vs_expenses": """
        SELECT
            month,
            SUM(CASE WHEN type = 'Income' AND cleaned_vendor NOT IN ('Transfer to Savings', 'Internal Transfer') THEN amount ELSE 0 END) AS income,
            SUM(CASE WHEN type = 'Expense' AND cleaned_vendor NOT IN ('Transfer to Savings', 'Internal Transfer') THEN amount ELSE 0 END) AS expenses
        FROM transactions
        GROUP BY month
        ORDER BY month
    """,
}

for view_name, view_sql in views.items():
    conn.execute(f"DROP VIEW IF EXISTS {view_name}")
    conn.execute(f"CREATE VIEW {view_name} AS {view_sql}")
    print(f"  Created view: {view_name}")

conn.commit()

# ── 8. Sanity check ────────────────────────────────────────────────────────────
print("\n── Sanity check ──────────────────────────────────────────────")
row_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
print(f"  transactions table: {row_count:,} rows")

print("\n  Sample (5 rows):")
sample = pd.read_sql("SELECT date, cleaned_vendor, amount, category, type FROM transactions LIMIT 5", conn)
print(sample.to_string(index=False))

print("\n  Income vs Expenses (first 5 months):")
summary = pd.read_sql("SELECT * FROM income_vs_expenses LIMIT 5", conn)
print(summary.to_string(index=False))

conn.close()
print("\nDone. finance.db is ready.")
