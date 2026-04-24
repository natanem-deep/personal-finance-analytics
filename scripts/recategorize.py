"""
recategorize.py
---------------
Fixes miscategorized transactions, especially those stuck in 'Other'.
Matches against Payee and Cleaned Vendor columns using keyword patterns.

Run this after auto_annotate.py.
Then rerun import_to_sqlite.py to update the database.

Usage:
    python scripts/recategorize.py
"""

import pandas as pd
from pathlib import Path

BASE_DIR  = Path(__file__).parent.parent
XLSX_PATH = BASE_DIR / "clean_data" / "MASTER_DATA.xlsx"

# ── Category rules ─────────────────────────────────────────────────────────────
# Each rule: (keyword, new_category, new_note or None)
# Matched case-insensitively against full Payee text
# First match wins

RULES = [
    # ── Subscriptions ──────────────────────────────────────────────────────────
    ("CHATGPT",           "Subscriptions",   None),
    ("OPENAI",            "Subscriptions",   None),
    ("PEACOCK",           "Subscriptions",   None),
    ("SIRIUSXM",          "Subscriptions",   None),
    ("HULU",              "Subscriptions",   None),
    ("ADOBE",             "Subscriptions",   None),
    ("SCRIBD",            "Subscriptions",   None),
    ("CODEBASICSI",       "Subscriptions",   "SQL course"),
    ("PRIME VIDEO",       "Subscriptions",   None),
    ("SPOTIFY",           "Subscriptions",   None),
    ("PATREON",           "Subscriptions",   None),
    ("PP*P33719",         "Subscriptions",   "Spotify"),
    ("PP*P341036",        "Subscriptions",   "Spotify"),
    ("PP*P34EE3",         "Subscriptions",   "Spotify"),
    ("PP*P35DB8",         "Subscriptions",   "Spotify"),
    ("PP*P36CAAD",        "Subscriptions",   "Spotify"),
    ("VSUBASTRO",         "Subscriptions",   "Astrology app"),
    ("SGT*V",             "Subscriptions",   "Astrology app"),
    ("SONY INTERACTIVE",  "Subscriptions",   "PlayStation"),
    ("PLAYSTATION",       "Subscriptions",   None),

    # ── Food & Dining ──────────────────────────────────────────────────────────
    ("PANERA",            "Food & Dining",   None),
    ("IHOP",              "Food & Dining",   None),
    ("FIVE GUYS",         "Food & Dining",   None),
    ("5GUYS",             "Food & Dining",   None),
    ("DOORDASH",          "Food & Dining",   None),
    ("WINGSTOP",          "Food & Dining",   None),
    ("PANDA EXPRESS",     "Food & Dining",   None),
    ("STARBUCKS",         "Food & Dining",   None),
    ("TACO",              "Food & Dining",   None),
    ("CAVA",              "Food & Dining",   None),
    ("ZEMETA",            "Food & Dining",   None),
    ("PIZZA",             "Food & Dining",   None),
    ("DENNY",             "Food & Dining",   None),
    ("CRUMBL",            "Food & Dining",   None),
    ("ROAMING ROOSTER",   "Food & Dining",   None),
    ("KENNEDY FRIED",     "Food & Dining",   None),
    ("FAMOUS ROTISSERIE", "Food & Dining",   None),
    ("FAMOUS FAMIGLIA",   "Food & Dining",   None),
    ("KAFFA",             "Food & Dining",   None),
    ("NYANMAR",           "Food & Dining",   None),
    ("DISTRICTTACO",      "Food & Dining",   None),
    ("Z BURGER",          "Food & Dining",   None),
    ("DOG HAUS",          "Food & Dining",   None),
    ("JENI'S",            "Food & Dining",   None),
    ("SUNNI TEEZ",        "Food & Dining",   None),
    ("ROOFTOP AT",        "Food & Dining",   None),
    ("MAYFLOWER REST",    "Food & Dining",   None),
    ("D.P.DOUGH",         "Food & Dining",   None),
    ("MOONLIGHT DELI",    "Food & Dining",   None),
    ("DAILY BAKERY",      "Food & Dining",   None),
    ("NORTHSIDE DELI",    "Food & Dining",   None),
    ("SOUTH WEDGE",       "Food & Dining",   None),
    ("LIVE ORGANIC",      "Food & Dining",   None),
    ("FIRST LOVE STORY",  "Food & Dining",   None),
    ("CAKE BAR",          "Food & Dining",   None),
    ("KFC",               "Food & Dining",   None),
    ("ZENE S DELI",       "Food & Dining",   None),
    ("THI CUISINE",       "Food & Dining",   None),
    ("JOHNNY S ROADSIDE", "Food & Dining",   None),
    ("BURGER KING",       "Food & Dining",   None),
    ("GARDENIA DELI",     "Food & Dining",   None),
    ("FOOTPRINTS CAFE",   "Food & Dining",   None),
    ("2LEVY DCUNI",       "Food & Dining",   "University food"),
    ("WONZONES",          "Food & Dining",   None),

    # ── Groceries ──────────────────────────────────────────────────────────────
    ("SAFEWAY",           "Groceries",       None),
    ("A AND A GROCERY",   "Groceries",       None),
    ("R CITY SUPER",      "Groceries",       None),
    ("NEW DODGE MARKET",  "Groceries",       None),
    ("ISLAND SMART",      "Groceries",       None),
    ("COSTCO",            "Groceries",       None),
    ("WHOLEFDS",          "Groceries",       None),
    ("WEGMANS",           "Groceries",       None),
    ("DOLLAR GENERAL",    "Groceries",       None),
    ("N & B COMPANY",     "Groceries",       "Corner store"),
    ("DAKOTA CONVENIENCE","Groceries",       None),
    ("MACS CONVENIENCE",  "Groceries",       None),
    ("01747 MACS",        "Groceries",       None),

    # ── Auto & Gas ─────────────────────────────────────────────────────────────
    ("EXXON",             "Auto & Gas",      None),
    ("EXXONMOBIL",        "Auto & Gas",      None),
    ("SHELL",             "Auto & Gas",      None),
    ("MARATHON",          "Auto & Gas",      None),
    ("SPEEDWAY",          "Auto & Gas",      None),
    ("CITGO",             "Auto & Gas",      None),
    ("HAYE A RECEIVER",   "Auto & Gas",      "Car purchase — 2 payments of $500"),
    ("DUNIFAB",           "Auto & Gas",      "Gas"),
    ("RIGGS RD MART",     "Auto & Gas",      None),
    ("FALCON FUEL",       "Auto & Gas",      None),
    ("AUTOZONE",          "Auto & Gas",      None),

    # ── Travel ─────────────────────────────────────────────────────────────────
    ("EXPEDIA",           "Travel",          None),
    ("UNITED ",           "Travel",          None),
    ("SYRACUSE AIRPORT",  "Travel",          None),
    ("UA INFLT",          "Travel",          None),
    ("LAZ PARKING",       "Travel",          None),
    ("FAIR HAVEN SP",     "Travel",          None),
    ("BROOK GEORGIA",     "Travel",          "Car rental"),
    ("EMPOWER",           "Travel",          "Car rental"),
    ("MERPAGO*MARY",      "Shopping",        "Mexico souvenir"),

    # ── Transport ──────────────────────────────────────────────────────────────
    ("METRO ",            "Transport",       None),

    # ── Shopping ───────────────────────────────────────────────────────────────
    ("BESTBUY",           "Shopping",        None),
    ("BEST BUY",          "Shopping",        None),
    ("WALMART",           "Shopping",        None),
    ("TARGET",            "Shopping",        None),
    ("MACY",              "Shopping",        None),
    ("TIKTOK SHOP",       "Shopping",        None),
    ("CHAB FASHION",      "Shopping",        "Graduation suit"),
    ("UNIQUE - 5108",     "Shopping",        None),
    ("THE UPS STORE",     "Shopping",        None),
    ("AMZN MKTP",         "Shopping",        None),
    ("OSWEGO PRINTING",   "Shopping",        None),

    # ── Entertainment ──────────────────────────────────────────────────────────
    ("REGAL CINEMAS",     "Entertainment",   None),
    ("REITHOFFER",        "Entertainment",   None),
    ("ROCKVILLE ICE",     "Entertainment",   None),
    ("REG MAJESTIC",      "Entertainment",   None),
    ("GREAT FALLS PARK",  "Entertainment",   None),
    ("VPI SFM",           "Entertainment",   "Ice skating"),
    ("OPS CSC FORT",      "Entertainment",   "Ice skating"),
    ("OPS*CSC FORT",      "Entertainment",   "Ice skating"),
    ("ENTERTAINMENT EXP", "Entertainment",   None),

    # ── Nightlife ──────────────────────────────────────────────────────────────
    ("UPTOWN LIQUORS",    "Nightlife",       None),
    ("MAYFAIT LIQUORS",   "Nightlife",       None),
    ("WINE AND SPIRITS",  "Nightlife",       None),
    ("CAVALIER LIQUOR",   "Nightlife",       None),
    ("FINE WINE",         "Nightlife",       None),
    ("SAUF HAUS",         "Nightlife",       None),
    ("CAMBRIA NAVY",      "Nightlife",       None),
    ("LITATRO",           "Nightlife",       None),
    ("DECADES LLC",       "Nightlife",       None),
    ("THE JETTY",         "Nightlife",       None),
    ("2ND STREET",        "Nightlife",       None),
    ("CLUB SEVEN",        "Nightlife",       "Niagara Falls"),

    # ── Tobacco ────────────────────────────────────────────────────────────────
    ("RED APPLE TOBACCO",  "Tobacco",        None),
    ("TOBACCO COLONY",     "Tobacco",        None),
    ("SMOKE WORLD",        "Tobacco",        None),
    ("PUFF CITY",          "Tobacco",        None),
    ("9TH AVE TOBACCO",    "Tobacco",        None),
    ("STORE OSWEGO",       "Tobacco",        "Smoke shop"),

    # ── Gambling ───────────────────────────────────────────────────────────────
    ("ROBINHOOD",          "Gambling",       None),
    ("UNDERDOG SPORTS",    "Gambling",       "Sports betting"),
    ("SLEEPER",            "Gambling",       None),

    # ── Weed (keep as Other but add note) ──────────────────────────────────────
    ("GG PHOTO ZELLE",     "Other",          "Weed"),
    ("POT SPOT",           "Other",          "Weed — Niagara Falls"),

    # ── Bank Fees ──────────────────────────────────────────────────────────────
    ("LATE FEE",           "Bank Fees",      None),
    ("EXPERIAN",           "Bank Fees",      None),
    ("FOREIGN TRANSACTION","Bank Fees",      None),
    ("BALANCE INQUIRY",    "Bank Fees",      None),

    # ── Bills & Utilities ──────────────────────────────────────────────────────
    ("PAYMENTUS",          "Bills & Utilities", None),

    # ── Internal transfers ─────────────────────────────────────────────────────
    ("PAYPAL *ABEBE NATANEM", "Transfers",   "My own account — internal transfer"),
]

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Reading {XLSX_PATH} ...")
df = pd.read_excel(XLSX_PATH, sheet_name="MASTER_DATA", engine="openpyxl")
df.columns = [c.strip() for c in df.columns]
print(f"  Loaded {len(df):,} rows")
print(f"  'Other' transactions before: {(df['Category'] == 'Other').sum()}")

if "Notes" not in df.columns:
    df["Notes"] = ""
df["Notes"] = df["Notes"].fillna("").astype(str)

# ── Apply rules ────────────────────────────────────────────────────────────────
updated = 0

for i, row in df.iterrows():
    payee    = str(row["Payee"]).upper()          if pd.notna(row["Payee"])          else ""
    vendor   = str(row["Cleaned Vendor"]).upper() if pd.notna(row["Cleaned Vendor"]) else ""
    combined = payee + " " + vendor

    for keyword, new_category, new_note in RULES:
        if keyword.upper() in combined:
            changed = False
            if df.at[i, "Category"] != new_category:
                df.at[i, "Category"] = new_category
                changed = True
            if new_note and df.at[i, "Notes"] in ("", "Needs Review"):
                df.at[i, "Notes"] = new_note
                changed = True
            if changed:
                updated += 1
            break

# ── Save ───────────────────────────────────────────────────────────────────────
df.to_excel(XLSX_PATH, sheet_name="MASTER_DATA", index=False, engine="openpyxl")

other_after = (df["Category"] == "Other").sum()
print(f"  Transactions recategorized:   {updated}")
print(f"  'Other' transactions after:   {other_after}")
print(f"\n  Saved to {XLSX_PATH}")
print(f"  Run import_to_sqlite.py to update the database.")
