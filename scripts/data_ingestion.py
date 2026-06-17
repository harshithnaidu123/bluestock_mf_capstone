"""
data_ingestion.py

Loads all 10 raw datasets for the Bluestock MF Capstone project,
prints shape, dtypes, and head() for each, and logs anomalies,
AMFI code validation, and fund master exploration findings to a
text file for later review.
"""

from pathlib import Path
import pandas as pd

# Project root is the parent of this script's folder (scripts/ -> project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
QUALITY_LOG_PATH = PROJECT_ROOT / "data" / "data_quality_summary.txt"

# All 10 provided CSV files
DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


def load_dataset(filename: str) -> pd.DataFrame:
    """Load a single CSV file from the raw data directory.

    Args:
        filename: Name of the CSV file inside data/raw.

    Returns:
        A pandas DataFrame containing the loaded data.
    """
    filepath = RAW_DIR / filename
    return pd.read_csv(filepath)


def inspect_dataset(name: str, df: pd.DataFrame, log_lines: list[str]) -> None:
    """Print shape, dtypes, and head for a dataset, and log basic
    anomaly checks (nulls, duplicates) to the provided log_lines list.

    Args:
        name: Dataset filename, used for display.
        df: The loaded DataFrame.
        log_lines: A list that anomaly notes get appended to.
    """
    print(f"\n{'=' * 70}")
    print(f"Dataset: {name}")
    print(f"{'=' * 70}")
    print(f"Shape: {df.shape}")
    print("\nDtypes:")
    print(df.dtypes)
    print("\nHead:")
    print(df.head())

    # Basic anomaly checks
    null_counts = df.isnull().sum()
    total_nulls = null_counts.sum()
    duplicate_rows = df.duplicated().sum()

    log_lines.append(f"\n{name}")
    log_lines.append(f"  Shape: {df.shape}")
    log_lines.append(f"  Total null values: {total_nulls}")
    if total_nulls > 0:
        cols_with_nulls = null_counts[null_counts > 0]
        log_lines.append(f"  Columns with nulls: {cols_with_nulls.to_dict()}")
    log_lines.append(f"  Duplicate rows: {duplicate_rows}")


def validate_amfi_codes(
    fund_master: pd.DataFrame,
    nav_history: pd.DataFrame,
    transactions: pd.DataFrame,
    log_lines: list[str],
) -> None:
    """Validate that every amfi_code in nav_history and investor_transactions
    actually exists in fund_master, and log the results.

    Args:
        fund_master: The loaded fund master DataFrame.
        nav_history: The loaded NAV history DataFrame.
        transactions: The loaded investor transactions DataFrame.
        log_lines: A list that validation notes get appended to.
    """
    valid_codes = set(fund_master["amfi_code"])
    nav_codes = set(nav_history["amfi_code"])
    txn_codes = set(transactions["amfi_code"])

    nav_orphans = nav_codes - valid_codes
    txn_orphans = txn_codes - valid_codes

    log_lines.append("\n\nAMFI CODE VALIDATION")
    log_lines.append(f"  Valid codes in fund_master: {len(valid_codes)}")
    log_lines.append(f"  Unique codes in nav_history: {len(nav_codes)}")
    log_lines.append(f"  Codes in nav_history NOT in fund_master: {sorted(nav_orphans)}")
    log_lines.append(f"  Unique codes in investor_transactions: {len(txn_codes)}")
    log_lines.append(
        f"  Codes in investor_transactions NOT in fund_master: {sorted(txn_orphans)}"
    )
    if txn_orphans:
        orphan_txn_count = transactions["amfi_code"].isin(txn_orphans).sum()
        log_lines.append(f"  Number of orphan transaction rows: {orphan_txn_count}")


def explore_fund_master(fund_master: pd.DataFrame, log_lines: list[str]) -> None:
    """Log unique fund houses, categories, sub-categories, and risk grades
    from the fund master dataset, plus the AMFI code range.

    Args:
        fund_master: The loaded fund master DataFrame.
        log_lines: A list that exploration notes get appended to.
    """
    log_lines.append("\n\nFUND MASTER EXPLORATION")
    log_lines.append(
        f"  Unique fund houses ({fund_master['fund_house'].nunique()}): "
        f"{sorted(fund_master['fund_house'].unique())}"
    )
    log_lines.append(
        f"  Unique categories ({fund_master['category'].nunique()}): "
        f"{sorted(fund_master['category'].unique())}"
    )
    log_lines.append(
        f"  Unique sub-categories ({fund_master['sub_category'].nunique()}): "
        f"{sorted(fund_master['sub_category'].unique())}"
    )
    log_lines.append(
        f"  Unique risk categories ({fund_master['risk_category'].nunique()}): "
        f"{sorted(fund_master['risk_category'].unique())}"
    )
    log_lines.append(
        f"  AMFI code range: {fund_master['amfi_code'].min()} - "
        f"{fund_master['amfi_code'].max()}"
    )


def main() -> None:
    """Load and inspect all 10 datasets, run AMFI code validation and
    fund master exploration, then write all findings to a log file.
    """
    log_lines: list[str] = ["DATA QUALITY SUMMARY - Bluestock MF Capstone", "=" * 50]

    # Step 1: load and inspect every dataset
    loaded: dict[str, pd.DataFrame] = {}
    for filename in DATASETS:
        df = load_dataset(filename)
        loaded[filename] = df
        inspect_dataset(filename, df, log_lines)

    # Step 2: AMFI code validation (Task 7) — runs once, after the loop
    validate_amfi_codes(
        fund_master=loaded["01_fund_master.csv"],
        nav_history=loaded["02_nav_history.csv"],
        transactions=loaded["08_investor_transactions.csv"],
        log_lines=log_lines,
    )

    # Step 3: fund master exploration (Task 6) — runs once, after the loop
    explore_fund_master(loaded["01_fund_master.csv"], log_lines)

    # Step 4: write everything to the log file
    QUALITY_LOG_PATH.write_text("\n".join(log_lines), encoding="utf-8")
    print(f"\n\nData quality summary written to: {QUALITY_LOG_PATH}")


if __name__ == "__main__":
    main()