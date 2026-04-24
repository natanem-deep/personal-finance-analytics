"""
add_annotation_columns.py
--------------------------
Adds 'Notes' and 'Income Source' columns to your MASTER_DATA.xlsx.
- Flags person-to-person transactions as 'Needs Review'
- Auto-fills known family senders as 'Family' in Income Source
- Auto-fills known earned/reimbursement patterns where possible

Run ONCE to add the columns. After that, fill in the 'Needs Review' rows manually in Excel.

Usage:
    python scripts/add_annotation_columns.py

Requirements:
    pip install pandas openpyxl
"""

import pandas as pd
from pathlib import Path

BASE_DIR  = Path(__file__).parent.parent
XLSX_PATH = BASE_DIR / "clean_data" / "MASTER_DATA.xlsx"

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Reading {XLSX_PATH} ...")
df = pd.read_excel(XLSX_PATH, sheet_name="MASTER_DATA", engine="openpyxl")
df.columns = [c.strip() for c in df.columns]  # preserve original casing
print(f"  Loaded {len(df):,} rows")

# ── Skip if columns already exist ─────────────────────────────────────────────
if "Notes" not in df.columns:
    df["Notes"] = ""
else:
    print("  'Notes' column already exists — will only fill empty cells")

if "Income Source" not in df.columns:
    df["Income Source"] = ""
else:
    print("  'Income Source' column already exists — will only fill empty cells")

# ── Person-to-person vendors that need manual review ──────────────────────────
REVIEW_VENDORS = [
    "Zelle (Sent)",
    "Zelle (Received)",
    "Venmo",
    "Apple Cash (Sent)",
    "Cash App",
]

# ── Known family members (Zelle received from these = Family income) ───────────
# Add more names here if needed
FAMILY_NAMES = [
    "BIRHANU GEBIREMES",   # dad
    "AMSALE BELETE",        # add other family members here
]

# ── Known internal transfers to always exclude ─────────────────────────────────
INTERNAL_TRANSFERS = [
    "Transfer to Savings",
    "Internal Transfer",
]

# ── Apply Notes flags ──────────────────────────────────────────────────────────
vendor_col = "Cleaned Vendor"
payee_col  = "Payee"

for i, row in df.iterrows():
    vendor = str(row[vendor_col]) if pd.notna(row[vendor_col]) else ""
    payee  = str(row[payee_col])  if pd.notna(row[payee_col])  else ""
    notes  = str(row["Notes"])    if pd.notna(row["Notes"])    else ""

    # Skip rows that already have notes
    if notes.strip():
        continue

    if vendor in INTERNAL_TRANSFERS:
        df.at[i, "Notes"] = "Internal transfer — excluded from summaries"

    elif vendor in REVIEW_VENDORS:
        df.at[i, "Notes"] = "Needs Review"

# ── Apply Income Source ────────────────────────────────────────────────────────
for i, row in df.iterrows():
    vendor       = str(row[vendor_col])       if pd.notna(row[vendor_col])       else ""
    payee        = str(row[payee_col])         if pd.notna(row[payee_col])         else ""
    txn_type     = str(row["Type"])            if pd.notna(row["Type"])            else ""
    income_src   = str(row["Income Source"])   if pd.notna(row["Income Source"])   else ""

    if income_src.strip():
        continue

    if txn_type != "Income":
        continue

    # Check if payee contains a known family name
    is_family = any(name.upper() in payee.upper() for name in FAMILY_NAMES)

    if is_family:
        df.at[i, "Income Source"] = "Family"
    elif vendor in ("Zelle (Received)", "Venmo", "Apple Cash (Sent)"):
        df.at[i, "Income Source"] = "Needs Review"
    else:
        df.at[i, "Income Source"] = "Earned"

# ── Save back to Excel ─────────────────────────────────────────────────────────
df.to_excel(XLSX_PATH, sheet_name="MASTER_DATA", index=False, engine="openpyxl")
print(f"\nSaved to {XLSX_PATH}")

# ── Summary ────────────────────────────────────────────────────────────────────
needs_review = (df["Notes"] == "Needs Review").sum()
family_income = (df["Income Source"] == "Family").sum()
earned_income = (df["Income Source"] == "Earned").sum()
income_review = (df["Income Source"] == "Needs Review").sum()

print(f"\n── Summary ───────────────────────────────────────────────────")
print(f"  Transactions flagged 'Needs Review' in Notes: {needs_review}")
print(f"  Income rows auto-filled as 'Family':          {family_income}")
print(f"  Income rows auto-filled as 'Earned':          {earned_income}")
print(f"  Income rows flagged 'Needs Review':            {income_review}")
print(f"\nNext step: Open MASTER_DATA.xlsx in Excel, filter Notes = 'Needs Review'")
print(f"and fill in what each transaction was for. Then rerun import_to_sqlite.py.")
