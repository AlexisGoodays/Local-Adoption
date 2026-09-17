-- ============================================================
-- Module E-réputation Google — détail. Méthodo miroir d'Insight.
-- Tous les comptes sont éligibles (pas de filtre customer au niveau module).
--
-- Actif E-réputation = >=1 activité BO ∈ ('Metric · GOOGLE_SCORE','Metric · GOOGLE_BENCHMARK').
-- 2 fonctionnalités :
--   - Note Google         -> Metric · GOOGLE_SCORE     (accès : administre >=1 place mappée fiche Google)
--   - Benchmark concurrentiel -> Metric · GOOGLE_BENCHMARK (accès : DIM_CUSTOMERS.EREP_BENCH_ENABLED)
-- Accessibilité appliquée UNIQUEMENT au bloc "Usage par fonctionnalité" (dénominateurs) — option "split".
-- ============================================================

CREATE OR REPLACE TABLE REPORTING.ADOPTION.FCT_EREP_USER_DAY AS
WITH scoped AS (
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED
)
SELECT
    ba.USERNAME, ba.CUSTOMER_ID, ba.OCCURRING_DATE AS ACTIVITY_DATE,
    COUNT_IF(ba.BO_ACTIVITY_NAME = 'Metric · GOOGLE_SCORE')     AS N_SCORE,
    COUNT_IF(ba.BO_ACTIVITY_NAME = 'Metric · GOOGLE_BENCHMARK') AS N_BENCHMARK,
    TRUE AS IS_ACTIVE_EREP
FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES ba
JOIN scoped s ON s.USERNAME = ba.USERNAME AND s.CUSTOMER_ID = ba.CUSTOMER_ID
WHERE ba.OCCURRING_DATE >= DATEADD('day', -300, CURRENT_DATE)
  AND ba.BO_ACTIVITY_NAME IN ('Metric · GOOGLE_SCORE', 'Metric · GOOGLE_BENCHMARK')
GROUP BY 1, 2, 3;

-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_DAILY AS
SELECT
    CUSTOMER_ID, ACTIVITY_DATE,
    COUNT(DISTINCT USERNAME)                              AS active_users,
    COUNT(DISTINCT IFF(N_SCORE > 0, USERNAME, NULL))      AS score_users,
    COUNT(DISTINCT IFF(N_BENCHMARK > 0, USERNAME, NULL))  AS bench_users,
    SUM(N_SCORE)     AS score_actions,
    SUM(N_BENCHMARK) AS bench_actions
FROM REPORTING.ADOPTION.FCT_EREP_USER_DAY
WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE)
GROUP BY 1, 2;

-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_USER_30D AS
WITH f AS (
    SELECT USERNAME, CUSTOMER_ID,
        SUM(N_SCORE)                   AS score,
        SUM(N_BENCHMARK)               AS benchmark,
        SUM(N_SCORE) + SUM(N_BENCHMARK) AS erep_actions
    FROM REPORTING.ADOPTION.FCT_EREP_USER_DAY
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE)
    GROUP BY 1, 2
)
SELECT f.USERNAME, f.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY,
    s.N_ADMIN_PLACES, s.CAN_GOOGLE_SCORE, c.EREP_BENCH_ENABLED,
    f.score, f.benchmark, f.erep_actions, TRUE AS is_active
FROM f
JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    ON s.USERNAME = f.USERNAME AND s.CUSTOMER_ID = f.CUSTOMER_ID
JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = f.CUSTOMER_ID;

-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D AS
WITH cust AS (
    SELECT CUSTOMER_ID, CUSTOMER_NAME, EREP_BENCH_ENABLED FROM REPORTING.ADOPTION.DIM_CUSTOMERS
),
roster AS (
    SELECT CUSTOMER_ID, COUNT(*) AS roster FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED GROUP BY 1
),
conn AS (   -- connectés 30 j + accès score
    SELECT f.CUSTOMER_ID,
        COUNT(DISTINCT f.USERNAME) AS connected_users,
        COUNT(DISTINCT IFF(s.CAN_GOOGLE_SCORE, f.USERNAME, NULL)) AS connected_score_access
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s ON s.USERNAME = f.USERNAME AND s.CUSTOMER_ID = f.CUSTOMER_ID
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
    GROUP BY 1
),
ins AS (
    SELECT CUSTOMER_ID,
        COUNT(DISTINCT IFF(is_active,    USERNAME, NULL)) AS active_erep_users,
        COUNT(DISTINCT IFF(score > 0,    USERNAME, NULL)) AS score_users,
        COUNT(DISTINCT IFF(benchmark > 0, USERNAME, NULL)) AS bench_users,
        SUM(score) AS score_actions, SUM(benchmark) AS bench_actions
    FROM REPORTING.ADOPTION.MART_EREP_USER_30D GROUP BY 1
)
SELECT
    ct.CUSTOMER_ID, ct.CUSTOMER_NAME, ct.EREP_BENCH_ENABLED,
    COALESCE(r.roster, 0)              AS roster,
    COALESCE(cn.connected_users, 0)    AS connected_users,
    COALESCE(cn.connected_score_access, 0) AS connected_score_access,
    IFF(ct.EREP_BENCH_ENABLED, COALESCE(cn.connected_users, 0), 0) AS connected_bench_access,
    COALESCE(i.active_erep_users, 0)   AS active_erep_users,
    GREATEST(COALESCE(cn.connected_users, 0) - COALESCE(i.active_erep_users, 0), 0) AS connected_zero_erep,
    COALESCE(i.score_users, 0) AS score_users,
    COALESCE(i.bench_users, 0) AS bench_users,
    COALESCE(i.score_actions, 0) AS score_actions,
    COALESCE(i.bench_actions, 0) AS bench_actions
FROM cust ct
LEFT JOIN roster r ON r.CUSTOMER_ID = ct.CUSTOMER_ID
LEFT JOIN conn   cn ON cn.CUSTOMER_ID = ct.CUSTOMER_ID
LEFT JOIN ins    i ON i.CUSTOMER_ID = ct.CUSTOMER_ID
WHERE r.roster > 0;

-- MART_EREP_UNIT_30D a été déplacée dans sql/build_hierarchy.sql (option B,
-- cf. build_insight.sql pour le contexte de la décision).

-- ------------------------------------------------------------
-- Fait quotidien 300 j (filtre de période) + dim utilisateurs
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_DAILY_USER AS
SELECT USERNAME, CUSTOMER_ID, ACTIVITY_DATE, N_SCORE, N_BENCHMARK
FROM REPORTING.ADOPTION.FCT_EREP_USER_DAY
WHERE (N_SCORE + N_BENCHMARK) > 0;

CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_EREP_USER AS
SELECT s.USERNAME, s.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY, s.N_ADMIN_PLACES,
    s.CAN_GOOGLE_SCORE, c.EREP_BENCH_ENABLED,
    s.SAL_PLACE, s.SAL_ZONE, s.SAL_SECTOR, s.SAL_SUBTYPE, s.SAL_REGION,
    s.SAL_DEPARTMENT, s.SAL_COUNTRY, s.SAL_TYPE, s.SAL_BRAND
FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = s.CUSTOMER_ID
WHERE EXISTS (
    SELECT 1 FROM REPORTING.ADOPTION.MART_EREP_DAILY_USER d
    WHERE d.USERNAME = s.USERNAME AND d.CUSTOMER_ID = s.CUSTOMER_ID
);
