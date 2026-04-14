-- ══════════════════════════════════════════════════════════════════════════
-- DORA #1 — Deployment Frequency
-- Com que frequência a organização entrega com sucesso em produção.
-- Agregação: deploys/dia por squad (média sobre dias úteis do período).
-- ══════════════════════════════════════════════════════════════════════════

WITH periodo AS (
    SELECT
        MIN(dt.date_full) AS date_min,
        MAX(dt.date_full) AS date_max,
        COUNT(DISTINCT CASE WHEN dt.is_business_day THEN dt.date_full END) AS business_days
    FROM {{SCHEMA}}.fato_deploys f
    JOIN {{SCHEMA}}.dim_time dt ON f.time_id = dt.time_id
),
por_squad AS (
    SELECT
        dr.squad,
        COUNT(f.deploy_id) AS total_deploys,
        SUM(CASE WHEN f.deploy_status = 'success' THEN 1 ELSE 0 END) AS success_deploys
    FROM {{SCHEMA}}.fato_deploys f
    JOIN {{SCHEMA}}.dim_repository dr ON f.repository_id = dr.repository_id
    WHERE f.environment = 'production'
    GROUP BY dr.squad
)
SELECT
    s.squad,
    s.total_deploys,
    s.success_deploys,
    ROUND(s.success_deploys * 1.0 / p.business_days, 3) AS deploys_per_business_day,
    CASE
        WHEN s.success_deploys * 1.0 / p.business_days >= 1.0 THEN 'Elite'
        WHEN s.success_deploys * 1.0 / p.business_days >= (1.0/7.0) THEN 'High'
        WHEN s.success_deploys * 1.0 / p.business_days >= (1.0/30.0) THEN 'Medium'
        ELSE 'Low'
    END AS dora_class
FROM por_squad s, periodo p
ORDER BY deploys_per_business_day DESC;
