-- ══════════════════════════════════════════════════════════════════════════
-- TechFlow BI — Star Schema DDL
-- Implementa o modelo definido em 01_modelagem_dimensional.md
--
-- Placeholder {{SCHEMA}} é substituído em runtime por cenario_a|cenario_b|cenario_c.
-- ══════════════════════════════════════════════════════════════════════════

CREATE SCHEMA IF NOT EXISTS {{SCHEMA}};

-- ─────────────────────────────────────────────────────────────
-- DIMENSION — dim_time
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE {{SCHEMA}}.dim_time (
    time_id           INTEGER PRIMARY KEY,
    date_full         DATE       NOT NULL,
    day_of_week       INTEGER    NOT NULL,
    day_name          VARCHAR(15),
    week_number       INTEGER,
    month_number      INTEGER,
    month_name        VARCHAR(15),
    quarter           INTEGER,
    year              INTEGER,
    is_business_day   BOOLEAN,
    sprint_number     INTEGER,
    sprint_name       VARCHAR(50)
);

-- ─────────────────────────────────────────────────────────────
-- DIMENSION — dim_repository
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE {{SCHEMA}}.dim_repository (
    repository_id       INTEGER PRIMARY KEY,
    repo_name           VARCHAR(100) NOT NULL,
    repo_full_name      VARCHAR(200),
    squad               VARCHAR(50),
    tech_stack          VARCHAR(50),
    service_type        VARCHAR(20),
    criticality_level   VARCHAR(10),
    ai_adoption_level   VARCHAR(10),
    ai_tool_used        VARCHAR(30),
    adoption_date       DATE,
    total_contributors  INTEGER,
    creation_date       DATE
);

-- ─────────────────────────────────────────────────────────────
-- DIMENSION — dim_engineer
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE {{SCHEMA}}.dim_engineer (
    engineer_id        INTEGER PRIMARY KEY,
    full_name          VARCHAR(100),
    github_username    VARCHAR(50),
    role               VARCHAR(30),
    seniority_level    VARCHAR(5),
    squad              VARCHAR(50),
    uses_ai_tools      BOOLEAN,
    ai_tool_name       VARCHAR(30),
    ai_adoption_date   DATE,
    experience_years   INTEGER,
    hire_date          DATE,
    is_reviewer        BOOLEAN
);

-- ─────────────────────────────────────────────────────────────
-- FACT — fato_deploys
-- Granularidade: 1 linha = 1 evento de deploy
-- ─────────────────────────────────────────────────────────────
CREATE OR REPLACE TABLE {{SCHEMA}}.fato_deploys (
    deploy_id                 BIGINT PRIMARY KEY,
    time_id                   INTEGER NOT NULL,
    repository_id             INTEGER NOT NULL,
    engineer_id               INTEGER NOT NULL,
    timestamp_deploy          TIMESTAMP,
    lead_time_minutes         INTEGER,
    change_fail_rate          DOUBLE,
    recovery_time_minutes     INTEGER,
    is_rollback               BOOLEAN,
    is_hotfix                 BOOLEAN,
    lines_added               INTEGER,
    lines_removed             INTEGER,
    ai_generated_pct          DOUBLE,
    pr_review_time_minutes    INTEGER,
    num_comments_review       INTEGER,
    num_approvals             INTEGER,
    num_revisions_requested   INTEGER,
    deploy_status             VARCHAR(20),
    deploy_trigger            VARCHAR(20),
    environment               VARCHAR(20),
    pr_number                 INTEGER,
    pr_title                  VARCHAR(200)
);
