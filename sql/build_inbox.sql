-- ============================================================
-- Module Inbox — détail. Méthodo miroir d'Insight/E-réputation.
-- Tous les comptes sont éligibles (pas de filtre customer, comme E-rép).
--
-- Funnel : "Actif Inbox" = a consulté l'inbox (définition V1 conservée telle
-- quelle — Alexis : l'inbox est souvent la page d'accueil, la simple
-- consultation est déjà un signal d'engagement). "Répondants" (a envoyé
-- ≥1 réponse) devient une métrique complémentaire du Value Driver Culture
-- Client, PAS un remplacement du funnel Adoption.
--
-- Value Driver "Culture Client" (6bis) : 8 KPI retenus sur 11 proposés —
-- % traité <72h et activation des notifications écartés pour le moment
-- (cf. Notion 6bis Inbox).
-- ============================================================

-- ------------------------------------------------------------
-- MART_INBOX_DAILY_USER — fait quotidien 400 j (filtre de période, période-flexible)
--   n_inbox   = actions de consultation (BO_ACTIVITIES, def. "actif" existante)
--   n_mobile  = sous-ensemble de n_inbox fait depuis l'app mobile (BO_PLATFORM)
--   n_replies / n_replies_ai / n_replies_templated = usage des réponses
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_DAILY_USER AS
WITH scoped AS (
    SELECT USERNAME, CUSTOMER_ID FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED
),
act AS (
    SELECT ba.USERNAME, ba.CUSTOMER_ID, ba.OCCURRING_DATE AS d,
        COUNT(*) AS n_inbox,
        COUNT_IF(ba.BO_PLATFORM = 'bo mobile') AS n_mobile
    FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES ba
    JOIN scoped s ON s.USERNAME = ba.USERNAME AND s.CUSTOMER_ID = ba.CUSTOMER_ID
    WHERE ba.OCCURRING_DATE >= DATEADD('day', -400, CURRENT_DATE)
      AND ba.BO_ACTIVITY_NAME IN ('Inbox','Inbox list','Inbox show','Inbox search','Inbox action','Conversation','Metric · MESSAGES')
    GROUP BY 1, 2, 3
),
rep AS (
    SELECT ci.USERNAME, ci.CUSTOMER_ID, ci.CREATED_DATE AS d,
        COUNT_IF(ci.IS_REPLY) AS n_replies,
        COUNT_IF(ci.IS_REPLY AND ci.IS_ASSISTED_REPLY) AS n_replies_ai
    FROM MARTING_BUSINESS.ANALYTICS.CONNECT_ITEMS ci
    JOIN scoped s ON s.USERNAME = ci.USERNAME AND s.CUSTOMER_ID = ci.CUSTOMER_ID
    WHERE ci.CREATED_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
),
tmpl AS (
    SELECT p.REPLIER_USERNAME AS USERNAME, p.CUSTOMER_ID, p.REPLIED_DATE AS d,
        COUNT_IF(p.IS_REPLY_TEMPLATED) AS n_replies_templated
    FROM MARTING_BUSINESS.ANALYTICS.PARTICIPATIONS p
    JOIN scoped s ON s.USERNAME = p.REPLIER_USERNAME AND s.CUSTOMER_ID = p.CUSTOMER_ID
    WHERE p.REPLIED_DATE >= DATEADD('day', -400, CURRENT_DATE)
    GROUP BY 1, 2, 3
),
keys AS (
    SELECT USERNAME, CUSTOMER_ID, d FROM act
    UNION SELECT USERNAME, CUSTOMER_ID, d FROM rep
    UNION SELECT USERNAME, CUSTOMER_ID, d FROM tmpl
)
SELECT k.USERNAME, k.CUSTOMER_ID, k.d AS ACTIVITY_DATE,
    COALESCE(a.n_inbox, 0)   AS N_INBOX,
    COALESCE(a.n_mobile, 0)  AS N_MOBILE,
    COALESCE(r.n_replies, 0) AS N_REPLIES,
    COALESCE(r.n_replies_ai, 0) AS N_REPLIES_AI,
    COALESCE(t.n_replies_templated, 0) AS N_REPLIES_TEMPLATED
FROM keys k
LEFT JOIN act  a ON a.USERNAME = k.USERNAME AND a.CUSTOMER_ID = k.CUSTOMER_ID AND a.d = k.d
LEFT JOIN rep  r ON r.USERNAME = k.USERNAME AND r.CUSTOMER_ID = k.CUSTOMER_ID AND r.d = k.d
LEFT JOIN tmpl t ON t.USERNAME = k.USERNAME AND t.CUSTOMER_ID = k.CUSTOMER_ID AND t.d = k.d;

-- ------------------------------------------------------------
-- MART_INBOX_CUSTOMER_DAY — agrégat customer×jour (400 j), pour la courbe
-- d'évolution période-flexible. ATTENTION : MART_INBOX_DAILY_USER (grain user)
-- fait 4,1M lignes (l'inbox est une page consultée en continu, contrairement
-- à Insight/E-rép) -> beaucoup trop volumineux à embarquer tel quel côté
-- dashboard. On agrège donc ici côté SQL ; le détail par utilisateur
-- (classement, top adopters, KPIs usage réponse) reste sur les marts *_30D
-- (fenêtre fixe 30 j, comme le reste du dashboard pour les dénominateurs
-- "connectés"). Seule la courbe (et le KPI Actifs Inbox associé) profite du
-- sélecteur de période complet.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_CUSTOMER_DAY AS
SELECT CUSTOMER_ID, ACTIVITY_DATE,
    COUNT(DISTINCT IFF(N_INBOX > 0, USERNAME, NULL))   AS active_users,
    COUNT(DISTINCT IFF(N_REPLIES > 0, USERNAME, NULL)) AS repliers,
    SUM(N_REPLIES)          AS replies,
    SUM(N_REPLIES_AI)       AS replies_ai,
    SUM(N_REPLIES_TEMPLATED) AS replies_templated,
    SUM(N_MOBILE)           AS mobile_actions
FROM REPORTING.ADOPTION.MART_INBOX_DAILY_USER
GROUP BY 1, 2;

-- ------------------------------------------------------------
-- DIM_INBOX_USER — dimension utilisateur (rôle + 9 SAL), users avec signal Inbox
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.DIM_INBOX_USER AS
SELECT s.USERNAME, s.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY, s.N_ADMIN_PLACES,
    s.SAL_PLACE, s.SAL_ZONE, s.SAL_SECTOR, s.SAL_SUBTYPE, s.SAL_REGION,
    s.SAL_DEPARTMENT, s.SAL_COUNTRY, s.SAL_TYPE, s.SAL_BRAND
FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
WHERE EXISTS (
    SELECT 1 FROM REPORTING.ADOPTION.MART_INBOX_DAILY_USER d
    WHERE d.USERNAME = s.USERNAME AND d.CUSTOMER_ID = s.CUSTOMER_ID
);

-- ------------------------------------------------------------
-- MART_INBOX_USER_30D — 1 ligne par user avec signal Inbox, 30 j
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_USER_30D AS
WITH f AS (
    SELECT USERNAME, CUSTOMER_ID,
        SUM(N_INBOX) AS n_inbox, SUM(N_MOBILE) AS n_mobile,
        SUM(N_REPLIES) AS n_replies, SUM(N_REPLIES_AI) AS n_replies_ai,
        SUM(N_REPLIES_TEMPLATED) AS n_replies_templated
    FROM REPORTING.ADOPTION.MART_INBOX_DAILY_USER
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE)
    GROUP BY 1, 2
)
SELECT f.USERNAME, f.CUSTOMER_ID, s.CUSTOMER_NAME, s.ROLE, s.JOB_CATEGORY, s.N_ADMIN_PLACES,
    f.n_inbox, f.n_mobile, f.n_replies, f.n_replies_ai, f.n_replies_templated,
    -- funnel Inbox affiné (Alexis 2026-09-16) : connecté = a vu l'inbox OU a répondu.
    -- actif = a effectué au moins une action (réponse) — cf. section 6 du PRD, appliqué ici
    -- uniquement à l'Inbox (pas aux 2 autres modules, jugé non pertinent).
    -- Connecté est défini en OU (pas seulement n_inbox>0) car certaines réponses
    -- (notamment IA-assistées) n'émettent aucun événement de consultation BO_ACTIVITIES
    -- (2026-09-17 : ~80% des réponses IA sur Chaussea/Feu Vert concernées) — sans ce
    -- correctif, "Actifs" pouvait dépasser "Connectés", ce qui est incohérent par nature
    -- d'un funnel (un actif est toujours connecté).
    (f.n_inbox > 0 OR f.n_replies > 0) AS is_connected_inbox,
    (f.n_replies > 0)                  AS is_active_inbox
FROM f
JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s ON s.USERNAME = f.USERNAME AND s.CUSTOMER_ID = f.CUSTOMER_ID;

-- ------------------------------------------------------------
-- MART_INBOX_CUSTOMER_30D — maille compte (tous comptes, pas d'éligibilité)
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D AS
WITH cust AS (
    SELECT CUSTOMER_ID, CUSTOMER_NAME FROM REPORTING.ADOPTION.DIM_CUSTOMERS
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
        COUNT_IF(is_connected_inbox) AS connected_inbox_users,
        COUNT_IF(is_active_inbox)    AS active_inbox_users,
        SUM(n_inbox) AS inbox_actions, SUM(n_replies) AS replies, SUM(n_replies_ai) AS replies_ai,
        SUM(n_replies_templated) AS replies_templated, SUM(n_mobile) AS mobile_actions
    FROM REPORTING.ADOPTION.MART_INBOX_USER_30D GROUP BY 1
)
SELECT
    ct.CUSTOMER_ID, ct.CUSTOMER_NAME,
    COALESCE(r.roster, 0) AS roster,
    COALESCE(cn.connected_users, 0) AS connected_users,
    COALESCE(i.connected_inbox_users, 0) AS connected_inbox_users,
    COALESCE(i.active_inbox_users, 0) AS active_inbox_users,
    GREATEST(COALESCE(cn.connected_users, 0) - COALESCE(i.connected_inbox_users, 0), 0) AS connected_zero_inbox,
    COALESCE(i.inbox_actions, 0) AS inbox_actions,
    COALESCE(i.replies, 0) AS replies,
    COALESCE(i.replies_ai, 0) AS replies_ai,
    COALESCE(i.replies_templated, 0) AS replies_templated,
    COALESCE(i.mobile_actions, 0) AS mobile_actions
FROM cust ct
LEFT JOIN roster r ON r.CUSTOMER_ID = ct.CUSTOMER_ID
LEFT JOIN conn   cn ON cn.CUSTOMER_ID = ct.CUSTOMER_ID
LEFT JOIN ins    i ON i.CUSTOMER_ID = ct.CUSTOMER_ID
WHERE r.roster > 0;

-- MART_INBOX_UNIT_30D a été déplacée dans sql/build_hierarchy.sql (option B,
-- cf. build_insight.sql pour le contexte de la décision).

-- ------------------------------------------------------------
-- MART_INBOX_CULTURE_PLACE_SNAPSHOT — value driver "Culture Client", grain place.
-- Sources : MONTHLY_PLACE_CHECKUPS (ENGAGEMENT_SCORE = "note de relation client",
-- REPLY_RATE/REPLY_TIME/NOT_REPLIED_CONVERSATIONS = déjà confirmés Inbox, pas E-rép).
-- ENGAGEMENT_SCORE figé le 5 du mois pour le mois échu -> on prend le dernier
-- mois IS_FINISHED, + mois précédent (M-1) et même mois l'an dernier (N-1).
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_CULTURE_PLACE_SNAPSHOT AS
WITH last_month AS (
    SELECT MAX(MONTH_ID) AS m FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS WHERE IS_FINISHED
),
cur AS (
    SELECT c.PLACE_ID, c.CUSTOMER_ID, c.ENGAGEMENT_SCORE, c.REPLY_RATE, c.REPLY_TIME,
        c.NOT_REPLIED_CONVERSATIONS, c.TOTAL_CONVERSATIONS,
        (c.TOTAL_CONVERSATIONS - c.NOT_REPLIED_CONVERSATIONS) AS REPLIED_CONVERSATIONS
    FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS c, last_month lm
    WHERE c.MONTH_ID = lm.m
),
prevm AS (
    SELECT c.PLACE_ID, c.ENGAGEMENT_SCORE AS ENGAGEMENT_SCORE_M1,
        c.REPLY_RATE AS REPLY_RATE_M1, c.REPLY_TIME AS REPLY_TIME_M1,
        c.NOT_REPLIED_CONVERSATIONS AS NOT_REPLIED_CONVERSATIONS_M1
    FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS c, last_month lm
    WHERE c.MONTH_ID = TO_CHAR(ADD_MONTHS(TO_DATE(lm.m || '-01'), -1), 'YYYY-MM')
),
ly AS (
    SELECT c.PLACE_ID, c.ENGAGEMENT_SCORE AS ENGAGEMENT_SCORE_LY
    FROM MARTING_BUSINESS.ANALYTICS.MONTHLY_PLACE_CHECKUPS c, last_month lm
    WHERE c.MONTH_ID = TO_CHAR(ADD_MONTHS(TO_DATE(lm.m || '-01'), -12), 'YYYY-MM')
)
SELECT
    p.PLACE_ID, p.CUSTOMER_ID, p.PLACE_NAME,
    cur.ENGAGEMENT_SCORE, pm.ENGAGEMENT_SCORE_M1, ly.ENGAGEMENT_SCORE_LY,
    cur.REPLY_RATE, pm.REPLY_RATE_M1,
    cur.REPLY_TIME, pm.REPLY_TIME_M1,
    cur.REPLIED_CONVERSATIONS, cur.TOTAL_CONVERSATIONS,
    cur.NOT_REPLIED_CONVERSATIONS, pm.NOT_REPLIED_CONVERSATIONS_M1,
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
LEFT JOIN prevm pm ON pm.PLACE_ID = p.PLACE_ID
LEFT JOIN ly ON ly.PLACE_ID = p.PLACE_ID
JOIN REPORTING.ADOPTION.DIM_CUSTOMERS dc ON dc.CUSTOMER_ID = p.CUSTOMER_ID
WHERE cur.TOTAL_CONVERSATIONS IS NOT NULL AND cur.TOTAL_CONVERSATIONS > 0;

-- ------------------------------------------------------------
-- MART_INBOX_USER_ACTIVITY_30D — détail des "Consultations Inbox" par type
-- d'activité (30 j), pour la modale de détail au clic sur la colonne
-- "Consultations" du classement (Alexis 2026-09-17 : "Actions Inbox" prêtait
-- à confusion, comptait des rechargements de page comme des "actions").
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_INBOX_USER_ACTIVITY_30D AS
SELECT ba.USERNAME, ba.CUSTOMER_ID, ba.BO_ACTIVITY_NAME, COUNT(*) AS n
FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES ba
JOIN REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED s
    ON s.USERNAME = ba.USERNAME AND s.CUSTOMER_ID = ba.CUSTOMER_ID
WHERE ba.OCCURRING_DATE >= DATEADD('day', -30, CURRENT_DATE)
  AND ba.BO_ACTIVITY_NAME IN ('Inbox','Inbox list','Inbox show','Inbox search','Inbox action','Conversation','Metric · MESSAGES')
GROUP BY 1, 2, 3;
