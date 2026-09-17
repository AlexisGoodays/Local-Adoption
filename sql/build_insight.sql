-- ============================================================
-- Module Insight — détail (Écran 3).
-- Socle = DIM_PRO_USERS_SCOPED restreint aux customers IS_INSIGHT_ELIGIBLE
--   (SEMANTIC_CLASSIFICATION_PLAN non nul et ne commençant pas par "-").
-- Grain : user x customer x jour, 180 j glissants.
--
-- Features (V1, définitions Alexis 2026-09-03) :
--   - Quick Overview     -> table ANALYTICS.TOPIC_OVERVIEW_CONSULTATIONS (1 ligne = 1 consultation)
--   - Carte de synthèse  -> BO_ACTIVITIES  BO_ACTIVITY_NAME = 'Topic drill-down · overview'
--   - Page thématique    -> BO_ACTIVITIES  BO_ACTIVITY_NAME IN
--                           ('Metric · SENTIMENT','Metric · SENTIMENT_OVERVIEW','Topic drill-down · thematic')
--
-- "Actif Insight" (niveau module) = actif sur >=1 des 3 features OU page vue monitored.
-- "Actions Insight" (volume ranking / top / drop-off) = somme des actions des 3 features.
-- ============================================================

CREATE OR REPLACE TABLE REPORTING.ADOPTION.FCT_INSIGHT_USER_DAY AS
WITH scoped AS (
    SELECT s.USERNAME, s.CUSTOMER_ID
    FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = s.CUSTOMER_ID
    WHERE c.IS_INSIGHT_ELIGIBLE
),
ba AS (   -- signaux BO_ACTIVITIES
    SELECT
        a.USERNAME, a.CUSTOMER_ID, a.OCCURRING_DATE AS d,
        COUNT_IF(a.INSIGHT_MONITORING_STATUS = 'monitored')          AS n_monitored_actions,
        COUNT_IF(a.BO_ACTIVITY_NAME = 'Topic drill-down · overview')  AS n_synthesis,
        COUNT_IF(a.BO_ACTIVITY_NAME IN ('Metric · SENTIMENT','Metric · SENTIMENT_OVERVIEW','Topic drill-down · thematic')) AS n_thematic
    FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES a
    JOIN scoped s ON s.USERNAME = a.USERNAME AND s.CUSTOMER_ID = a.CUSTOMER_ID
    WHERE a.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
),
toc AS (  -- Quick Overview = consultations de résumés IA
    SELECT
        t.USERNAME, t.CUSTOMER_ID, t.OCCURRING_DATE AS d,
        COUNT(*) AS n_overview
    FROM MARTING_BUSINESS.ANALYTICS.TOPIC_OVERVIEW_CONSULTATIONS t
    JOIN scoped s ON s.USERNAME = t.USERNAME AND s.CUSTOMER_ID = t.CUSTOMER_ID
    WHERE t.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
),
pv AS (   -- pages vues monitored
    SELECT
        bpv.USERNAME, bpv.CUSTOMER_ID, bpv.OCCURRING_DATE AS d,
        COUNT_IF(bpv.INSIGHT_MONITORING_STATUS = 'monitored') AS n_monitored_views
    FROM MARTING_BUSINESS.ANALYTICS.BO_WEB_PAGE_VIEWS bpv
    JOIN scoped s ON s.USERNAME = bpv.USERNAME AND s.CUSTOMER_ID = bpv.CUSTOMER_ID
    WHERE bpv.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
),
keys AS (
    SELECT USERNAME, CUSTOMER_ID, d FROM ba
    UNION SELECT USERNAME, CUSTOMER_ID, d FROM toc
    UNION SELECT USERNAME, CUSTOMER_ID, d FROM pv
)
SELECT
    k.USERNAME, k.CUSTOMER_ID, k.d AS ACTIVITY_DATE,
    COALESCE(ba.n_monitored_actions, 0) AS N_MONITORED_ACTIONS,  -- info : pages/actions "monitored" en BO_ACTIVITIES
    COALESCE(toc.n_overview, 0)         AS N_OVERVIEW,            -- Quick Overview
    COALESCE(ba.n_synthesis, 0)         AS N_SYNTHESIS,           -- Carte de synthèse
    COALESCE(ba.n_thematic, 0)          AS N_THEMATIC,            -- Page thématique
    COALESCE(pv.n_monitored_views, 0)   AS N_MONITORED_VIEWS,
    (COALESCE(toc.n_overview, 0) > 0
        OR COALESCE(ba.n_synthesis, 0) > 0
        OR COALESCE(ba.n_thematic, 0) > 0
        OR COALESCE(pv.n_monitored_views, 0) > 0) AS IS_ACTIVE_INSIGHT
FROM keys k
LEFT JOIN ba  ON ba.USERNAME = k.USERNAME  AND ba.CUSTOMER_ID = k.CUSTOMER_ID  AND ba.d = k.d
LEFT JOIN toc ON toc.USERNAME = k.USERNAME AND toc.CUSTOMER_ID = k.CUSTOMER_ID AND toc.d = k.d
LEFT JOIN pv  ON pv.USERNAME = k.USERNAME  AND pv.CUSTOMER_ID = k.CUSTOMER_ID  AND pv.d = k.d;


-- ------------------------------------------------------------
-- MART_INSIGHT_DAILY — série quotidienne 90 j (grain customer x jour)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_DAILY AS
SELECT
    CUSTOMER_ID,
    ACTIVITY_DATE,
    COUNT(DISTINCT IFF(IS_ACTIVE_INSIGHT, USERNAME, NULL)) AS active_users,
    COUNT(DISTINCT IFF(N_OVERVIEW  > 0, USERNAME, NULL))   AS overview_users,
    COUNT(DISTINCT IFF(N_THEMATIC  > 0, USERNAME, NULL))   AS thematic_users,
    COUNT(DISTINCT IFF(N_SYNTHESIS > 0, USERNAME, NULL))   AS synthesis_users,
    SUM(N_OVERVIEW)  AS overview_actions,
    SUM(N_THEMATIC)  AS thematic_actions,
    SUM(N_SYNTHESIS) AS synthesis_actions
FROM REPORTING.ADOPTION.FCT_INSIGHT_USER_DAY
WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE)
GROUP BY 1, 2
HAVING active_users > 0;

-- ------------------------------------------------------------
-- MART_INSIGHT_USER_30D — 1 ligne par utilisateur AVEC signal Insight (30 j)
-- insight_actions = somme des actions des 3 features
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_USER_30D AS
WITH f AS (
    SELECT USERNAME, CUSTOMER_ID,
        SUM(N_OVERVIEW)  AS overview,
        SUM(N_THEMATIC)  AS thematic,
        SUM(N_SYNTHESIS) AS synthesis,
        SUM(N_OVERVIEW) + SUM(N_THEMATIC) + SUM(N_SYNTHESIS) AS insight_actions,
        SUM(N_MONITORED_VIEWS) AS monitored_views,
        BOOLOR_AGG(IS_ACTIVE_INSIGHT) AS is_active
    FROM REPORTING.ADOPTION.FCT_INSIGHT_USER_DAY
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE)
    GROUP BY 1, 2
    HAVING (SUM(N_OVERVIEW)+SUM(N_THEMATIC)+SUM(N_SYNTHESIS)+SUM(N_MONITORED_VIEWS)) > 0
)
SELECT f.USERNAME, f.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY,
    s.N_ADMIN_PLACES,   -- nb de places administrées (ANALYTICS.PLACE_ADMINISTRATIONS)
    f.insight_actions, f.overview, f.thematic, f.synthesis, f.monitored_views, f.is_active
FROM f
JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    ON s.USERNAME = f.USERNAME AND s.CUSTOMER_ID = f.CUSTOMER_ID;

-- ------------------------------------------------------------
-- MART_INSIGHT_CUSTOMER_30D — 1 ligne par customer éligible (30 j)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D AS
WITH elig AS (
    SELECT CUSTOMER_ID, CUSTOMER_NAME FROM REPORTING.ADOPTION.DIM_CUSTOMERS WHERE IS_INSIGHT_ELIGIBLE
),
roster AS (
    SELECT CUSTOMER_ID, COUNT(*) AS roster FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED GROUP BY 1
),
conn AS (
    SELECT CUSTOMER_ID, COUNT(DISTINCT USERNAME) AS connected_users
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND IS_CONNECTED
    GROUP BY 1
),
ins AS (
    SELECT CUSTOMER_ID,
        COUNT(DISTINCT IFF(is_active,     USERNAME, NULL)) AS active_insight_users,
        COUNT(DISTINCT IFF(overview  > 0, USERNAME, NULL)) AS overview_users,
        COUNT(DISTINCT IFF(thematic  > 0, USERNAME, NULL)) AS thematic_users,
        COUNT(DISTINCT IFF(synthesis > 0, USERNAME, NULL)) AS synthesis_users,
        SUM(overview) AS overview_actions, SUM(thematic) AS thematic_actions,
        SUM(synthesis) AS synthesis_actions
    FROM REPORTING.ADOPTION.MART_INSIGHT_USER_30D GROUP BY 1
)
SELECT
    e.CUSTOMER_ID, e.CUSTOMER_NAME,
    COALESCE(r.roster, 0)              AS roster,
    COALESCE(c.connected_users, 0)     AS connected_users,
    COALESCE(i.active_insight_users, 0) AS active_insight_users,
    GREATEST(COALESCE(c.connected_users, 0) - COALESCE(i.active_insight_users, 0), 0) AS connected_zero_insight,
    COALESCE(i.overview_users, 0)  AS overview_users,
    COALESCE(i.thematic_users, 0)  AS thematic_users,
    COALESCE(i.synthesis_users, 0) AS synthesis_users,
    COALESCE(i.overview_actions, 0)  AS overview_actions,
    COALESCE(i.thematic_actions, 0)  AS thematic_actions,
    COALESCE(i.synthesis_actions, 0) AS synthesis_actions
FROM elig e
LEFT JOIN roster r ON r.CUSTOMER_ID = e.CUSTOMER_ID
LEFT JOIN conn   c ON c.CUSTOMER_ID = e.CUSTOMER_ID
LEFT JOIN ins    i ON i.CUSTOMER_ID = e.CUSTOMER_ID;


-- MART_INSIGHT_UNIT_30D a été déplacée dans sql/build_hierarchy.sql (option B,
-- rattachement hiérarchique via DIM_USER_UNIT — cf. décision Alexis 2026-09-16
-- suite au constat que l'option A "single administrated" ne remonte que
-- l'administrateur direct d'un niveau, pas tous les utilisateurs qui en
-- dépendent). Elle doit donc être (re)créée APRÈS build_hierarchy.sql.

-- ------------------------------------------------------------
-- MART_INSIGHT_USER_PLACES — noms des places administrées par utilisateur (30 j actifs)
-- Source : ANALYTICS.PLACE_ADMINISTRATIONS x ANALYTICS.PLACES. 50 premiers noms max.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_USER_PLACES AS
WITH act AS (SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.MART_INSIGHT_USER_30D),
pl AS (
    SELECT pa.USERNAME, pa.CUSTOMER_ID, p.PLACE_NAME
    FROM MARTING_BUSINESS.ANALYTICS.PLACE_ADMINISTRATIONS pa
    JOIN act a ON a.USERNAME = pa.USERNAME AND a.CUSTOMER_ID = pa.CUSTOMER_ID
    JOIN MARTING_BUSINESS.ANALYTICS.PLACES p ON p.PLACE_ID = CAST(pa.PLACE_ID AS VARCHAR)
)
SELECT
    USERNAME, CUSTOMER_ID,
    COUNT(DISTINCT PLACE_NAME)                          AS total_places,
    ARRAY_SLICE(ARRAY_UNIQUE_AGG(PLACE_NAME), 0, 50)    AS place_names
FROM pl
GROUP BY 1, 2;


-- ------------------------------------------------------------
-- MART_INSIGHT_DAILY_USER — grain user x jour, lignes "signal" uniquement (400 j)
-- Alimente le filtre de période du Classement d'adoption (agrégation côté dashboard).
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_DAILY_USER AS
SELECT USERNAME, CUSTOMER_ID, ACTIVITY_DATE,
    N_OVERVIEW, N_SYNTHESIS, N_THEMATIC, N_MONITORED_VIEWS
FROM REPORTING.ADOPTION.FCT_INSIGHT_USER_DAY
WHERE (N_OVERVIEW + N_SYNTHESIS + N_THEMATIC + N_MONITORED_VIEWS) > 0;

-- ------------------------------------------------------------
-- DIM_INSIGHT_USER — attributs + niveaux SAL des utilisateurs présents dans le fait quotidien
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_INSIGHT_USER AS
SELECT s.USERNAME, s.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY, s.N_ADMIN_PLACES,
    s.SAL_PLACE, s.SAL_ZONE, s.SAL_SECTOR, s.SAL_SUBTYPE, s.SAL_REGION,
    s.SAL_DEPARTMENT, s.SAL_COUNTRY, s.SAL_TYPE, s.SAL_BRAND
FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
WHERE EXISTS (
    SELECT 1 FROM REPORTING.ADOPTION.MART_INSIGHT_DAILY_USER d
    WHERE d.USERNAME = s.USERNAME AND d.CUSTOMER_ID = s.CUSTOMER_ID
);
