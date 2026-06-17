-- ============================================================
-- Bluestock MF Capstone - Analytical SQL Queries
-- 10 queries answering key business questions using the star
-- schema defined in schema.sql
-- ============================================================

-- ----------------------------------------------------------
-- Query 1: Top 5 funds by AUM (from fact_performance, latest snapshot)
-- ----------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;

-- ----------------------------------------------------------
-- Query 2: Average NAV per month, across all funds
-- ----------------------------------------------------------
SELECT
    strftime('%Y-%m', nav_date) AS month,
    ROUND(AVG(nav_value), 2) AS avg_nav
FROM fact_nav
GROUP BY month
ORDER BY month;

-- ----------------------------------------------------------
-- Query 3: SIP year-over-year growth (using fact_sip's
-- pre-computed yoy_growth_pct column)
-- ----------------------------------------------------------
SELECT
    strftime('%Y-%m', month_year) AS month,
    sip_inflow_crore,
    yoy_growth_pct
FROM fact_sip
WHERE yoy_growth_pct IS NOT NULL
ORDER BY month_year;

-- ----------------------------------------------------------
-- Query 4: Total transaction amount by state
-- ----------------------------------------------------------
SELECT
    i.state,
    COUNT(*) AS num_transactions,
    SUM(t.amount_inr) AS total_amount_inr
FROM fact_transactions t
JOIN dim_investor i ON t.investor_id = i.investor_id
GROUP BY i.state
ORDER BY total_amount_inr DESC;

-- ----------------------------------------------------------
-- Query 5: Funds with expense_ratio_pct < 1%
-- ----------------------------------------------------------
SELECT
    scheme_name,
    fund_house,
    expense_ratio_pct
FROM dim_fund
WHERE expense_ratio_pct < 1.0
ORDER BY expense_ratio_pct ASC;

-- ----------------------------------------------------------
-- Query 6: Monthly redemption volume (to spot tax-harvesting spikes)
-- ----------------------------------------------------------
SELECT
    strftime('%Y-%m', transaction_date) AS month,
    SUM(amount_inr) AS total_redemption_inr,
    COUNT(*) AS num_redemptions
FROM fact_transactions
WHERE transaction_type = 'Redemption'
GROUP BY month
ORDER BY month;

-- ----------------------------------------------------------
-- Query 7: Top 5 categories by net inflow in FY 2024-25
-- (FY25 = April 2024 to March 2025)
-- ----------------------------------------------------------
SELECT
    category,
    SUM(net_inflow_crore) AS total_net_inflow_crore
FROM fact_category_inflows
WHERE month_year BETWEEN '2024-04-01' AND '2025-03-31'
GROUP BY category
ORDER BY total_net_inflow_crore DESC
LIMIT 5;

-- ----------------------------------------------------------
-- Query 8: Investor count and average SIP amount by age group
-- ----------------------------------------------------------
SELECT
    i.age_group,
    COUNT(DISTINCT i.investor_id) AS num_investors,
    ROUND(AVG(t.amount_inr), 2) AS avg_transaction_amount
FROM fact_transactions t
JOIN dim_investor i ON t.investor_id = i.investor_id
WHERE t.transaction_type = 'SIP'
GROUP BY i.age_group
ORDER BY avg_transaction_amount DESC;

-- ----------------------------------------------------------
-- Query 9: Average SIP amount by city tier
-- ----------------------------------------------------------
SELECT
    i.city_tier,
    COUNT(*) AS num_sip_transactions,
    ROUND(AVG(t.amount_inr), 2) AS avg_sip_amount
FROM fact_transactions t
JOIN dim_investor i ON t.investor_id = i.investor_id
WHERE t.transaction_type = 'SIP'
GROUP BY i.city_tier
ORDER BY avg_sip_amount DESC;

-- ----------------------------------------------------------
-- Query 10: Fund count by risk grade
-- ----------------------------------------------------------
SELECT
    risk_category,
    COUNT(*) AS num_funds
FROM dim_fund
GROUP BY risk_category
ORDER BY num_funds DESC;