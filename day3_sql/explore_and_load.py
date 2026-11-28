import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

CSV_PATH = Path("day3_sql/data/vendor_payments.csv")
DATABASE_URL = os.environ["DATABASE_URL"]

# --- STEP 1: Explore CSV in pandas ---
df = pd.read_csv(
    CSV_PATH,
    parse_dates=["invoice_date", "due_date", "payment_date"],
)

print("=== SHAPE (rows, cols) ===")
print(df.shape)

print("\n=== DATA TYPES ===")
print(df.dtypes)

print("\n=== NULL COUNTS ===")
print(df.isna().sum())

print("\n=== TOP 5 VENDORS BY TOTAL SPEND (pandas groupby) ===")
print(df.groupby("vendor_name")["amount"].sum().sort_values(ascending=False).head(5))

# --- STEP 2: Create Postgres table & load data ---
engine = create_engine(DATABASE_URL)

create_table_sql = """
DROP TABLE IF EXISTS vendor_payments;
CREATE TABLE vendor_payments (
    payment_id   INTEGER PRIMARY KEY,
    invoice_no   TEXT NOT NULL,
    vendor_name  TEXT NOT NULL,
    category     TEXT NOT NULL,
    amount       NUMERIC(12, 2) NOT NULL,
    invoice_date DATE NOT NULL,
    due_date     DATE NOT NULL,
    payment_date DATE,
    status       TEXT NOT NULL,
    notes        TEXT
);
"""

with engine.begin() as conn:
    conn.execute(text(create_table_sql))

df.to_sql(
    "vendor_payments",
    con=engine,
    if_exists="append",
    index=False,
    method="multi",
    chunksize=1000,
)

with engine.connect() as conn:
    row_count = conn.execute(text("SELECT COUNT(*) FROM vendor_payments")).scalar()
print(f"\nLoaded {row_count} rows into PostgreSQL table 'vendor_payments'.")