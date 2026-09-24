-- 03_delinquency_migration.sql
-- Early-warning view. How does the most recent month's delinquency status
-- (PAY_1 = September) map to next-month default? This is the single strongest
-- predictor and the backbone of any behavioral scorecard.

SELECT
    PAY_0 AS current_delinquency_status,   -- PAY_0 = September status. -2/-1/0 = paid/no balance, n = n months past due
    COUNT(*)                                  AS accounts,
    ROUND(AVG("default.payment.next.month"), 4) AS default_rate_next_month,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_book
FROM accounts_raw
GROUP BY PAY_0
ORDER BY PAY_0;

-- Payment behavior: do accounts that pay more of their bill default less?
-- Buckets the payment ratio to show the monotonic protective effect.
SELECT
    CASE
        WHEN payment_ratio < 0.05 THEN '0-5%_min_or_none'
        WHEN payment_ratio < 0.20 THEN '5-20%'
        WHEN payment_ratio < 0.60 THEN '20-60%'
        ELSE '60%+_toward_full'
    END                               AS payment_ratio_band,
    COUNT(*)                          AS accounts,
    ROUND(AVG(default_next_month), 4) AS default_rate
FROM accounts
GROUP BY payment_ratio_band
ORDER BY default_rate DESC;
