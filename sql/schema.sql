-- ============================================================
-- Bluestock MF Capstone - Star Schema
-- SQLite database schema for mutual fund analytics platform
-- ============================================================

-- ----------------------------------------------------------
-- DIMENSION TABLE: dim_fund
-- One row per AMFI scheme (40 funds)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           INTEGER PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT NOT NULL,
    sub_category        TEXT NOT NULL,
    plan                TEXT,
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,
    sebi_category_code  TEXT
);

-- ----------------------------------------------------------
-- DIMENSION TABLE: dim_date
-- One row per calendar date covering the full project range
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      TEXT PRIMARY KEY,   -- ISO format YYYY-MM-DD
    full_date    DATE NOT NULL,
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    month_name   TEXT NOT NULL,
    day          INTEGER NOT NULL,
    day_of_week  TEXT NOT NULL,
    is_weekend   INTEGER NOT NULL    -- 0 or 1
);

-- ----------------------------------------------------------
-- DIMENSION TABLE: dim_investor
-- One row per unique investor, derived from investor_transactions
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_investor (
    investor_id          TEXT PRIMARY KEY,
    state                TEXT,
    city                 TEXT,
    city_tier            TEXT,
    age_group            TEXT,
    gender               TEXT,
    annual_income_lakh   REAL,
    kyc_status           TEXT
);

-- ----------------------------------------------------------
-- FACT TABLE: fact_nav
-- Daily NAV per scheme (grain: one row per amfi_code + date)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code    INTEGER NOT NULL,
    nav_date     DATE NOT NULL,
    nav_value    REAL NOT NULL,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi_date ON fact_nav(amfi_code, nav_date);

-- ----------------------------------------------------------
-- FACT TABLE: fact_transactions
-- One row per investor transaction (SIP/Lumpsum/Redemption)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT NOT NULL,
    transaction_date    DATE NOT NULL,
    amfi_code           INTEGER NOT NULL,
    transaction_type    TEXT NOT NULL,   -- SIP / Lumpsum / Redemption
    amount_inr          INTEGER NOT NULL,
    payment_mode        TEXT,
    FOREIGN KEY (investor_id) REFERENCES dim_investor(investor_id),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX IF NOT EXISTS idx_fact_txn_amfi ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_txn_investor ON fact_transactions(investor_id);
CREATE INDEX IF NOT EXISTS idx_fact_txn_date ON fact_transactions(transaction_date);

-- ----------------------------------------------------------
-- FACT TABLE: fact_performance
-- One row per scheme - pre-computed performance metrics
-- (used for validation against Day 4 notebook calculations)
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code           INTEGER NOT NULL,
    return_1yr_pct      REAL,
    return_3yr_pct      REAL,
    return_5yr_pct      REAL,
    benchmark_3yr_pct   REAL,
    alpha               REAL,
    beta                REAL,
    sharpe_ratio        REAL,
    sortino_ratio       REAL,
    std_dev_ann_pct     REAL,
    max_drawdown_pct    REAL,
    aum_crore           INTEGER,
    expense_ratio_pct   REAL,
    morningstar_rating  INTEGER,
    risk_grade          TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX IF NOT EXISTS idx_fact_perf_amfi ON fact_performance(amfi_code);

-- ----------------------------------------------------------
-- FACT TABLE: fact_aum
-- Quarterly AUM by fund house
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    quarter_date     DATE NOT NULL,
    fund_house       TEXT NOT NULL,
    aum_lakh_crore   REAL NOT NULL,
    aum_crore        INTEGER NOT NULL,
    num_schemes      INTEGER
);
CREATE INDEX IF NOT EXISTS idx_fact_aum_house_date ON fact_aum(fund_house, quarter_date);

-- ----------------------------------------------------------
-- FACT TABLE: fact_sip
-- Monthly industry-wide SIP inflow statistics
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sip (
    sip_id                       INTEGER PRIMARY KEY AUTOINCREMENT,
    month_year                   DATE NOT NULL,
    sip_inflow_crore             INTEGER NOT NULL,
    active_sip_accounts_crore    REAL,
    new_sip_accounts_lakh        REAL,
    sip_aum_lakh_crore           REAL,
    yoy_growth_pct               REAL
);
CREATE INDEX IF NOT EXISTS idx_fact_sip_month ON fact_sip(month_year);

-- ----------------------------------------------------------
-- FACT TABLE: fact_category_inflows
-- Monthly net inflows by fund category
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    inflow_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    month_year           DATE NOT NULL,
    category            TEXT NOT NULL,
    net_inflow_crore     REAL
);
CREATE INDEX IF NOT EXISTS idx_fact_cat_inflow_month ON fact_category_inflows(month_year);

-- ----------------------------------------------------------
-- FACT TABLE: fact_folio_count
-- Quarterly industry-wide folio counts
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_folio_count (
    folio_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    month_year              DATE NOT NULL,
    total_folios_crore     REAL NOT NULL,
    equity_folios_crore    REAL,
    debt_folios_crore      REAL,
    hybrid_folios_crore    REAL,
    others_folios_crore    REAL
);

-- ----------------------------------------------------------
-- FACT TABLE: fact_holdings
-- Top stock holdings per equity fund
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_holdings (
    holding_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code            INTEGER NOT NULL,
    stock_symbol         TEXT,
    stock_name           TEXT,
    sector               TEXT,
    weight_pct           REAL,
    market_value_cr      REAL,
    current_price_inr    REAL,
    portfolio_date       DATE,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund(amfi_code)
);
CREATE INDEX IF NOT EXISTS idx_fact_holdings_amfi ON fact_holdings(amfi_code);

-- ----------------------------------------------------------
-- FACT TABLE: fact_benchmark
-- Daily closing values for benchmark indices
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_benchmark (
    benchmark_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    index_date       DATE NOT NULL,
    index_name       TEXT NOT NULL,
    close_value      REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_fact_benchmark_name_date ON fact_benchmark(index_name, index_date);