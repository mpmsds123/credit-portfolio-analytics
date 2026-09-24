-- 04_risk_return_pricing.sql
-- The money question: for each risk grade, is the segment profitable, and at
-- what price? This is a simplified unit-economics model built entirely in SQL
-- so the logic is auditable line by line. Full assumptions live in the README.
--
-- Per-account annual economics:
--   expected_loss    = PD * EAD * LGD
--   expected_revenue = APR * revolving_balance + annual_fee_equiv
--   expected_profit  = expected_revenue - expected_loss - servicing_cost
--
-- Assumptions (documented, swappable):
--   LGD              = 0.90   (unsecured card, low recovery)
--   APR              = 0.22   (blended revolving APR)
--   servicing_cost   = 120    NT$/yr per account
--   annual_fee_equiv = 0      (no fee product in this scenario)
--   EAD proxy        = current_balance
--   revolving_balance= current_balance (interest-earning portion)

WITH params AS (
    SELECT 0.90 AS lgd, 0.22 AS apr, 120.0 AS servicing_cost, 0.0 AS annual_fee
),
segment AS (
    SELECT
        risk_grade,
        COUNT(*)                 AS accounts,
        AVG(default_next_month)  AS pd,
        AVG(current_balance)     AS ead,
        AVG(current_balance)     AS revolving_balance
    FROM accounts
    GROUP BY risk_grade
)
SELECT
    s.risk_grade,
    s.accounts,
    ROUND(s.pd, 4)                                            AS pd,
    ROUND(s.ead, 0)                                           AS avg_exposure,
    ROUND(s.pd * s.ead * p.lgd, 0)                            AS expected_loss,
    ROUND(p.apr * s.revolving_balance + p.annual_fee, 0)      AS expected_revenue,
    ROUND(p.apr * s.revolving_balance + p.annual_fee
          - s.pd * s.ead * p.lgd - p.servicing_cost, 0)       AS expected_profit_per_acct,
    -- Break-even APR: the price at which this segment stops losing money.
    ROUND((s.pd * s.ead * p.lgd + p.servicing_cost)
          / NULLIF(s.revolving_balance, 0), 4)                AS breakeven_apr,
    CASE
        WHEN p.apr * s.revolving_balance + p.annual_fee
             - s.pd * s.ead * p.lgd - p.servicing_cost > 0
        THEN 'APPROVE'
        ELSE 'DECLINE_or_REPRICE'
    END                                                       AS recommendation
FROM segment s CROSS JOIN params p
ORDER BY s.risk_grade;
