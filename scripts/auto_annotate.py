"""
auto_annotate.py
----------------
Fills in Notes, Income Source, and Category for all known transactions.
Run this any time you add new rules or people.
Then rerun import_to_sqlite.py to update the database.

Usage:
    python scripts/auto_annotate.py
"""

import pandas as pd
from pathlib import Path

BASE_DIR  = Path(__file__).parent.parent
XLSX_PATH = BASE_DIR / "clean_data" / "MASTER_DATA.xlsx"

# ── 1. Person rules ────────────────────────────────────────────────────────────
# Matched against Payee column (case-insensitive contains)
# exclude = True → internal transfer, excluded from summaries

PERSON_RULES = {

    # Your own accounts
    "NATANEM ABEBE":      {"note": "My own account — internal transfer", "income_src": "Internal",      "exclude": True},
    "NATANEM ABEB":       {"note": "My own account — internal transfer", "income_src": "Internal",      "exclude": True},
    "CASH APP NATANEM":   {"note": "My own account — internal transfer", "income_src": "Internal",      "exclude": True},
    "ZELLE SENT REFUND":  {"note": "Zelle refund — internal",            "income_src": "Internal",      "exclude": True},

    # Family
    "BIRHANU GEBIREMES":  {"note": "Dad",                  "income_src": "Family",        "exclude": False},
    "AMSALE BELETE":      {"note": "Mom",                  "income_src": "Family",        "exclude": False},
    "AMSALE BELET":       {"note": "Mom",                  "income_src": "Family",        "exclude": False},
    "EDEN ABEBE":         {"note": "Family member",        "income_src": "Family",        "exclude": False},
    "HANIEBAL GEBRIE":    {"note": "Family member",        "income_src": "Family",        "exclude": False},
    "AMENKUGNE":          {"note": "Dad's friend — money from dad via Ethiopia", "income_src": "Family", "exclude": False},

    # Best friends / smoking
    "EJAAZ KEREM":        {"note": "Best friend / smoking", "income_src": "Reimbursement", "exclude": False},
    "ZWE AUNG":           {"note": "Best friend / smoking", "income_src": "Reimbursement", "exclude": False},
    "SU KHAING":          {"note": "Best friend / smoking", "income_src": "Reimbursement", "exclude": False},
    "MIO MAHONEY":        {"note": "Friend / smoking / plug","income_src": "Reimbursement", "exclude": False},

    # Best friends
    "DANIEL FARRELL":     {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "DANIEL FARRE":       {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "DAGMAWI MOHAMMED":   {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "DAGMAWI MOHA":       {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "FITSUM MOHAMMED":    {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "NAOL ANBESE":        {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "YOUNAEL ABUNE":      {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "SAMSON SHOBENO":     {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "ALAZAR ASCHALEW":    {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "KALEB TSEGAY":       {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "RICHARD RIVERA":     {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "RICHARD RIVER":      {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},
    "Rich D":             {"note": "Best friend",           "income_src": "Reimbursement", "exclude": False},

    # Frat friends
    "DENIZHAN CITIROGLU": {"note": "Frat friend",           "income_src": "Reimbursement", "exclude": False},
    "DENIZHAN CITIR":     {"note": "Frat friend",           "income_src": "Reimbursement", "exclude": False},
    "LIAM JUDD":          {"note": "Frat friend",           "income_src": "Reimbursement", "exclude": False},
    "AUSTIN TOMPKIN":     {"note": "Frat friend",           "income_src": "Reimbursement", "exclude": False},
    "JOHN BOLDS":         {"note": "Frat friend",           "income_src": "Reimbursement", "exclude": False},

    # Friends
    "GIANNI LUBITZ":      {"note": "Friend",                "income_src": "Reimbursement", "exclude": False},
    "GIANNI LUBIT":       {"note": "Friend",                "income_src": "Reimbursement", "exclude": False},
    "MARK STAFFORD":      {"note": "Friend",                "income_src": "Reimbursement", "exclude": False},
    "DONAE MILLER":       {"note": "Friend",                "income_src": "Reimbursement", "exclude": False},
    "MARTA MARTINEZ":     {"note": "Friend / plug",         "income_src": "Reimbursement", "exclude": False},
    "MARTA MARTIN":       {"note": "Friend / plug",         "income_src": "Reimbursement", "exclude": False},
    "EMMANUEL MOSCOSO":   {"note": "Frat friend / plug",    "income_src": "Reimbursement", "exclude": False},
    "NICHOLAS FIORIO":    {"note": "Frat friend / plug",    "income_src": "Reimbursement", "exclude": False},
    "NICHOLAS FIORI":     {"note": "Frat friend / plug",    "income_src": "Reimbursement", "exclude": False},
    "JORDY PARADA":       {"note": "Friend",                "income_src": "Reimbursement", "exclude": False},
    "JESSE GRABER":       {"note": "Friend — bought beer",  "income_src": "Reimbursement", "exclude": False},
    "JEREMY BRAVO":       {"note": "Friend — bought beer",  "income_src": "Reimbursement", "exclude": False},
    "SHIRELL THOMAS":     {"note": "Unknown",               "income_src": "Reimbursement", "exclude": False},
    "REEM MUZEYEN":       {"note": "Sister's friend — graduation", "income_src": "Reimbursement", "exclude": False},

    # Plugs
    "JOSHUA LLANOS":      {"note": "Plug",                  "income_src": "Reimbursement", "exclude": False},
    "JOSHUA LLANO":       {"note": "Plug",                  "income_src": "Reimbursement", "exclude": False},
    "ABRAHAM BERHANE":    {"note": "Plug",                  "income_src": "Reimbursement", "exclude": False},
    "ABRAHAM BERH":       {"note": "Plug",                  "income_src": "Reimbursement", "exclude": False},
    "MARQUIS O'NEAL":     {"note": "Plug",                  "income_src": "Reimbursement", "exclude": False},
}

# ── 2. Payment method rules ────────────────────────────────────────────────────
# Applied to all matching rows where Notes is blank or Needs Review

VENDOR_NOTES = {
    "Cash App":          "Weed",
    "Apple Cash (Sent)": "Weed",
    "Venmo":             "Frat & Social",
}

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Reading {XLSX_PATH} ...")
df = pd.read_excel(XLSX_PATH, sheet_name="MASTER_DATA", engine="openpyxl")
df.columns = [c.strip() for c in df.columns]
print(f"  Loaded {len(df):,} rows")

if "Notes" not in df.columns:
    df["Notes"] = ""
if "Income Source" not in df.columns:
    df["Income Source"] = ""

df["Notes"]         = df["Notes"].fillna("").astype(str)
df["Income Source"] = df["Income Source"].fillna("").astype(str)
df["Amount"]        = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)

# ── 3. Min Maw rent vs smoking split ──────────────────────────────────────────
# Done first so person rules don't overwrite it
rent_updated = 0
for i, row in df.iterrows():
    payee  = str(row["Payee"]).upper() if pd.notna(row["Payee"]) else ""
    amount = row["Amount"]

    if "MIN MAW" not in payee and "MIN PHONE MAW" not in payee:
        continue

    if amount <= -250:
        df.at[i, "Notes"]    = "Rent — Min Maw"
        df.at[i, "Category"] = "Bills & Utilities"
    elif amount >= 0:
        df.at[i, "Notes"] = "Best friend / smoking — change"
    else:
        df.at[i, "Notes"] = "Best friend / smoking"
    rent_updated += 1

# ── 4. Apply person rules ──────────────────────────────────────────────────────
# Skip Min Maw rows already handled above
person_updated = 0
for i, row in df.iterrows():
    payee    = str(row["Payee"]).upper() if pd.notna(row["Payee"]) else ""
    txn_type = str(row["Type"])          if pd.notna(row["Type"])  else ""
    note     = df.at[i, "Notes"]

    # Skip already annotated by rent logic
    if "Min Maw" in note:
        continue

    for person, rules in PERSON_RULES.items():
        if person.upper() not in payee:
            continue

        if rules["exclude"]:
            df.at[i, "Notes"] = "Internal transfer — excluded from summaries"
        else:
            df.at[i, "Notes"] = rules["note"]

        if txn_type == "Income":
            df.at[i, "Income Source"] = rules["income_src"]

        person_updated += 1
        break

# ── 5. Apply vendor/payment method rules ───────────────────────────────────────
vendor_updated = 0
for i, row in df.iterrows():
    vendor       = str(row["Cleaned Vendor"]) if pd.notna(row["Cleaned Vendor"]) else ""
    current_note = df.at[i, "Notes"]

    if vendor in VENDOR_NOTES and current_note in ("", "Needs Review"):
        df.at[i, "Notes"] = VENDOR_NOTES[vendor]
        vendor_updated += 1

# ── 6. Save ────────────────────────────────────────────────────────────────────
df.to_excel(XLSX_PATH, sheet_name="MASTER_DATA", index=False, engine="openpyxl")

# ── 7. Summary ─────────────────────────────────────────────────────────────────
still_needs_review = (df["Notes"] == "Needs Review").sum()
internal           = df["Notes"].str.contains("Internal transfer", na=False).sum()
rent_rows          = df["Notes"].str.contains("Rent — Min Maw", na=False).sum()
total_annotated    = (df["Notes"] != "").sum()

print(f"\n── Summary ───────────────────────────────────────────────────")
print(f"  Rent rows identified:           {rent_rows}")
print(f"  Person rules applied:           {person_updated}")
print(f"  Vendor rules applied:           {vendor_updated}")
print(f"  Internal transfers marked:      {internal}")
print(f"  Still needs manual review:      {still_needs_review}")
print(f"  Total annotated:                {total_annotated}")
print(f"\n  Saved to {XLSX_PATH}")

if still_needs_review > 0:
    print(f"\n  {still_needs_review} rows still need review — filter Notes = 'Needs Review' in Excel.")
else:
    print(f"\n  All done! Run import_to_sqlite.py to update the database.")
