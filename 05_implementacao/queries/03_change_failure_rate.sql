-- ══════════════════════════════════════════════════════════════════════════
-- DORA #3 — Change Failure Rate
-- % de deploys em produção que falham ou exigem rollback.
-- Segmentado por faixa de código gerado por IA.
-- ══════════════════════════════════════════════════════════════════════════

SELECT
    CASE
        WHEN f.ai_generated_pct >= 0.7 THEN 'Alta IA (>=70%)'
        WHEN f.ai_generated_pct >= 0.3 THEN 'Media IA (30-70%)'
        ELSE 'Baixa IA (<30%)'
    END AS ai_band,
    COUNT(*) AS total_deploys,
    SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) AS failed_deploys,
    ROUND(
        SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS cfr_pct,
    CASE
        WHEN SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) < 0.05 THEN 'Elite'
        WHEN SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) < 0.10 THEN 'High'
        WHEN SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 1.0 / COUNT(*) < 0.15 THEN 'Medium'
        ELSE 'Low'
    END AS dora_class
FROM {{SCHEMA}}.fato_deploys f
WHERE f.environment = 'production'
GROUP BY ai_band
ORDER BY ai_band;
