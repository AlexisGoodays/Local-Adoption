-- ============================================================
-- Couche REPORTING.ADOPTION — V1 Dashboard Adoption Utilisateurs Locaux
-- Aligné sur Notion "Définition des metrics" + PRD.
-- Décisions V1 : "créés" = comptes éligibles à date ; "actif Inbox" = consultation
-- (indicateur réponses/IA exposé séparément) ; fenêtre glissante 30 j.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS REPORTING.ADOPTION;

-- ------------------------------------------------------------
-- DIM_CUSTOMERS
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_CUSTOMERS AS
SELECT
    CUSTOMER_ID,
    CUSTOMER_NAME,
    CSM_OWNER,
    RENEWAL_STATUS,
    SEMANTIC_PROVIDER,
    SEMANTIC_CLASSIFICATION_PLAN,
    -- Éligible Insight = un semantic scheme est configuré et son nom ne commence pas par "-"
    -- (les "- ..." / "-- Retrocompat ..." sont des plans dépréciés).
    -- Exception validée par Alexis le 2026-09-17 : "- Buffalo Grill Restaurant" porte le
    -- préfixe des plans dépréciés mais le compte utilise réellement Insight (41 utilisateurs
    -- actifs sur 30 j, repérés pendant l'audit de cohérence car comptés au Portefeuille et
    -- absents de l'onglet). Ajouter ici tout autre plan à réintégrer au même titre.
    (SEMANTIC_CLASSIFICATION_PLAN IS NOT NULL
        AND (SEMANTIC_CLASSIFICATION_PLAN NOT LIKE '-%'
             OR SEMANTIC_CLASSIFICATION_PLAN IN ('- Buffalo Grill Restaurant'))) AS IS_INSIGHT_ELIGIBLE,
    -- E-réputation : accès au benchmark Google si une compétition est configurée au niveau customer
    (CUSTOMER_GOOGLE_BRAND_COMPETITION_CONFIGURATION = 'enabled'
        OR CUSTOMER_GOOGLE_PLACE_TYPE_COMPETITION_CONFIGURATION = 'enabled') AS EREP_BENCH_ENABLED
FROM MARTING_BUSINESS.ANALYTICS.CUSTOMERS;

-- ------------------------------------------------------------
-- DIM_PRO_USERS_SCOPED — périmètre commun, dédoublonné (username, customer)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED AS
WITH base AS (
    SELECT pu.*,
        ROW_NUMBER() OVER (
            PARTITION BY pu.USERNAME, pu.CUSTOMER_ID
            ORDER BY pu.JOINED_AT DESC NULLS LAST, pu.USER_ID DESC
        ) AS rn
    FROM MARTING_BUSINESS.ANALYTICS.PRO_USERS pu
    WHERE pu.ACCOUNT_STATUS = 'active'
      AND pu.HAS_VALID_BO_ACCOUNT = TRUE
      AND COALESCE(pu.USER_INSIGHT_REPORT_CONFIGURATION, '') <> 'specifically enabled'
),
pa AS (
    SELECT pa.USERNAME, pa.CUSTOMER_ID,
        COUNT(DISTINCT pa.PLACE_ID) AS n_admin_places,
        MAX(pa.PLACE_ID)            AS any_place_id,
        BOOLOR_AGG(p.GOOGLE_PLACE_ID IS NOT NULL) AS can_google_score  -- ≥1 place mappée fiche Google
    FROM MARTING_BUSINESS.ANALYTICS.PLACE_ADMINISTRATIONS pa
    LEFT JOIN MARTING_BUSINESS.ANALYTICS.PLACES p ON p.PLACE_ID = CAST(pa.PLACE_ID AS VARCHAR)
    GROUP BY 1, 2
)
SELECT
    b.USERNAME, b.CUSTOMER_ID, b.CUSTOMER_NAME, b.USER_ID,
    b.ROLE, b.JOB_CATEGORY, b.JOB_NAME, b.BO_MODE, b.TRAINING_STATUS,
    b.JOINED_AT, b.FIRST_SEEN_AT, b.USER_LANGUAGE,
    b.TOTAL_VALID_PLACES, b.IS_BRAND_LEVEL_ADMIN, b.HAS_SSO_ACCOUNT,
    COALESCE(pa.n_admin_places, 0) AS N_ADMIN_PLACES,
    COALESCE(pa.can_google_score, FALSE) AS CAN_GOOGLE_SCORE,
    CASE WHEN COALESCE(pa.n_admin_places, 0) = 1 THEN pa.any_place_id END AS SINGLE_PLACE_ID,
    (COALESCE(NULLIF(pa.n_admin_places, 0), b.TOTAL_VALID_PLACES, 1) <= 1
        AND COALESCE(b.IS_BRAND_LEVEL_ADMIN, FALSE) = FALSE) AS IS_LOCAL_SCOPE,
    -- Niveaux d'agrégation "single administrated" (option A). Une seule (souvent) est renseignée
    -- par user = l'unique unité qu'il administre à ce niveau. Tout null = accès multi-strates.
    b.SINGLE_ADMINISTRATED_PLACE_UNIT_NAME      AS SAL_PLACE,
    b.SINGLE_ADMINISTRATED_ZONE_UNIT_NAME       AS SAL_ZONE,
    b.SINGLE_ADMINISTRATED_SECTOR_UNIT_NAME     AS SAL_SECTOR,
    b.SINGLE_ADMINISTRATED_SUBTYPE_UNIT_NAME    AS SAL_SUBTYPE,
    b.SINGLE_ADMINISTRATED_REGION_UNIT_NAME     AS SAL_REGION,
    b.SINGLE_ADMINISTRATED_DEPARTMENT_UNIT_NAME AS SAL_DEPARTMENT,
    b.SINGLE_ADMINISTRATED_COUNTRY_UNIT_NAME    AS SAL_COUNTRY,
    b.SINGLE_ADMINISTRATED_TYPE_UNIT_NAME       AS SAL_TYPE,
    b.SINGLE_ADMINISTRATED_BRAND_UNIT_NAME      AS SAL_BRAND
FROM base b
LEFT JOIN pa ON pa.USERNAME = b.USERNAME AND pa.CUSTOMER_ID = b.CUSTOMER_ID
WHERE b.rn = 1;

-- ------------------------------------------------------------
-- FCT_LOCAL_ADOPTION_DAILY — grain user x customer x jour (400 j glissants)
-- Fenêtre portée de 180 à 400 j le 2026-09-17 : les dénominateurs "connectés"
-- sont désormais recalculables sur la période choisie (jusqu'à "année courante",
-- soit ~365 j), et l'on s'aligne sur la profondeur des faits des 3 modules.
-- Cette table ne porte PLUS de drapeau "actif <module>" : chaque module est seul
-- maître de sa définition d'actif (cf. MART_*_CUSTOMER_30D), et MART_PORTFOLIO_30D
-- les relit (sql/build_portfolio.sql). Auparavant les deux coexistaient et avaient
-- divergé : "Actifs Inbox" affichait 36 346 au Portefeuille (consultation) contre
-- 24 699 dans l'onglet (réponse), sur 126 comptes sur 139.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY AS
WITH scoped AS (
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED
),
act AS (
    SELECT ba.USERNAME, ba.CUSTOMER_ID, ba.OCCURRING_DATE AS d, ba.BO_ACTIVITY_NAME AS name
    FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES ba
    JOIN scoped s ON s.USERNAME = ba.USERNAME AND s.CUSTOMER_ID = ba.CUSTOMER_ID
    WHERE ba.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
),
agg AS (
    SELECT USERNAME, CUSTOMER_ID, d,
        COUNT(*) AS n_activities,
        COUNT_IF(name IN ('Inbox','Inbox list','Inbox show','Inbox search','Inbox action','Conversation','Metric · MESSAGES')) AS n_inbox,
        COUNT_IF(name IN ('Metric · GOOGLE_SCORE','Metric · GOOGLE_BENCHMARK')) AS n_ereput,
        COUNT_IF(name IN ('Topic drill-down · overview','Metric · SENTIMENT','Metric · SENTIMENT_OVERVIEW')) AS n_insight_act,
        COUNT_IF(name = 'Insight Report Center') AS n_insight_summary,
        COUNT_IF(name = 'Topic drill-down · thematic') AS n_insight_thematic
    FROM act GROUP BY 1, 2, 3
),
mon_agg AS (
    SELECT bpv.USERNAME, bpv.CUSTOMER_ID, bpv.OCCURRING_DATE AS d, COUNT(*) AS n_monitored_views
    FROM MARTING_BUSINESS.ANALYTICS.BO_WEB_PAGE_VIEWS bpv
    JOIN scoped s ON s.USERNAME = bpv.USERNAME AND s.CUSTOMER_ID = bpv.CUSTOMER_ID
    WHERE bpv.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
      AND bpv.INSIGHT_MONITORING_STATUS = 'monitored'
    GROUP BY 1, 2, 3
),
-- réponses Inbox (CONNECT_ITEMS) : signal de connexion à part entière (2026-09-17).
-- Certaines réponses (notamment IA-assistées) n'émettent aucun événement BO_ACTIVITIES
-- (cf. constat sur Chaussea/Feu Vert) -> sans ce signal, IS_CONNECTED sous-comptait
-- des utilisateurs pourtant actifs (ils apparaissaient "actifs Inbox" sans être "connectés").
rep_agg AS (
    SELECT ci.USERNAME, ci.CUSTOMER_ID, ci.CREATED_DATE AS d, COUNT_IF(ci.IS_REPLY) AS n_replies
    FROM MARTING_BUSINESS.ANALYTICS.CONNECT_ITEMS ci
    JOIN scoped s ON s.USERNAME = ci.USERNAME AND s.CUSTOMER_ID = ci.CUSTOMER_ID
    WHERE ci.CREATED_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
)
SELECT
    COALESCE(a.USERNAME, m.USERNAME, r.USERNAME)     AS USERNAME,
    COALESCE(a.CUSTOMER_ID, m.CUSTOMER_ID, r.CUSTOMER_ID) AS CUSTOMER_ID,
    COALESCE(a.d, m.d, r.d)              AS ACTIVITY_DATE,
    COALESCE(a.n_activities, 0)          AS N_ACTIVITIES,
    COALESCE(a.n_inbox, 0)              AS N_INBOX,
    COALESCE(a.n_ereput, 0)             AS N_EREPUT,
    COALESCE(a.n_insight_act, 0)        AS N_INSIGHT_ACT,
    COALESCE(a.n_insight_summary, 0)    AS N_INSIGHT_SUMMARY,
    COALESCE(a.n_insight_thematic, 0)   AS N_INSIGHT_THEMATIC,
    COALESCE(m.n_monitored_views, 0)    AS N_MONITORED_VIEWS,
    COALESCE(r.n_replies, 0)            AS N_REPLIES,
    (COALESCE(a.n_activities, 0) > 0 OR COALESCE(r.n_replies, 0) > 0) AS IS_CONNECTED
FROM agg a
FULL OUTER JOIN mon_agg m
    ON a.USERNAME = m.USERNAME AND a.CUSTOMER_ID = m.CUSTOMER_ID AND a.d = m.d
FULL OUTER JOIN rep_agg r
    ON r.USERNAME = COALESCE(a.USERNAME, m.USERNAME) AND r.CUSTOMER_ID = COALESCE(a.CUSTOMER_ID, m.CUSTOMER_ID) AND r.d = COALESCE(a.d, m.d);

-- ------------------------------------------------------------
-- FCT_INBOX_REPLIES_DAILY — indicateur d'usage Inbox (réponses envoyées, part IA)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.FCT_INBOX_REPLIES_DAILY AS
SELECT
    ci.USERNAME, ci.CUSTOMER_ID, ci.CREATED_DATE AS ACTIVITY_DATE,
    COUNT_IF(ci.IS_REPLY) AS N_REPLIES,
    COUNT_IF(ci.IS_REPLY AND ci.IS_ASSISTED_REPLY) AS N_REPLIES_AI
FROM MARTING_BUSINESS.ANALYTICS.CONNECT_ITEMS ci
JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    ON s.USERNAME = ci.USERNAME AND s.CUSTOMER_ID = ci.CUSTOMER_ID
WHERE ci.CREATED_DATE >= DATEADD('day', -400, CURRENT_DATE)
GROUP BY 1, 2, 3;

-- ------------------------------------------------------------
-- MART_PORTFOLIO_30D a été déplacée dans sql/build_portfolio.sql (2026-09-17),
-- qui s'exécute EN DERNIER : l'écran Portefeuille relit désormais les marts des
-- 3 modules au lieu de recalculer sa propre notion d'"actif". C'est ce qui
-- garantit qu'un même libellé affiche le même chiffre sur tous les écrans.
-- ------------------------------------------------------------


-- ------------------------------------------------------------
-- MART_CONNECTED_PERIOD_CUSTOMER — "connectés" recalculés sur chacune des
-- périodes proposées par le dashboard (2026-09-17).
--
-- Pourquoi : jusqu'ici le dénominateur "connectés" était FIGÉ à 30 j alors que
-- le numérateur "actifs" suivait la période choisie. En "Année courante" on
-- comparait donc ~260 j d'actifs à 30 j de connectés : Insight passait de 5,8 %
-- à 23,5 % sans qu'aucun usage n'ait changé, et 2 comptes dépassaient 100 %
-- (ORPEA 102,3 %). Les fenêtres ci-dessous reproduisent exactement celles du
-- client (cf. periodRange() dans tools/build_dashboard.py).
-- Les périodes "custom" ne sont pas précalculables : le dashboard masque alors
-- le ratio au lieu d'en afficher un faux.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_CONNECTED_PERIOD_CUSTOMER AS
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
SELECT CUSTOMER_ID,
    COUNT_IF(c30) AS CONNECTED_30D,
    COUNT_IF(cpm) AS CONNECTED_PREVMONTH,
    COUNT_IF(cq)  AS CONNECTED_QUARTER,
    COUNT_IF(cy)  AS CONNECTED_YEAR
FROM u GROUP BY 1;
