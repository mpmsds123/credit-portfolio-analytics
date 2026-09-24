-- 01_portfolio_overview.sql
-- Question a business analyst gets on day one: "How big is the book and how
-- risky is it right now?" One row = the headline health of the portfolio.

SELECT
    COUNT(*)                                   AS accounts,
    ROUND(SUM(current_balance) / 1e6, 1)       AS total_balance_m_ntd,
    ROUND(AVG(credit_limit), 0)                AS avg_credit_limit,
    ROUND(AVG(utilization), 3)                 AS avg_utilization,
    ROUND(AVG(default_next_month), 4)          AS default_rate,
    -- Balance-weighted default rate: the number that actually drives losses,
    -- because a default on a large balance costs more than on a small one.
    ROUND(SUM(default_next_month * current_balance)
          / NULLIF(SUM(current_balance), 0), 4) AS bal_weighted_default_rate
FROM accounts;
