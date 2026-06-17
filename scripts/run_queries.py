"""
run_queries.py

Executes every query in sql/queries.sql against bluestock_mf.db and
prints the results, to verify all 10 analytical queries run without
errors and return sensible data.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db" / "bluestock_mf.db"
QUERIES_PATH = PROJECT_ROOT / "sql" / "queries.sql"


def main() -> None:
    """Parse queries.sql into individual statements and run each one."""
    engine = create_engine(f"sqlite:///{DB_PATH}")
    sql_text = QUERIES_PATH.read_text(encoding="utf-8")

    # Split on the "-- Query N:" comment markers to isolate each query
    raw_blocks = sql_text.split("-- Query ")[1:]  # skip header before Query 1

    for block in raw_blocks:
        # First line after split has the query number/title
        title_line, _, rest = block.partition("\n")
        query_sql = rest.split("--", 1)[-1] if rest.strip().startswith("--") else rest
        # Strip leading comment lines, keep the actual SQL
        lines = [l for l in rest.split("\n") if not l.strip().startswith("--")]
        query_sql = "\n".join(lines).strip()

        print(f"\n{'=' * 70}")
        print(f"Query {title_line.strip()}")
        print(f"{'=' * 70}")
        try:
            result_df = pd.read_sql_query(query_sql, engine)
            print(result_df.head(10).to_string(index=False))
            print(f"... ({len(result_df)} total rows)" if len(result_df) > 10 else "")
        except Exception as exc:
            print(f"ERROR running query: {exc}")


if __name__ == "__main__":
    main()