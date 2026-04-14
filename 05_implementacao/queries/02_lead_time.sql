-- ══════════════════════════════════════════════════════════════════════════
-- DORA #2 — Lead Time for Changes
-- Tempo entre o primeiro commit e o deploy em produção.
-- Compara pré- vs pós-adoção de IA, agregando squads.
-- ══════════════════════════════════════════════════════════════════════════

SELECT
    CASE
        WHEN dt.date_full < DATE '2025-03-01' THEN 'pre_ia'
        ELSE 'pos_ia'
    END AS periodo,
    COUNT(*) AS n_deploys,
    ROUND(AVG(f.lead_time_minutes) / 60.0, 2) AS avg_lead_time_h,
    ROUND(quantile_cont(f.lead_time_minutes, 0.5) / 60.0, 2) AS median_lead_time_h,
    ROUND(quantile_cont(f.lead_time_minutes, 0.95) / 60.0, 2) AS p95_lead_time_h,
    CASE
        WHEN AVG(f.lead_time_minutes) / 60.0 < 1.0  THEN 'Elite'
        WHEN AVG(f.lead_time_minutes) / 60.0 < 24.0 THEN 'High'
        WHEN AVG(f.lead_time_minutes) / 60.0 < 168.0 THEN 'Medium'
        ELSE 'Low'
    END AS dora_class
FROM {{SCHEMA}}.fato_deploys f
JOIN {{SCHEMA}}.dim_time dt ON f.time_id = dt.time_id
WHERE f.environment = 'production'
GROUP BY periodo
ORDER BY periodo;
