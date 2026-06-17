"""
db_loader.py

Creates the Bluestock MF SQLite database, executes the star schema
from sql/schema.sql, and loads all cleaned CSVs from data/processed/
into their corresponding tables using SQLAlchemy. Verifies that row
counts in the database match the source CSV row counts.
"""

from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def create_schema(engine) -> None:
    """Execute the schema.sql file to create all tables and indexes.

    Args:
        engine: A SQLAlchemy engine connected to the target database.
    """
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    # SQLite via SQLAlchemy needs statements executed one at a time
    statements = [s.strip() for s in schema_sql.split(";") if s.strip()]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))
    print(f"Schema created from {SCHEMA_PATH}")


def load_dim_fund(engine) -> int:
    """Load dim_fund from clean_fund_master.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_fund_master.csv")
    df.to_sql("dim_fund", engine, if_exists="append", index=False)
    return len(df)


def load_dim_investor(engine) -> int:
    """Build dim_investor by extracting unique investors from the
    cleaned investor_transactions CSV (one row per investor_id).

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of unique investors loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_investor_transactions.csv")
    investor_cols = [
        "investor_id", "state", "city", "city_tier",
        "age_group", "gender", "annual_income_lakh", "kyc_status",
    ]
    investors = df[investor_cols].drop_duplicates(subset="investor_id")
    investors.to_sql("dim_investor", engine, if_exists="append", index=False)
    return len(investors)


def load_fact_nav(engine) -> int:
    """Load fact_nav from clean_nav_history.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_nav_history.csv")
    df = df.rename(columns={"date": "nav_date", "nav": "nav_value"})
    df[["amfi_code", "nav_date", "nav_value"]].to_sql(
        "fact_nav", engine, if_exists="append", index=False
    )
    return len(df)


def load_fact_transactions(engine) -> int:
    """Load fact_transactions from clean_investor_transactions.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_investor_transactions.csv")
    cols = [
        "investor_id", "transaction_date", "amfi_code",
        "transaction_type", "amount_inr", "payment_mode",
    ]
    df[cols].to_sql("fact_transactions", engine, if_exists="append", index=False)
    return len(df)


def load_fact_performance(engine) -> int:
    """Load fact_performance from clean_scheme_performance.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_scheme_performance.csv")
    cols = [
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade",
    ]
    df[cols].to_sql("fact_performance", engine, if_exists="append", index=False)
    return len(df)


def load_fact_aum(engine) -> int:
    """Load fact_aum from clean_aum_by_fund_house.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_aum_by_fund_house.csv")
    df = df.rename(columns={"date": "quarter_date"})
    cols = ["quarter_date", "fund_house", "aum_lakh_crore", "aum_crore", "num_schemes"]
    df[cols].to_sql("fact_aum", engine, if_exists="append", index=False)
    return len(df)


def load_fact_sip(engine) -> int:
    """Load fact_sip from clean_monthly_sip_inflows.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_monthly_sip_inflows.csv")
    df = df.rename(columns={"month": "month_year"})
    df.to_sql("fact_sip", engine, if_exists="append", index=False)
    return len(df)


def load_fact_category_inflows(engine) -> int:
    """Load fact_category_inflows from clean_category_inflows.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_category_inflows.csv")
    df = df.rename(columns={"month": "month_year"})
    df.to_sql("fact_category_inflows", engine, if_exists="append", index=False)
    return len(df)


def load_fact_folio_count(engine) -> int:
    """Load fact_folio_count from clean_industry_folio_count.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_industry_folio_count.csv")
    df = df.rename(columns={"month": "month_year"})
    df.to_sql("fact_folio_count", engine, if_exists="append", index=False)
    return len(df)


def load_fact_holdings(engine) -> int:
    """Load fact_holdings from clean_portfolio_holdings.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_portfolio_holdings.csv")
    df.to_sql("fact_holdings", engine, if_exists="append", index=False)
    return len(df)


def load_fact_benchmark(engine) -> int:
    """Load fact_benchmark from clean_benchmark_indices.csv.

    Args:
        engine: SQLAlchemy engine.

    Returns:
        Number of rows loaded.
    """
    df = pd.read_csv(PROCESSED_DIR / "clean_benchmark_indices.csv")
    df = df.rename(columns={"date": "index_date"})
    df.to_sql("fact_benchmark", engine, if_exists="append", index=False)
    return len(df)


def verify_row_counts(engine, expected_counts: dict[str, int]) -> None:
    """Compare expected row counts (from source CSVs) against actual
    row counts now in the database, and print a pass/fail report.

    Args:
        engine: SQLAlchemy engine.
        expected_counts: Dict of {table_name: expected_row_count}.
    """
    print("\n" + "=" * 60)
    print("ROW COUNT VERIFICATION")
    print("=" * 60)
    with engine.connect() as conn:
        for table_name, expected in expected_counts.items():
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            actual = result.scalar()
            status = "OK" if actual == expected else "MISMATCH"
            print(f"  {table_name}: expected={expected}, actual={actual}  [{status}]")


def main() -> None:
    """Build the database from scratch: create schema, load all
    tables, and verify row counts match source CSVs.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)

    # Start fresh each time this script runs
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database at {DB_PATH}")

    engine = create_engine(f"sqlite:///{DB_PATH}")

    print("Creating schema...")
    create_schema(engine)

    print("\nLoading tables...")
    expected_counts = {}

    expected_counts["dim_fund"] = load_dim_fund(engine)
    print(f"  dim_fund: {expected_counts['dim_fund']} rows loaded")

    expected_counts["dim_investor"] = load_dim_investor(engine)
    print(f"  dim_investor: {expected_counts['dim_investor']} rows loaded")

    expected_counts["fact_nav"] = load_fact_nav(engine)
    print(f"  fact_nav: {expected_counts['fact_nav']} rows loaded")

    expected_counts["fact_transactions"] = load_fact_transactions(engine)
    print(f"  fact_transactions: {expected_counts['fact_transactions']} rows loaded")

    expected_counts["fact_performance"] = load_fact_performance(engine)
    print(f"  fact_performance: {expected_counts['fact_performance']} rows loaded")

    expected_counts["fact_aum"] = load_fact_aum(engine)
    print(f"  fact_aum: {expected_counts['fact_aum']} rows loaded")

    expected_counts["fact_sip"] = load_fact_sip(engine)
    print(f"  fact_sip: {expected_counts['fact_sip']} rows loaded")

    expected_counts["fact_category_inflows"] = load_fact_category_inflows(engine)
    print(f"  fact_category_inflows: {expected_counts['fact_category_inflows']} rows loaded")

    expected_counts["fact_folio_count"] = load_fact_folio_count(engine)
    print(f"  fact_folio_count: {expected_counts['fact_folio_count']} rows loaded")

    expected_counts["fact_holdings"] = load_fact_holdings(engine)
    print(f"  fact_holdings: {expected_counts['fact_holdings']} rows loaded")

    expected_counts["fact_benchmark"] = load_fact_benchmark(engine)
    print(f"  fact_benchmark: {expected_counts['fact_benchmark']} rows loaded")

    verify_row_counts(engine, expected_counts)

    print(f"\nDatabase built successfully at {DB_PATH}")


if __name__ == "__main__":
    main()