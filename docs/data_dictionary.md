# Data Dictionary — Bluestock MF Capstone

This document describes every table and column in `bluestock_mf.db`,
including data types, business definitions, allowed values, and the
source CSV each table was built from. See `sql/schema.sql` for the
full CREATE TABLE statements.

## Star Schema Overview

- **3 dimension tables**: `dim_fund`, `dim_date`, `dim_investor`
- **8 fact tables**: `fact_nav`, `fact_transactions`, `fact_performance`,
  `fact_aum`, `fact_sip`, `fact_category_inflows`, `fact_folio_count`,
  `fact_holdings`, `fact_benchmark`

---

## dim_fund

One row per AMFI scheme. Source: `01_fund_master.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| amfi_code | INTEGER (PK) | Unique AMFI scheme code identifying this fund | Range observed: 100016–149324 |
| fund_house | TEXT | Asset Management Company (AMC) operating the fund | 10 AMCs: SBI, HDFC, ICICI Prudential, Nippon India, Kotak Mahindra, Axis, Aditya Birla Sun Life, UTI, Mirae Asset, DSP |
| scheme_name | TEXT | Full official scheme name including plan and option | e.g. "SBI Bluechip Fund - Direct Plan - Growth" |
| category | TEXT | Top-level SEBI category | Equity, Debt |
| sub_category | TEXT | SEBI sub-category | ELSS, Flexi Cap, Gilt, Index, Index/ETF, Large & Mid Cap, Large Cap, Liquid, Mid Cap, Short Duration, Small Cap, Value |
| plan | TEXT | Plan type | Direct, Regular |
| launch_date | DATE | Date the scheme was launched | ISO format YYYY-MM-DD |
| benchmark | TEXT | Benchmark index this fund is measured against | e.g. NIFTY50, NIFTY100 |
| expense_ratio_pct | REAL | Annual fund management fee as % of AUM | Validated range: 0.1%–2.5% |
| exit_load_pct | REAL | Penalty % charged on early redemption | Percentage |
| min_sip_amount | INTEGER | Minimum SIP investment amount in INR | Whole rupees |
| min_lumpsum_amount | INTEGER | Minimum lumpsum investment amount in INR | Whole rupees |
| fund_manager | TEXT | Name of the fund's manager | |
| risk_category | TEXT | SEBI riskometer grade | Low, Moderate, Moderately High, High, Very High |
| sebi_category_code | TEXT | Internal SEBI classification code | e.g. EC01, DC02 |

---

## dim_date

Calendar reference table covering the full project date range
(2022-01-01 to 2026-05-31). Generated programmatically, not from a
source CSV.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| date_id | TEXT (PK) | ISO date string, used as join key | YYYY-MM-DD |
| full_date | DATE | The calendar date | |
| year | INTEGER | Calendar year | 2022–2026 |
| quarter | INTEGER | Calendar quarter | 1–4 |
| month | INTEGER | Calendar month number | 1–12 |
| month_name | TEXT | Full month name | January–December |
| day | INTEGER | Day of month | 1–31 |
| day_of_week | TEXT | Day name | Monday–Sunday |
| is_weekend | INTEGER | Whether the date falls on Sat/Sun | 0 = weekday, 1 = weekend |

---

## dim_investor

One row per unique investor, de-duplicated from transaction records.
Source: derived from `08_investor_transactions.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| investor_id | TEXT (PK) | Unique investor identifier | Format: INV###### |
| state | TEXT | Indian state of residence | 12 states observed (MH, KA, TN, DL, GJ, UP, WB, etc.) |
| city | TEXT | City of residence | |
| city_tier | TEXT | City tier classification | T30 (top 30 cities), B30 (beyond top 30) |
| age_group | TEXT | Investor age band | 18-25, 26-35, 36-45, 46-55, 56+ |
| gender | TEXT | Investor gender | Male, Female |
| annual_income_lakh | REAL | Self-reported annual income in lakh INR | |
| kyc_status | TEXT | KYC verification status | Verified, Pending (Rejected defined but not observed in this dataset) |

---

## fact_nav

Daily NAV per scheme. Grain: one row per (amfi_code, nav_date).
Source: `02_nav_history.csv`, cleaned (forward-filled for
weekends/holidays).

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| nav_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| amfi_code | INTEGER (FK -> dim_fund) | Scheme this NAV belongs to | |
| nav_date | DATE | Date of this NAV value | Daily, including weekends (forward-filled) |
| nav_value | REAL | Net Asset Value per unit, in INR | Always > 0 |

**Cleaning note**: raw data only includes trading days (~46,000 rows
for 40 schemes over ~4.5 years). Cleaned data is reindexed to every
calendar day per scheme and forward-filled, producing 64,320 rows,
so that day-over-day return calculations in Day 4 don't see false
gaps across weekends/holidays.

---

## fact_transactions

One row per investor transaction. Source: `08_investor_transactions.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| txn_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| investor_id | TEXT (FK -> dim_investor) | Investor who made this transaction | |
| transaction_date | DATE | Date of the transaction | |
| amfi_code | INTEGER (FK -> dim_fund) | Scheme this transaction relates to | |
| transaction_type | TEXT | Type of transaction | SIP, Lumpsum, Redemption |
| amount_inr | INTEGER | Transaction amount in INR | Always > 0 (validated during cleaning) |
| payment_mode | TEXT | Method of payment | UPI, Cheque, Mandate, Net Banking, etc. |

---

## fact_performance

One row per scheme — pre-computed performance metrics provided in
the source data. Source: `07_scheme_performance.csv`.

**Important**: this table is used to VALIDATE the metrics independently
recomputed in the Day 4 performance analytics notebook from
`fact_nav`. It is not the primary source of truth for Sharpe/Sortino/
Alpha/Beta in the final analysis.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| perf_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| amfi_code | INTEGER (FK -> dim_fund) | Scheme this performance row describes | |
| return_1yr_pct | REAL | 1-year trailing return | Percentage |
| return_3yr_pct | REAL | 3-year annualised return (CAGR) | Percentage |
| return_5yr_pct | REAL | 5-year annualised return (CAGR) | Percentage |
| benchmark_3yr_pct | REAL | Benchmark's 3-year annualised return | Percentage |
| alpha | REAL | Jensen's Alpha vs benchmark | Annualised |
| beta | REAL | Beta (systematic risk) vs benchmark | Typically 0.7–1.3 for equity funds |
| sharpe_ratio | REAL | Risk-adjusted return (excess return / total volatility) | |
| sortino_ratio | REAL | Risk-adjusted return (excess return / downside volatility) | |
| std_dev_ann_pct | REAL | Annualised standard deviation of returns | Percentage |
| max_drawdown_pct | REAL | Maximum peak-to-trough decline | Percentage (negative) |
| aum_crore | INTEGER | Assets Under Management, in INR crore | Scheme-level (not industry-level) |
| expense_ratio_pct | REAL | Annual expense ratio | Validated: 0.1%–2.5% |
| morningstar_rating | INTEGER | Morningstar star rating | 1–5 |
| risk_grade | TEXT | SEBI riskometer grade | Same values as dim_fund.risk_category |

---

## fact_aum

Quarterly AUM by fund house. Source: `03_aum_by_fund_house.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| aum_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| quarter_date | DATE | Quarter-end date | e.g. 2022-03-31 |
| fund_house | TEXT | AMC name | Matches dim_fund.fund_house |
| aum_lakh_crore | REAL | AUM in lakh crore INR (industry-level unit) | e.g. 6.05 = Rs 6.05 lakh crore |
| aum_crore | INTEGER | AUM in crore INR | e.g. 605000 = Rs 6.05 lakh crore. **Units differ from fact_performance.aum_crore, which is scheme-level, not fund-house-level** |
| num_schemes | INTEGER | Number of schemes this AMC operates | |

---

## fact_sip

Monthly industry-wide SIP inflow statistics. Source:
`04_monthly_sip_inflows.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| sip_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| month_year | DATE | Month this row describes (first of month) | |
| sip_inflow_crore | INTEGER | Total SIP inflow that month, in INR crore | All-time high: Rs 31,002 crore (Dec 2025) |
| active_sip_accounts_crore | REAL | Active SIP accounts, in crore | |
| new_sip_accounts_lakh | REAL | New SIP accounts opened that month, in lakh | |
| sip_aum_lakh_crore | REAL | AUM attributable to SIP, in lakh crore | |
| yoy_growth_pct | REAL | Year-over-year growth in SIP inflow | NULL for first 12 months (no prior year to compare) |

---

## fact_category_inflows

Monthly net inflows by fund category. Source: `05_category_inflows.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| inflow_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| month_year | DATE | Month this row describes | Covers FY 2024-25 |
| category | TEXT | Fund category | Large Cap, Mid Cap, Small Cap, Flexi Cap, Large & Mid Cap, ELSS, Liquid, Gilt, Sectoral/Thematic, Short Duration, etc. |
| net_inflow_crore | REAL | Net inflow (or outflow if negative) that month, in INR crore | |

---

## fact_folio_count

Quarterly industry-wide investor folio counts. Source:
`06_industry_folio_count.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| folio_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| month_year | DATE | Quarter this row describes | Jan 2022 – Dec 2025 |
| total_folios_crore | REAL | Total folios across all categories, in crore | Grew from 13.26 Cr to 26.12 Cr over the period |
| equity_folios_crore | REAL | Folios in equity schemes, in crore | |
| debt_folios_crore | REAL | Folios in debt schemes, in crore | |
| hybrid_folios_crore | REAL | Folios in hybrid schemes, in crore | |
| others_folios_crore | REAL | Folios in other scheme types, in crore | |

---

## fact_holdings

Top stock holdings per equity fund. Source: `09_portfolio_holdings.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| holding_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| amfi_code | INTEGER (FK -> dim_fund) | Fund this holding belongs to | |
| stock_symbol | TEXT | NSE/BSE ticker symbol | |
| stock_name | TEXT | Full company name | |
| sector | TEXT | Industry sector | Banking, Pharma, Utilities, Diversified, Paints, etc. |
| weight_pct | REAL | % of fund's portfolio in this stock | **Note**: per-fund weights may sum to <100% since this file lists only TOP holdings, not the complete portfolio. 9 of 40 funds show total weight outside 50-100% for this reason — not a data error. |
| market_value_cr | REAL | Market value of this holding, in INR crore | |
| current_price_inr | REAL | Current share price, in INR | |
| portfolio_date | DATE | As-of date for this holdings snapshot | |

---

## fact_benchmark

Daily closing values for benchmark indices. Source:
`10_benchmark_indices.csv`.

| Column | Type | Definition | Allowed values / notes |
|---|---|---|---|
| benchmark_id | INTEGER (PK) | Auto-incrementing surrogate key | |
| index_date | DATE | Date of this closing value | |
| index_name | TEXT | Name of the benchmark index | NIFTY50, NIFTY100, NIFTY500, NIFTY_MIDCAP150, BSE_SMALLCAP, CRISIL_GILT, CRISIL_LIQUID |
| close_value | REAL | Closing value of the index that day | Always > 0 |

---

## Known Data Quality Notes

1. **mfapi.in scheme renames**: several funds referenced by the project
   brief under their pre-2018 names ("Bluechip", "Top 100") were
   renamed under SEBI's 2018 re-categorisation rules to "Large Cap
   Fund". Live NAV fetch in `live_nav_fetch.py` resolves these via
   manually verified scheme codes documented in that script's
   `VERIFIED_SCHEMES` dictionary.
2. **AUM unit distinction**: `fact_aum.aum_crore` (fund-house/industry
   level, can be in the hundreds of thousands of crore) and
   `fact_performance.aum_crore` (single-scheme level, typically tens
   of thousands of crore) measure different things at different
   granularities despite the identical column name. Always check
   which table you're querying.
3. **kyc_status**: the schema allows for "Rejected" as a valid value,
   but this dataset only contains "Verified" and "Pending" records.
4. **Portfolio holdings completeness**: `fact_holdings.weight_pct`
   does not necessarily sum to 100% per fund, since the source file
   only lists top holdings, not the full portfolio breakdown.
5. **AMFI code validation**: all `amfi_code` values across
   `nav_history` and `investor_transactions` were confirmed to exist
   in `fund_master` with zero orphan records (see
   `data/data_quality_summary.txt`).