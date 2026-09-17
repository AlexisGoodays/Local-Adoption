-- ============================================================
-- Écran 1 "Vue Portefeuille" — S'EXÉCUTE EN DERNIER dans la pipeline.
--
-- Principe (refonte 2026-09-17, suite à l'audit de cohérence) : le Portefeuille
-- ne recalcule JAMAIS sa propre notion d'"actif". Il relit les marts des 3 modules,
-- qui sont seuls maîtres de leur définition. Avant cette refonte, la définition
-- d'"actif" existait en double (ici ET dans chaque module) et avait divergé :
--   - "Actifs Inbox" : 36 346 au Portefeuille (= a consulté, définition V1)
--     contre 24 699 dans l'onglet (= a répondu, définition validée le 2026-09-16),
--     soit un écart sur 126 comptes sur 139.
--   - "Actifs Insight" : 1 425 contre 1 388, car le Portefeuille ignorait la
--     feature Quick Overview et comptait 41 utilisateurs Buffalo Grill, compte
--     pourtant non éligible Insight (donc absent de l'onglet).
-- D'où la règle : un même libellé = un même chiffre sur tous les écrans, par
-- construction et non par vigilance.
--
-- Dépendances (toutes doivent être construites AVANT) :
--   build_adoption (DIM_*, FCT_LOCAL_ADOPTION_DAILY, FCT_INBOX_REPLIES_DAILY)
--   build_insight / build_erep / build_inbox (MART_*_CUSTOMER_30D + faits jour)
-- ============================================================

-- ------------------------------------------------------------
-- MART_PORTFOLIO_30D — maille compte, fenêtre 30 j
-- "créés" et "connectés" restent définis ici (notions transverses) ;
-- les 3 "actifs" viennent des modules.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_PORTFOLIO_30D AS
WITH created AS (
    SELECT CUSTOMER_ID,
        COUNT(*) AS created_users,
        COUNT_IF(IS_LOCAL_SCOPE) AS created_users_local
    FROM REPORTING.ADOPTION.DIM_PRO_USERS_SCOPED
    GROUP BY 1
),
conn AS (
    SELECT CUSTOMER_ID, COUNT(DISTINCT USERNAME) AS connected_users
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE) AND IS_CONNECTED
    GROUP BY 1
),
rep AS (
    SELECT CUSTOMER_ID,
        SUM(N_REPLIES) AS inbox_replies,
        SUM(N_REPLIES_AI) AS inbox_replies_ai
    FROM REPORTING.ADOPTION.FCT_INBOX_REPLIES_DAILY
    WHERE ACTIVITY_DATE >= DATEADD('day', -30, CURRENT_DATE)
    GROUP BY 1
)
SELECT
    cr.CUSTOMER_ID,
    dc.CUSTOMER_NAME,
    dc.CSM_OWNER,
    dc.RENEWAL_STATUS,
    dc.IS_INSIGHT_ELIGIBLE,
    cr.created_users,
    cr.created_users_local,
    COALESCE(cn.connected_users, 0) AS connected_users,
    -- les 3 "actifs" = valeurs des modules, telles quelles (source unique de vérité)
    COALESCE(xi.active_inbox_users, 0)   AS active_inbox,
    COALESCE(xi.connected_inbox_users, 0) AS viewed_inbox,  -- a ouvert l'inbox (ancienne déf. V1), gardé pour info
    COALESCE(e.active_erep_users, 0)     AS active_ereput,
    COALESCE(i.active_insight_users, 0)  AS active_insight,
    COALESCE(rp.inbox_replies, 0)    AS inbox_replies,
    COALESCE(rp.inbox_replies_ai, 0) AS inbox_replies_ai,
    COALESCE(xi.active_inbox_users, 0) AS inbox_repliers,  -- = active_inbox depuis 2026-09-17 (même notion)
    DIV0(cn.connected_users, cr.created_users)      AS ratio_connected_created,
    DIV0(xi.active_inbox_users, cn.connected_users)  AS ratio_inbox,
    DIV0(e.active_erep_users, cn.connected_users)    AS ratio_ereput,
    DIV0(i.active_insight_users, cn.connected_users) AS ratio_insight,
    DIV0(rp.inbox_replies_ai, rp.inbox_replies)      AS ratio_replies_ai
FROM created cr
LEFT JOIN REPORTING.ADOPTION.DIM_CUSTOMERS dc ON dc.CUSTOMER_ID = cr.CUSTOMER_ID
LEFT JOIN conn cn ON cn.CUSTOMER_ID = cr.CUSTOMER_ID
LEFT JOIN rep  rp ON rp.CUSTOMER_ID = cr.CUSTOMER_ID
LEFT JOIN REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D   xi ON xi.CUSTOMER_ID = cr.CUSTOMER_ID
LEFT JOIN REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D    e  ON e.CUSTOMER_ID  = cr.CUSTOMER_ID
LEFT JOIN REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D i  ON i.CUSTOMER_ID  = cr.CUSTOMER_ID;

-- ------------------------------------------------------------
-- MART_PORTFOLIO_TREND_90D — courbe d'activité quotidienne (90 j).
-- Construite ici, à partir des faits des modules, pour la même raison que
-- ci-dessus : la courbe "Inbox" doit suivre la définition de l'onglet Inbox
-- (réponse) et non plus la consultation. Remplace la requête ad hoc qui vivait
-- dans tools/extract_portfolio.py.
-- ------------------------------------------------------------
CREATE OR REPLACE TABLE REPORTING.ADOPTION.MART_PORTFOLIO_TREND_90D AS
WITH d AS (
    SELECT DISTINCT ACTIVITY_DATE AS d
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY
    WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE)
),
cn AS (
    SELECT ACTIVITY_DATE AS d, COUNT(DISTINCT USERNAME || '|' || CUSTOMER_ID) AS connected
    FROM REPORTING.ADOPTION.FCT_LOCAL_ADOPTION_DAILY
    WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE) AND IS_CONNECTED
    GROUP BY 1
),
xb AS (
    SELECT ACTIVITY_DATE AS d, COUNT(DISTINCT USERNAME || '|' || CUSTOMER_ID) AS inbox
    FROM REPORTING.ADOPTION.MART_INBOX_DAILY_USER
    WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE) AND N_REPLIES > 0
    GROUP BY 1
),
er AS (
    SELECT ACTIVITY_DATE AS d, COUNT(DISTINCT USERNAME || '|' || CUSTOMER_ID) AS ereput
    FROM REPORTING.ADOPTION.FCT_EREP_USER_DAY
    WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE) AND IS_ACTIVE_EREP
    GROUP BY 1
),
ins AS (
    SELECT ACTIVITY_DATE AS d, COUNT(DISTINCT USERNAME || '|' || CUSTOMER_ID) AS insight
    FROM REPORTING.ADOPTION.FCT_INSIGHT_USER_DAY
    WHERE ACTIVITY_DATE >= DATEADD('day', -90, CURRENT_DATE) AND IS_ACTIVE_INSIGHT
    GROUP BY 1
)
SELECT d.d AS ACTIVITY_DATE,
    COALESCE(cn.connected, 0) AS CONNECTED,
    COALESCE(xb.inbox, 0)     AS INBOX,
    COALESCE(er.ereput, 0)    AS EREPUT,
    COALESCE(ins.insight, 0)  AS INSIGHT
FROM d
LEFT JOIN cn  ON cn.d  = d.d
LEFT JOIN xb  ON xb.d  = d.d
LEFT JOIN er  ON er.d  = d.d
LEFT JOIN ins ON ins.d = d.d
ORDER BY 1;
