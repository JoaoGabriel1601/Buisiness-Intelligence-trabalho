-- ══════════════════════════════════════════════════════════════════════════
-- IA × Qualidade — análise correlacional
-- Para cada faixa de % de código IA, mede: lead time, review time,
-- comentários, revisões solicitadas e taxa de falhas.
-- ══════════════════════════════════════════════════════════════════════════

SELECT
    CASE
        WHEN f.ai_generated_pct >= 0.7 THEN 'Alta IA (>=70%)'
        WHEN f.ai_generated_pct >= 0.3 THEN 'Media IA (30-70%)'
        ELSE 'Baixa IA (<30%)'
    END AS ai_band,
    COUNT(*) AS n_deploys,
    ROUND(AVG(f.lead_time_minutes) / 60.0, 2) AS avg_lead_time_h,
    ROUND(AVG(f.pr_review_time_minutes) / 60.0, 2) AS avg_review_time_h,
    ROUND(AVG(f.num_comments_review), 1) AS avg_comments,
    ROUND(AVG(f.num_revisions_requested), 1) AS avg_revisions,
    ROUND(
        SUM(CASE WHEN f.is_rollback OR f.deploy_status = 'failure' THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        2
    ) AS failure_rate_pct
FROM {{SCHEMA}}.fato_deploys f
WHERE f.environment = 'production'
GROUP BY ai_band
ORDER BY ai_band;
