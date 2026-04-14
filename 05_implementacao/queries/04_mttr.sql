-- ══════════════════════════════════════════════════════════════════════════
-- DORA #4 — Mean Time to Recovery
-- Tempo médio de recuperação após incidentes (só linhas com recovery preenchido).
-- Por nível de criticidade do repositório.
-- ══════════════════════════════════════════════════════════════════════════

SELECT
    dr.criticality_level,
    COUNT(*) AS total_incidents,
    ROUND(AVG(f.recovery_time_minutes), 1) AS avg_mttr_min,
    ROUND(AVG(f.recovery_time_minutes) / 60.0, 2) AS avg_mttr_h,
    ROUND(quantile_cont(f.recovery_time_minutes, 0.5) / 60.0, 2) AS median_mttr_h,
    ROUND(MAX(f.recovery_time_minutes) / 60.0, 2) AS max_mttr_h,
    CASE
        WHEN AVG(f.recovery_time_minutes) / 60.0 < 1.0   THEN 'Elite'
        WHEN AVG(f.recovery_time_minutes) / 60.0 < 24.0  THEN 'High'
        WHEN AVG(f.recovery_time_minutes) / 60.0 < 168.0 THEN 'Medium'
        ELSE 'Low'
    END AS dora_class
FROM {{SCHEMA}}.fato_deploys f
JOIN {{SCHEMA}}.dim_repository dr ON f.repository_id = dr.repository_id
WHERE f.recovery_time_minutes IS NOT NULL
  AND (f.is_rollback OR f.deploy_status IN ('failure', 'rolled_back'))
GROUP BY dr.criticality_level
ORDER BY
    CASE dr.criticality_level
        WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4
    END;
