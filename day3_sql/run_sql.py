import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
engine = create_engine(os.environ["DATABASE_URL"])

raw_sql = Path("day3_sql/queries.sql").read_text(encoding="utf-8")
statements = [s.strip() for s in raw_sql.split(";") if s.strip()]

with engine.begin() as conn:
    for stmt in statements:
        first_line = stmt.splitlines()[0]
        print(f"\n{'=' * 70}\n{first_line}\n{'=' * 70}")
        result = conn.execute(text(stmt))
        if result.returns_rows:
            rows = result.fetchall()
            print(" | ".join(result.keys()))
            limit = 25 if "EXPLAIN" in stmt.upper() else 10
            for row in rows[:limit]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > limit:
                print(f"... ({len(rows)} total rows)")
        else:
            print("Executed successfully.")