-- ============================================================
-- Rattachement hiérarchique des utilisateurs (option B) — pour le filtre "Périmètre"
-- À exécuter APRÈS build_adoption + build_insight + build_erep.
--
-- DIM_USER_UNIT : 1 ligne par (user, niveau, unité) à laquelle l'utilisateur appartient :
--   - sa valeur single_administrated à ce niveau (tout nb de places), niveau 'place' inclus ;
--   - + toutes les unités zone/secteur/sous-type/région/département/pays/type/brand de SES magasins
--     administrés, UNIQUEMENT si l'utilisateur administre entre 1 et 60 places (exclut siège/national).
-- Restreint aux utilisateurs présents dans l'un des faits quotidiens (Insight ou E-rép).
-- ============================================================

CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_USER_UNIT AS
WITH du_users AS (
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.MART_INSIGHT_DAILY_USER
    UNION
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.MART_EREP_DAILY_USER
    UNION
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.MART_INBOX_DAILY_USER
),
u AS (
    SELECT s.USERNAME, s.CUSTOMER_ID, s.N_ADMIN_PLACES,
        s.SAL_PLACE, s.SAL_ZONE, s.SAL_SECTOR, s.SAL_SUBTYPE, s.SAL_REGION,
        s.SAL_DEPARTMENT, s.SAL_COUNTRY, s.SAL_TYPE, s.SAL_BRAND
    FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    JOIN du_users d ON d.USERNAME = s.USERNAME AND d.CUSTOMER_ID = s.CUSTOMER_ID
),
-- (a) rattachement "single administrated" propre à l'utilisateur
sal AS (
    SELECT USERNAME, CUSTOMER_ID, 'place'      AS level, SAL_PLACE      AS unit_name FROM u WHERE SAL_PLACE      IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'zone',       SAL_ZONE       FROM u WHERE SAL_ZONE       IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'sector',     SAL_SECTOR     FROM u WHERE SAL_SECTOR     IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'subtype',    SAL_SUBTYPE    FROM u WHERE SAL_SUBTYPE    IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'region',     SAL_REGION     FROM u WHERE SAL_REGION     IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'department', SAL_DEPARTMENT FROM u WHERE SAL_DEPARTMENT IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'country',    SAL_COUNTRY    FROM u WHERE SAL_COUNTRY    IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'type',       SAL_TYPE       FROM u WHERE SAL_TYPE       IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'brand',      SAL_BRAND      FROM u WHERE SAL_BRAND      IS NOT NULL
),
-- (b) héritage via les magasins administrés (users locaux/régionaux : 1..60 places)
adm AS (
    SELECT u.USERNAME, u.CUSTOMER_ID,
        p.ZONE_DIVISION_NAME, p.SECTOR_DIVISION_NAME, p.SUBTYPE_DIVISION_NAME, p.REGION_DIVISION_NAME,
        p.DEPARTMENT_DIVISION_NAME, p.COUNTRY_DIVISION_NAME, p.TYPE_DIVISION_NAME, p.BRAND_DIVISION_NAME
    FROM u
    JOIN MARTING_BUSINESS.ANALYTICS.PLACE_ADMINISTRATIONS pa
        ON pa.USERNAME = u.USERNAME AND pa.CUSTOMER_ID = u.CUSTOMER_ID
    JOIN MARTING_BUSINESS.ANALYTICS.PLACES p
        ON p.PLACE_ID = CAST(pa.PLACE_ID AS VARCHAR)
    WHERE COALESCE(u.N_ADMIN_PLACES, 0) BETWEEN 1 AND 60
),
hier AS (
    SELECT USERNAME, CUSTOMER_ID, 'zone'       AS level, ZONE_DIVISION_NAME       AS unit_name FROM adm WHERE ZONE_DIVISION_NAME       IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'sector',     SECTOR_DIVISION_NAME     FROM adm WHERE SECTOR_DIVISION_NAME     IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'subtype',    SUBTYPE_DIVISION_NAME    FROM adm WHERE SUBTYPE_DIVISION_NAME    IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'region',     REGION_DIVISION_NAME     FROM adm WHERE REGION_DIVISION_NAME     IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'department', DEPARTMENT_DIVISION_NAME FROM adm WHERE DEPARTMENT_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'country',    COUNTRY_DIVISION_NAME    FROM adm WHERE COUNTRY_DIVISION_NAME    IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'type',       TYPE_DIVISION_NAME       FROM adm WHERE TYPE_DIVISION_NAME       IS NOT NULL
    UNION ALL SELECT USERNAME, CUSTOMER_ID, 'brand',      BRAND_DIVISION_NAME      FROM adm WHERE BRAND_DIVISION_NAME      IS NOT NULL
)
SELECT DISTINCT USERNAME, CUSTOMER_ID, level, unit_name
FROM (SELECT * FROM sal UNION ALL SELECT * FROM hier);

-- ------------------------------------------------------------
-- MART_INSIGHT_PERIMETER_30D — pour chaque (customer, niveau, unité) : connectés 30 j (option B)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_PERIMETER_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = f.CUSTOMER_ID AND c.IS_INSIGHT_ELIGIBLE
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
)
SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
    COUNT(DISTINCT uu.USERNAME) AS connected_users
FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
JOIN conn c ON c.USERNAME = uu.USERNAME AND c.CUSTOMER_ID = uu.CUSTOMER_ID
GROUP BY 1, 2, 3;

-- ------------------------------------------------------------
-- MART_EREP_PERIMETER_30D — idem + accès Note Google / Benchmark
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_PERIMETER_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID, s.CAN_GOOGLE_SCORE, c.EREP_BENCH_ENABLED
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s ON s.USERNAME = f.USERNAME AND s.CUSTOMER_ID = f.CUSTOMER_ID
    JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = f.CUSTOMER_ID
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
)
SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
    COUNT(DISTINCT uu.USERNAME) AS connected_users,
    COUNT(DISTINCT IFF(c.CAN_GOOGLE_SCORE, uu.USERNAME, NULL)) AS connected_score_access,
    COUNT(DISTINCT IFF(c.EREP_BENCH_ENABLED, uu.USERNAME, NULL)) AS connected_bench_access
FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
JOIN conn c ON c.USERNAME = uu.USERNAME AND c.CUSTOMER_ID = uu.CUSTOMER_ID
GROUP BY 1, 2, 3;

-- ------------------------------------------------------------
-- MART_INBOX_PERIMETER_30D — connectés 30 j (option B), tous comptes (pas d'éligibilité)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_PERIMETER_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
)
SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
    COUNT(DISTINCT uu.USERNAME) AS connected_users
FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
JOIN conn c ON c.USERNAME = uu.USERNAME AND c.CUSTOMER_ID = uu.CUSTOMER_ID
GROUP BY 1, 2, 3;

-- ------------------------------------------------------------
-- MART_INSIGHT_UNIT_30D / MART_EREP_UNIT_30D / MART_INBOX_UNIT_30D — option B
-- (2026-09-16, remplace l'option A "single administrated" : celle-ci ne
-- remontait que l'administrateur direct d'un niveau, pas les utilisateurs
-- qui en dépendent hiérarchiquement — cf. constat Alexis sur le classement
-- "Région" n'affichant qu'1 connecté). Grain : customer x niveau x unité,
-- via l'appartenance DIM_USER_UNIT (même logique que le filtre Périmètre :
-- exclut donc aussi les utilisateurs siège/national, cf. build_hierarchy
-- ci-dessus). Plus de bucket "(accès multi-strates)" : un utilisateur sans
-- rattachement (0 place administrée, ou >60) n'apparaît simplement dans
-- aucune unité, comme pour le Périmètre.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INSIGHT_UNIT_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    JOIN REPORTING.ADOPTION.DIM_CUSTOMERS c ON c.CUSTOMER_ID = f.CUSTOMER_ID AND c.IS_INSIGHT_ELIGIBLE
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
),
base AS (
    SELECT cu.USERNAME, cu.CUSTOMER_ID,
        COALESCE(iu.insight_actions, 0) AS insight_actions,
        COALESCE(iu.overview, 0)  AS overview,
        COALESCE(iu.synthesis, 0) AS synthesis,
        COALESCE(iu.thematic, 0)  AS thematic,
        IFF(iu.is_active, 1, 0)   AS is_active_insight
    FROM conn cu
    LEFT JOIN REPORTING.ADOPTION.MART_INSIGHT_USER_30D iu
        ON iu.USERNAME = cu.USERNAME AND iu.CUSTOMER_ID = cu.CUSTOMER_ID
),
unpiv AS (
    SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
        b.insight_actions, b.overview, b.synthesis, b.thematic, b.is_active_insight
    FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
    JOIN base b ON b.USERNAME = uu.USERNAME AND b.CUSTOMER_ID = uu.CUSTOMER_ID
),
places_long AS (
    SELECT CUSTOMER_ID, 'place' AS level, PLACE_NAME AS unit_name, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE PLACE_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'zone',       ZONE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE ZONE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'sector',     SECTOR_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SECTOR_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'subtype',    SUBTYPE_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SUBTYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'region',     REGION_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE REGION_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'department', DEPARTMENT_DIVISION_NAME, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE DEPARTMENT_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'country',    COUNTRY_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE COUNTRY_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'type',       TYPE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE TYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'brand',      BRAND_DIVISION_NAME,      PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE BRAND_DIVISION_NAME IS NOT NULL
),
unit_places AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(DISTINCT PLACE_ID) AS place_count,
        ARRAY_SLICE(ARRAY_UNIQUE_AGG(PLACE_NAME), 0, 50) AS place_names
    FROM places_long GROUP BY 1, 2, 3
),
agg AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(*)               AS connected_users,
        SUM(is_active_insight) AS active_insight_users,
        SUM(insight_actions)   AS insight_actions,
        SUM(overview)          AS overview_actions,
        SUM(synthesis)         AS synthesis_actions,
        SUM(thematic)          AS thematic_actions
    FROM unpiv GROUP BY 1, 2, 3
)
SELECT a.CUSTOMER_ID, a.level, a.unit_name,
    a.connected_users, a.active_insight_users, a.insight_actions,
    a.overview_actions, a.synthesis_actions, a.thematic_actions,
    up.place_count, up.place_names
FROM agg a
LEFT JOIN unit_places up
    ON up.CUSTOMER_ID = a.CUSTOMER_ID AND up.level = a.level AND up.unit_name = a.unit_name;

-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_UNIT_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
),
base AS (
    SELECT cu.USERNAME, cu.CUSTOMER_ID,
        COALESCE(eu.erep_actions, 0) AS erep_actions,
        COALESCE(eu.score, 0)     AS score,
        COALESCE(eu.benchmark, 0) AS benchmark,
        IFF(eu.is_active, 1, 0)   AS is_active_erep
    FROM conn cu
    LEFT JOIN REPORTING.ADOPTION.MART_EREP_USER_30D eu
        ON eu.USERNAME = cu.USERNAME AND eu.CUSTOMER_ID = cu.CUSTOMER_ID
),
unpiv AS (
    SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
        b.erep_actions, b.score, b.benchmark, b.is_active_erep
    FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
    JOIN base b ON b.USERNAME = uu.USERNAME AND b.CUSTOMER_ID = uu.CUSTOMER_ID
),
places_long AS (
    SELECT CUSTOMER_ID, 'place' AS level, PLACE_NAME AS unit_name, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE PLACE_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'zone',       ZONE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE ZONE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'sector',     SECTOR_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SECTOR_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'subtype',    SUBTYPE_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SUBTYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'region',     REGION_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE REGION_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'department', DEPARTMENT_DIVISION_NAME, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE DEPARTMENT_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'country',    COUNTRY_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE COUNTRY_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'type',       TYPE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE TYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'brand',      BRAND_DIVISION_NAME,      PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE BRAND_DIVISION_NAME IS NOT NULL
),
unit_places AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(DISTINCT PLACE_ID) AS place_count,
        ARRAY_SLICE(ARRAY_UNIQUE_AGG(PLACE_NAME), 0, 50) AS place_names
    FROM places_long GROUP BY 1, 2, 3
),
agg AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(*)               AS connected_users,
        SUM(is_active_erep)    AS active_erep_users,
        SUM(erep_actions)      AS erep_actions,
        SUM(score)             AS score_actions,
        SUM(benchmark)         AS bench_actions
    FROM unpiv GROUP BY 1, 2, 3
)
SELECT a.CUSTOMER_ID, a.level, a.unit_name,
    a.connected_users, a.active_erep_users, a.erep_actions, a.score_actions, a.bench_actions,
    up.place_count, up.place_names
FROM agg a
LEFT JOIN unit_places up
    ON up.CUSTOMER_ID = a.CUSTOMER_ID AND up.level = a.level AND up.unit_name = a.unit_name;

-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_UNIT_30D AS
WITH conn AS (
    SELECT DISTINCT f.USERNAME, f.CUSTOMER_ID
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY f
    WHERE f.ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND f.IS_CONNECTED
),
base AS (
    SELECT cu.USERNAME, cu.CUSTOMER_ID,
        COALESCE(iu.n_inbox, 0)   AS inbox_actions,
        COALESCE(iu.n_replies, 0) AS replies,
        IFF(iu.is_connected_inbox, 1, 0) AS is_connected_inbox,
        IFF(iu.is_active_inbox, 1, 0)    AS is_active_inbox
    FROM conn cu
    LEFT JOIN REPORTING.ADOPTION.MART_INBOX_USER_30D iu
        ON iu.USERNAME = cu.USERNAME AND iu.CUSTOMER_ID = cu.CUSTOMER_ID
),
unpiv AS (
    SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
        b.inbox_actions, b.replies, b.is_connected_inbox, b.is_active_inbox
    FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
    JOIN base b ON b.USERNAME = uu.USERNAME AND b.CUSTOMER_ID = uu.CUSTOMER_ID
),
places_long AS (
    SELECT CUSTOMER_ID, 'place' AS level, PLACE_NAME AS unit_name, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE PLACE_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'zone',       ZONE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE ZONE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'sector',     SECTOR_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SECTOR_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'subtype',    SUBTYPE_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SUBTYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'region',     REGION_DIVISION_NAME,     PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE REGION_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'department', DEPARTMENT_DIVISION_NAME, PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE DEPARTMENT_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'country',    COUNTRY_DIVISION_NAME,    PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE COUNTRY_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'type',       TYPE_DIVISION_NAME,       PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE TYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, 'brand',      BRAND_DIVISION_NAME,      PLACE_ID, PLACE_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE BRAND_DIVISION_NAME IS NOT NULL
),
unit_places AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(DISTINCT PLACE_ID) AS place_count,
        ARRAY_SLICE(ARRAY_UNIQUE_AGG(PLACE_NAME), 0, 50) AS place_names
    FROM places_long GROUP BY 1, 2, 3
),
agg AS (
    SELECT CUSTOMER_ID, level, unit_name,
        COUNT(*)                  AS connected_users,
        SUM(is_connected_inbox)   AS connected_inbox_users,
        SUM(is_active_inbox)      AS active_inbox_users,
        SUM(inbox_actions)        AS inbox_actions,
        SUM(replies)              AS replies
    FROM unpiv GROUP BY 1, 2, 3
)
SELECT a.CUSTOMER_ID, a.level, a.unit_name,
    a.connected_users, a.connected_inbox_users, a.active_inbox_users, a.inbox_actions, a.replies,
    up.place_count, up.place_names
FROM agg a
LEFT JOIN unit_places up
    ON up.CUSTOMER_ID = a.CUSTOMER_ID AND up.level = a.level AND up.unit_name = a.unit_name;

-- ------------------------------------------------------------
-- MART_CONNECTED_PERIOD_UNIT — pendant de MART_CONNECTED_PERIOD_CUSTOMER à la
-- maille unité (2026-09-17). Sert de dénominateur "connectés" quand une période
-- autre que 30 j est sélectionnée, que ce soit via le filtre Périmètre ou dans
-- la colonne "Connectés" du classement par niveau.
-- Table autonome (et non colonnes ajoutées aux 6 marts PERIMETER/UNIT existants)
-- pour garder ces marts inchangés : le client fait la jointure sur (level, unit).
-- Rattachement = DIM_USER_UNIT, donc exactement la même règle option B que le
-- filtre Périmètre (un utilisateur peut appartenir à plusieurs unités d'un
-- même niveau : la somme des unités peut dépasser le total du compte).
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_CONNECTED_PERIOD_UNIT AS
WITH u AS (
    SELECT USERNAME, CUSTOMER_ID,
        BOOLOR_AGG(ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE)) AS c30,
        BOOLOR_AGG(ACTIVITY_DATE >= DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE))
               AND ACTIVITY_DATE <  DATE_TRUNC('month', CURRENT_DATE))  AS cpm,
        BOOLOR_AGG(ACTIVITY_DATE >= DATE_TRUNC('quarter', CURRENT_DATE)) AS cq,
        BOOLOR_AGG(ACTIVITY_DATE >= DATE_TRUNC('year', CURRENT_DATE))    AS cy
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY
    WHERE IS_CONNECTED
      AND ACTIVITY_DATE >= LEAST(DATEADD('day', -30, CURRENT_DATE),
                                 DATE_TRUNC('month', DATEADD('month', -1, CURRENT_DATE)),
                                 DATE_TRUNC('year', CURRENT_DATE))
    GROUP BY 1, 2
)
SELECT uu.CUSTOMER_ID, uu.level, uu.unit_name,
    COUNT(DISTINCT IFF(u.c30, uu.USERNAME, NULL)) AS CONNECTED_30D,
    COUNT(DISTINCT IFF(u.cpm, uu.USERNAME, NULL)) AS CONNECTED_PREVMONTH,
    COUNT(DISTINCT IFF(u.cq,  uu.USERNAME, NULL)) AS CONNECTED_QUARTER,
    COUNT(DISTINCT IFF(u.cy,  uu.USERNAME, NULL)) AS CONNECTED_YEAR
FROM REPORTING.ADOPTION.DIM_USER_UNIT uu
JOIN u ON u.USERNAME = uu.USERNAME AND u.CUSTOMER_ID = uu.CUSTOMER_ID
GROUP BY 1, 2, 3;
