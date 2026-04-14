-- ══════════════════════════════════════════════════════════════════════════
-- DORA Balance Score — métrica autoral (doc 04_analise_estrategica §4.4)
-- Razão entre velocidade (DF × 1/LT) e instabilidade (CFR × MTTR).
--   Score > 1.0 → velocidade cresce mais que instabilidade (saudável)
--   Score < 1.0 → instabilidade cresce mais que velocidade (problema)
-- Agregado mensal.
-- ══════════════════════════════════════════════════════════════════════════

WITH velocity AS (
    SELECT
        dt.year,
        dt.month_number,
        COUNT(f.deploy_id) / 30.0 AS daily_deploy_freq,
        1.0 / NULLIF(AVG(f.lead_time_minutes) / 60.0, 0) AS lead_time_inverse
    FROM {{SCHEMA}}.fato_deploys f
    JOIN {{SCHEMA}}.dim_time dt ON f.time_id = dt.time_id
    WHERE f.environment = 'production'
    GROUP BY dt.year, dt.month_number
),
stability AS (
    SELECT
        dt.year,
        dt.month_number,
        1.0 - (SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) AS cfr_health,
        1.0 / NULLIF(AVG(CASE WHEN f.is_rollback THEN f.recovery_time_minutes END) / 60.0, 0) AS mttr_inverse
    FROM {{SCHEMA}}.fato_deploys f
    JOIN {{SCHEMA}}.dim_time dt ON f.time_id = dt.time_id
    WHERE f.environment = 'production'
    GROUP BY dt.year, dt.month_number
)
SELECT
    v.year,
    v.month_number,
    ROUND(v.daily_deploy_freq, 2) AS deploy_freq,
    ROUND(v.lead_time_inverse, 3) AS speed_score,
    ROUND(s.cfr_health, 3) AS stability_score,
    ROUND(
        (v.daily_deploy_freq * v.lead_time_inverse) /
        NULLIF((1.0 - s.cfr_health) * (1.0 / NULLIF(s.mttr_inverse, 0)), 0),
        2
    ) AS dora_balance_score
FROM velocity v
JOIN stability s
    ON v.year = s.year AND v.month_number = s.month_number
ORDER BY v.year, v.month_number;
