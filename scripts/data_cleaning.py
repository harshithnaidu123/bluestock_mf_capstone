"""
data_cleaning.py

Cleans all 10 raw datasets for the Bluestock MF Capstone project and
saves cleaned versions to data/processed/. Each cleaning function
handles a specific dataset's known data quality issues: date parsing,
missing value handling, deduplication, and range validation.
"""

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def clean_nav_history() -> pd.DataFrame:
    """Clean 02_nav_history.csv.

    Steps:
        1. Parse the date column to datetime.
        2. Sort by amfi_code then date.
        3. Reindex each scheme to a full daily date range and
           forward-fill missing NAVs (covers weekends/holidays
           where no NAV is published).
        4. Drop exact duplicate rows.
        5. Validate that every NAV value is strictly positive.

    Returns:
        The cleaned NAV history DataFrame with columns:
        amfi_code, date, nav.
    """
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["amfi_code", "date"]).drop_duplicates()

    # Reindex each scheme to a full daily calendar range, then
    # forward-fill NAV for weekends/holidays where markets are closed.
    cleaned_groups = []
    for amfi_code, group in df.groupby("amfi_code"):
        group = group.set_index("date")
        full_range = pd.date_range(group.index.min(), group.index.max(), freq="D")
        group = group.reindex(full_range)
        group["nav"] = group["nav"].ffill()
        group["amfi_code"] = amfi_code
        group = group.reset_index().rename(columns={"index": "date"})
        cleaned_groups.append(group)

    result = pd.concat(cleaned_groups, ignore_index=True)
    result = result[["amfi_code", "date", "nav"]]

    # Validation: every NAV must be > 0
    invalid_count = (result["nav"] <= 0).sum()
    if invalid_count > 0:
        print(f"  WARNING: {invalid_count} rows have NAV <= 0 after cleaning")
    assert result["nav"].notna().all(), "NAV contains nulls after forward-fill"

    print(
        f"  nav_history: {len(df)} raw rows -> {len(result)} cleaned rows "
        f"(reindexed to full daily range per scheme)"
    )
    print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    print(f"  Unique schemes: {result['amfi_code'].nunique()}")
    return result


def clean_investor_transactions() -> pd.DataFrame:
    """Clean 08_investor_transactions.csv.

    Steps:
        1. Parse transaction_date to datetime.
        2. Standardise transaction_type values to exactly
           {"SIP", "Lumpsum", "Redemption"} (case/whitespace fixes).
        3. Validate amount_inr > 0; flag and remove any violations.
        4. Check kyc_status only contains expected enum values.
        5. Drop exact duplicate rows.

    Returns:
        The cleaned investor transactions DataFrame.
    """
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    initial_rows = len(df)

    df["transaction_date"] = pd.to_datetime(df["transaction_date"])

    # Standardise transaction_type: strip whitespace, fix casing.
    # Title-casing "SIP" gives "Sip", so explicitly map it back to "SIP".
    df["transaction_type"] = df["transaction_type"].str.strip().str.title()
    df["transaction_type"] = df["transaction_type"].replace({"Sip": "SIP"})
    valid_types = {"SIP", "Lumpsum", "Redemption"}

    unexpected_types = set(df["transaction_type"].unique()) - valid_types
    if unexpected_types:
        print(f"  WARNING: unexpected transaction_type values found: {unexpected_types}")

    # Validate amount_inr > 0
    invalid_amount_count = (df["amount_inr"] <= 0).sum()
    if invalid_amount_count > 0:
        print(f"  WARNING: {invalid_amount_count} rows have amount_inr <= 0, removing them")
        df = df[df["amount_inr"] > 0]

    # Check KYC status enum values
    valid_kyc_statuses = {"Verified", "Pending", "Rejected"}
    actual_kyc_statuses = set(df["kyc_status"].unique())
    unexpected_kyc = actual_kyc_statuses - valid_kyc_statuses
    if unexpected_kyc:
        print(f"  NOTE: kyc_status contains values beyond the expected set: {unexpected_kyc}")
    print(f"  KYC status values found: {sorted(actual_kyc_statuses)}")

    # Drop exact duplicates
    before_dedup = len(df)
    df = df.drop_duplicates()
    after_dedup = len(df)
    if before_dedup != after_dedup:
        print(f"  Removed {before_dedup - after_dedup} duplicate rows")

    print(f"  investor_transactions: {initial_rows} raw rows -> {len(df)} cleaned rows")
    print(f"  transaction_type values: {sorted(df['transaction_type'].unique())}")
    return df


def clean_scheme_performance() -> pd.DataFrame:
    """Clean 07_scheme_performance.csv.

    Steps:
        1. Coerce all return/ratio columns to numeric, flagging any
           values that fail to convert.
        2. Validate expense_ratio_pct falls within the expected
           0.1%-2.5% industry range.
        3. Drop exact duplicate rows.

    Returns:
        The cleaned scheme performance DataFrame.
    """
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    initial_rows = len(df)

    numeric_cols = [
        "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
        "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct",
        "expense_ratio_pct",
    ]
    for col in numeric_cols:
        before_na = df[col].isna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_na = df[col].isna().sum()
        new_nans = after_na - before_na
        if new_nans > 0:
            print(f"  WARNING: {new_nans} non-numeric values found in '{col}', coerced to NaN")

    # Validate expense_ratio_pct is between 0.1% and 2.5%
    # Note: column is stored as a percentage value (e.g. 1.54 means 1.54%)
    out_of_range = df[(df["expense_ratio_pct"] < 0.1) | (df["expense_ratio_pct"] > 2.5)]
    if len(out_of_range) > 0:
        print(f"  WARNING: {len(out_of_range)} schemes have expense_ratio_pct outside 0.1%-2.5%:")
        print(out_of_range[["scheme_name", "expense_ratio_pct"]].to_string(index=False))
    else:
        print(f"  All expense ratios within expected 0.1%-2.5% range")

    df = df.drop_duplicates()
    print(f"  scheme_performance: {initial_rows} raw rows -> {len(df)} cleaned rows")
    return df


def main() -> None:
    """Run all cleaning functions and save outputs to data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Cleaning nav_history...")
    nav_clean = clean_nav_history()
    nav_clean.to_csv(PROCESSED_DIR / "clean_nav_history.csv", index=False)
    print(f"  Saved to {PROCESSED_DIR / 'clean_nav_history.csv'}")

    print("\nCleaning investor_transactions...")
    txn_clean = clean_investor_transactions()
    txn_clean.to_csv(PROCESSED_DIR / "clean_investor_transactions.csv", index=False)
    print(f"  Saved to {PROCESSED_DIR / 'clean_investor_transactions.csv'}")

    print("\nCleaning scheme_performance...")
    perf_clean = clean_scheme_performance()
    perf_clean.to_csv(PROCESSED_DIR / "clean_scheme_performance.csv", index=False)
    print(f"  Saved to {PROCESSED_DIR / 'clean_scheme_performance.csv'}")


if __name__ == "__main__":
    main()