-- ============================================================
-- Value driver E-réputation « Acquisition » — Note Google, volume d'avis,
-- taux/temps de réponse. Périmètre = PLACES (pas d'utilisateurs) : chaque
-- place porte déjà sa propre unité à chaque niveau (*_DIVISION_NAME), pas
-- besoin du rollup hiérarchique de build_hierarchy.sql (qui concerne les users).
--
-- Sources :
--   - MONTHLY_PLACE_CHECKUPS (MARTING_BUSINESS.ANALYTICS) : snapshot mensuel
--     GOOGLE_SCORE / GOOGLE_REVIEW_COUNT par place (cumulés, pas un delta).
--   - PARTICIPATIONS filtrée PARTICIPATION_CHANNEL='Google' AND
--     PARTICIPATION_MEDIUM='GoogleMyBusiness' = avis Google individuels,
--     avec COLLECTED_DATE (date de l'avis) et REPLIED_DATE (date de réponse,
--     NULL si pas répondu). Vérifié : taux de réponse ≈58%, délai moyen ≈2j.
-- ============================================================

-- ------------------------------------------------------------
-- 1) Snapshot par place : score courant, N-1 an, volume cumulé + tokens de
--    périmètre (position = SAL_IDX du dashboard : place,zone,sector,subtype,
--    region,department,country,type,brand). Un score Google déjà agrégé par
--    Google -> pas d'agrégation "avis" possible ici, seulement pondération.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_GOOGLE_PLACE_SNAPSHOT AS
WITH last_month AS (
    SELECT MAX(MONTH_ID) AS m FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS WHERE IS_FINISHED
),
cur AS (
    SELECT c.PLACE_ID, c.CUSTOMER_ID, c.GOOGLE_SCORE, c.GOOGLE_REVIEW_COUNT
    FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS c, last_month lm
    WHERE c.MONTH_ID = lm.m
),
ly AS (
    SELECT c.PLACE_ID, c.GOOGLE_SCORE AS GOOGLE_SCORE_LY
    FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS c, last_month lm
    WHERE c.MONTH_ID = TO_CHAR(ADD_MONTHS(TO_DATE(lm.m || '-01'), -12), 'YYYY-MM')
)
SELECT
    p.PLACE_ID, p.CUSTOMER_ID, p.PLACE_NAME,
    cur.GOOGLE_SCORE            AS score,
    cur.GOOGLE_REVIEW_COUNT     AS reviews,
    ly.GOOGLE_SCORE_LY          AS score_ly,
    p.PLACE_NAME                AS u_place,
    p.ZONE_DIVISION_NAME        AS u_zone,
    p.SECTOR_DIVISION_NAME      AS u_sector,
    p.SUBTYPE_DIVISION_NAME     AS u_subtype,
    p.REGION_DIVISION_NAME      AS u_region,
    p.DEPARTMENT_DIVISION_NAME  AS u_department,
    p.COUNTRY_DIVISION_NAME     AS u_country,
    p.TYPE_DIVISION_NAME        AS u_type,
    p.BRAND_DIVISION_NAME       AS u_brand
FROM MARTING_BUSINESS.ANALYTICS.PLACES p
JOIN cur ON cur.PLACE_ID = p.PLACE_ID
LEFT JOIN ly ON ly.PLACE_ID = p.PLACE_ID
JOIN REPORTING.ADOPTION.DIM_CUSTOMERS dc ON dc.CUSTOMER_ID = p.CUSTOMER_ID
WHERE cur.GOOGLE_SCORE IS NOT NULL;

-- ------------------------------------------------------------
-- 2) Fait quotidien customer×jour (400 j, sans périmètre) — volume/taux/temps
--    période-flexible côté client, même logique que FCT_INSIGHT_USER_DAY.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.FCT_EREP_GOOGLE_REVIEW_CUSTOMER_DAY AS
SELECT
    pt.CUSTOMER_ID,
    pt.COLLECTED_DATE AS ACTIVITY_DATE,
    COUNT(*)                    AS n_reviews,
    COUNT(pt.REPLIED_DATE)      AS n_replied,
    SUM(IFF(pt.REPLIED_DATE IS NOT NULL,
            DATEDIFF('day', pt.COLLECTED_DATE, pt.REPLIED_DATE), 0)) AS sum_reply_days
FROM MARTING_BUSINESS.ANALYTICS.PARTICIPATIONS pt
JOIN REPORTING.ADOPTION.DIM_CUSTOMERS dc ON dc.CUSTOMER_ID = pt.CUSTOMER_ID
WHERE pt.PARTICIPATION_CHANNEL = 'Google' AND pt.PARTICIPATION_MEDIUM = 'GoogleMyBusiness'
  AND pt.COLLECTED_DATE >= DATEADD('day', -400, CURRENT_DATE)
GROUP BY 1, 2;

-- ------------------------------------------------------------
-- 3) Périmètre (customer×level×unit) fixé 30j courant + 30j précédents —
--    même logique que les dénominateurs "connectés (30j)" déjà en place :
--    quand un périmètre est actif, volume/taux/temps s'affichent en 30j fixe.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_EREP_GOOGLE_PERIMETER_30D AS
WITH rev AS (
    SELECT pt.CUSTOMER_ID, pt.PLACE_ID, pt.COLLECTED_DATE, pt.REPLIED_DATE,
        IFF(pt.COLLECTED_DATE >= DATEADD('day', -29, CURRENT_DATE), 'cur', 'prev') AS bucket
    FROM MARTING_BUSINESS.ANALYTICS.PARTICIPATIONS pt
    WHERE pt.PARTICIPATION_CHANNEL = 'Google' AND pt.PARTICIPATION_MEDIUM = 'GoogleMyBusiness'
      AND pt.COLLECTED_DATE >= DATEADD('day', -59, CURRENT_DATE)
),
places_long AS (
    SELECT CUSTOMER_ID, PLACE_ID, 'place' AS level, PLACE_NAME AS unit_name FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE PLACE_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'zone',       ZONE_DIVISION_NAME       FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE ZONE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'sector',     SECTOR_DIVISION_NAME     FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SECTOR_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'subtype',    SUBTYPE_DIVISION_NAME    FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE SUBTYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'region',     REGION_DIVISION_NAME     FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE REGION_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'department', DEPARTMENT_DIVISION_NAME FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE DEPARTMENT_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'country',    COUNTRY_DIVISION_NAME    FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE COUNTRY_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'type',       TYPE_DIVISION_NAME       FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE TYPE_DIVISION_NAME IS NOT NULL
    UNION ALL SELECT CUSTOMER_ID, PLACE_ID, 'brand',      BRAND_DIVISION_NAME      FROM MARTING_BUSINESS.ANALYTICS.PLACES WHERE BRAND_DIVISION_NAME IS NOT NULL
),
joined AS (
    SELECT pl.CUSTOMER_ID, pl.level, pl.unit_name, r.bucket, r.COLLECTED_DATE, r.REPLIED_DATE
    FROM places_long pl
    JOIN rev r ON r.PLACE_ID = pl.PLACE_ID AND r.CUSTOMER_ID = pl.CUSTOMER_ID
)
SELECT CUSTOMER_ID, level, unit_name,
    COUNT_IF(bucket='cur')                                              AS reviews_30d,
    COUNT_IF(bucket='cur'  AND REPLIED_DATE IS NOT NULL)                AS replied_30d,
    SUM(IFF(bucket='cur'  AND REPLIED_DATE IS NOT NULL, DATEDIFF('day', COLLECTED_DATE, REPLIED_DATE), 0)) AS reply_days_30d,
    COUNT_IF(bucket='prev')                                             AS reviews_prev30d,
    COUNT_IF(bucket='prev' AND REPLIED_DATE IS NOT NULL)                AS replied_prev30d,
    SUM(IFF(bucket='prev' AND REPLIED_DATE IS NOT NULL, DATEDIFF('day', COLLECTED_DATE, REPLIED_DATE), 0)) AS reply_days_prev30d
FROM joined
GROUP BY 1, 2, 3;
