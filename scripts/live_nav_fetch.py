"""
live_nav_fetch.py

Fetches live NAV history from the mfapi.in REST API for HDFC Top 100
Direct and 5 additional key schemes, parses the JSON response, and
saves each as a raw CSV in data/raw/.

IMPORTANT DATA QUALITY NOTE:
Several of these funds were renamed under SEBI's 2018 mutual fund
re-categorisation rules. "Bluechip" and "Top 100" branded large-cap
funds across multiple AMCs were renamed to "Large Cap Fund". The
scheme codes below were manually verified against the live mfapi.in
API on 2026-06-17 by searching for both the original brief name and
the renamed SEBI category name. Each entry below documents both the
original name (from the project brief) and the confirmed current
name (from mfapi.in).
"""

from pathlib import Path
import time

import pandas as pd
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

API_BASE_URL = "https://api.mfapi.in/mf"
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30  # seconds

# friendly_name -> (scheme_code, original_brief_name, confirmed_current_name)
# All scheme codes below were manually verified via /mf/search against
# the live API. See module docstring for the SEBI rename context.
VERIFIED_SCHEMES = {
    "HDFC_Top_100_Direct": (
        119018,
        "HDFC Top 100 Fund",
        "HDFC Large Cap Fund - Growth Option - Direct Plan",
    ),
    "SBI_Bluechip": (
        119598,
        "SBI Bluechip Fund",
        "SBI Large Cap FUND-DIRECT PLAN-GROWTH",
    ),
    "ICICI_Bluechip": (
        120586,
        "ICICI Prudential Bluechip Fund",
        "ICICI Prudential Large Cap Fund (erstwhile Bluechip Fund) - Direct Plan - Growth",
    ),
    "Nippon_Large_Cap": (
        118632,
        "Nippon India Large Cap Fund",
        "Nippon India Large Cap Fund - Direct Plan Growth Plan - Growth Option",
    ),
    "Axis_Bluechip": (
        120465,
        "Axis Bluechip Fund",
        "Axis Large Cap Fund - Direct Plan - Growth",
    ),
    "Kotak_Bluechip": (
        120152,
        "Kotak Bluechip Fund",
        "Kotak Large Cap Fund - Growth - Direct",
    ),
}


def request_with_retry(url: str, params: dict | None = None):
    """Make a GET request with retry logic for transient network errors.

    Args:
        url: The URL to fetch.
        params: Optional query string parameters.

    Returns:
        Parsed JSON response.

    Raises:
        requests.RequestException: If all retry attempts fail.
    """
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            last_error = exc
            print(f"    Attempt {attempt}/{MAX_RETRIES} failed: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(2 * attempt)
    raise last_error  # type: ignore[misc]


def fetch_nav(scheme_code: int) -> dict:
    """Fetch full NAV history + meta for a scheme code.

    Args:
        scheme_code: The AMFI scheme code to fetch.

    Returns:
        Parsed JSON response with "meta" and "data" keys.
    """
    return request_with_retry(f"{API_BASE_URL}/{scheme_code}")


def save_nav_to_csv(scheme_code: int, friendly_name: str, payload: dict) -> Path:
    """Convert the mfapi.in JSON payload into a DataFrame and save as CSV.

    Args:
        scheme_code: The AMFI scheme code (used in filename).
        friendly_name: A readable fund name (used in filename).
        payload: The parsed JSON response from fetch_nav.

    Returns:
        Path to the saved CSV file.
    """
    nav_records = payload.get("data", [])
    df = pd.DataFrame(nav_records)
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values("date").reset_index(drop=True)
    df["amfi_code"] = scheme_code

    out_path = RAW_DIR / f"live_nav_{scheme_code}_{friendly_name}.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    """Fetch and save live NAV data for all 6 verified target schemes."""
    summary: list[str] = []

    for friendly_name, (scheme_code, original_name, expected_name) in VERIFIED_SCHEMES.items():
        print(f"\n{'=' * 70}")
        print(f"Fetching: {friendly_name}  (code {scheme_code})")
        print(f"  Original brief name: {original_name}")
        print(f"{'=' * 70}")

        payload = fetch_nav(scheme_code)
        meta = payload.get("meta", {})
        confirmed_name = meta.get("scheme_name", "")
        confirmed_house = meta.get("fund_house", "")

        print(f"  Confirmed fund house: {confirmed_house}")
        print(f"  Confirmed scheme name: {confirmed_name}")

        if confirmed_name != expected_name:
            print(f"  WARNING: confirmed name differs from expected '{expected_name}'")

        out_path = save_nav_to_csv(scheme_code, friendly_name, payload)
        row_count = len(payload.get("data", []))
        print(f"  Saved {row_count} rows to: {out_path}")

        summary.append(
            f"{friendly_name}: scheme_code={scheme_code}, "
            f"fund_house='{confirmed_house}', name='{confirmed_name}', rows={row_count}"
        )

    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    for line in summary:
        print(line)


if __name__ == "__main__":
    main()