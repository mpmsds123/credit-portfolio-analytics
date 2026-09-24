-- 02_segment_default_rates.sql
-- Where does risk concentrate? Slice default rate by the behavioral segments
-- an underwriter actually controls: risk grade, credit-limit tier, utilization.
-- These are the levers for approve / decline / price decisions.

-- (a) By behavioral risk grade (delinquency history) -------------------------
SELECT
    risk_grade,
    COUNT(*)                          AS accounts,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_book,
    ROUND(AVG(default_next_month), 4) AS default_rate,
    ROUND(AVG(credit_limit), 0)       AS avg_limit
FROM accounts
GROUP BY risk_grade
ORDER BY risk_grade;

-- (b) By credit-limit tier ---------------------------------------------------
SELECT
    limit_tier,
    COUNT(*)                          AS accounts,
    ROUND(AVG(default_next_month), 4) AS default_rate,
    ROUND(AVG(utilization), 3)        AS avg_utilization
FROM accounts
GROUP BY limit_tier
ORDER BY limit_tier;

-- (c) Risk grade x utilization band: the interaction is where the sharpest
--     signal lives (a maxed-out, already-delinquent account is the worst box).
SELECT
    risk_grade,
    util_band,
    COUNT(*)                          AS accounts,
    ROUND(AVG(default_next_month), 4) AS default_rate
FROM accounts
GROUP BY risk_grade, util_band
ORDER BY risk_grade, util_band;
