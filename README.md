# Personal Finance Analytics Pipeline

A personal data engineering project that processes, cleans, and analyzes 2,000+ bank transactions across multiple accounts using Python, SQLite, and SQL.

## Project Overview

Built an end-to-end ETL (Extract, Transform, Load) pipeline to consolidate raw bank exports into a structured, queryable database. The project automates data cleaning, vendor classification, and category normalization — turning messy bank data into clean, analyzable insights.

## What It Does

- **Ingests** raw Excel exports from multiple bank accounts (TD Bank, Bank of America, Citi)
- **Cleans** and normalizes 2,021 transactions including dates, amounts, and vendor names
- **Classifies** 600+ person-to-person transactions using rule-based annotation
- **Recategorizes** miscategorized vendors using keyword-matching rules
- **Loads** cleaned data into a SQLite database with derived analytical views
- **Generates** summaries for spending by category, income vs expenses, and monthly trends

## Tech Stack

- **Python** (pandas, openpyxl, sqlite3)
- **SQLite** for structured storage and querying
- **SQL** for analytical views and reporting
- **Excel** for raw data management

## Project Structure

```
finance_project/
│
├── scripts/
│   ├── import_to_sqlite.py        # ETL pipeline: Excel → SQLite
│   ├── auto_annotate.py           # Rule-based transaction annotation
│   ├── recategorize.py            # Vendor keyword recategorization
│   └── add_annotation_columns.py  # Adds Notes and Income Source columns
│
├── clean_data/                    # (gitignored) Master transaction data
├── database/                      # (gitignored) SQLite database
└── .gitignore
```

## Database Schema

**`transactions`** table — master table with all raw and cleaned fields:

| Column | Description |
|---|---|
| date | Transaction date (YYYY-MM-DD) |
| payee | Raw payee description from bank |
| amount | Transaction amount (negative = expense) |
| category | Spending category |
| cleaned_vendor | Normalized vendor name |
| type | Expense / Income |
| notes | Manual or auto-generated annotation |
| income_source | Earned / Family / Reimbursement / Internal |

**Derived views:**
- `monthly_summary` — spending by category per month
- `top_vendors` — top 25 vendors by total spend
- `category_summary` — total and average spend per category
- `income_vs_expenses` — monthly income vs expense comparison

## Key Features

### Automated Annotation (`auto_annotate.py`)
- Matches 50+ known people against raw payee text
- Distinguishes rent payments from personal payments using amount thresholds
- Classifies income by source (earned, family, reimbursement, internal transfer)
- Flags unidentified transactions for manual review

### Vendor Recategorization (`recategorize.py`)
- 100+ keyword rules to fix miscategorized transactions
- Moves vendors from "Other" into correct categories (Food & Dining, Auto & Gas, Subscriptions, etc.)
- Reduced uncategorized transactions from 267 to 0

### ETL Pipeline (`import_to_sqlite.py`)
- Handles Excel date serial number conversion
- Normalizes column names
- Rebuilds all views on every run
- Prints sanity check summary after each load

## Setup

```bash
pip install pandas openpyxl
python scripts/import_to_sqlite.py
```

## Skills Demonstrated

- ETL pipeline design and implementation
- Data cleaning and normalization at scale
- Rule-based classification systems
- Relational database design (SQLite)
- SQL view creation and querying
- Python scripting (pandas, file I/O, string matching)
