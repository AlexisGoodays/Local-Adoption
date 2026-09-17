-- Validation V1 : périmètre commun + funnel global + actifs par module (30 derniers jours)
-- Aligné sur Notion "Définition des metrics". Maille customer, dédoublonnage username+customer.

WITH perimeter AS (
    SELECT pu.USERNAME, pu.CUSTOMER_ID, pu.CUSTOMER_NAME
    FROM MARTING_BUSINESS.ANALYTICS.PRO_USERS pu
    WHERE pu.ACCOUNT_STATUS = 'active'
      AND pu.HAS_VALID_BO_ACCOUNT = TRUE
      AND COALESCE(pu.USER_INSIGHT_REPORT_CONFIGURATION, '') <> 'specifically enabled'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY pu.USERNAME, pu.CUSTOMER_ID
        ORDER BY pu.JOINED_AT DESC NULLS LAST, pu.USER_ID DESC
    ) = 1
),
d AS (SELECT DATEADD('day', -30, CURRENT_DATE) AS start_d, CURRENT_DATE AS end_d),
act AS (  -- activités BO sur la période, restreintes au périmètre
    SELECT ba.USERNAME, ba.CUSTOMER_ID, ba.BO_ACTIVITY_NAME
    FROM MARTING_BUSINESS.ANALYTICS.BO_ACTIVITIES ba
    JOIN perimeter p ON p.USERNAME = ba.USERNAME AND p.CUSTOMER_ID = ba.CUSTOMER_ID
    CROSS JOIN d
    WHERE ba.OCCURRING_DATE >= d.start_d AND ba.OCCURRING_DATE < d.end_d
),
wpv AS (
    SELECT bpv.USERNAME, bpv.CUSTOMER_ID
    FROM MARTING_BUSINESS.ANALYTICS.BO_WEB_PAGE_VIEWS bpv
    JOIN perimeter p ON p.USERNAME = bpv.USERNAME AND p.CUSTOMER_ID = bpv.CUSTOMER_ID
    CROSS JOIN d
    WHERE bpv.OCCURRING_DATE >= d.start_d AND bpv.OCCURRING_DATE < d.end_d
      AND bpv.INSIGHT_MONITORING_STATUS = 'monitored'
)
SELECT
    (SELECT COUNT(*) FROM perimeter)                                             AS created_users,
    (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act)                 AS connected_users,
    (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act
       WHERE BO_ACTIVITY_NAME IN ('Topic drill-down · overview','Metric · SENTIMENT','Metric · SENTIMENT_OVERVIEW'))
     + (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM wpv)              AS active_insight_upper_bound,
    (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act
       WHERE BO_ACTIVITY_NAME IN ('Inbox','Inbox list','Inbox show','Inbox search','Inbox action','Conversation','Metric · MESSAGES')) AS active_inbox,
    (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act
       WHERE BO_ACTIVITY_NAME IN ('Metric · GOOGLE_SCORE','Metric · GOOGLE_BENCHMARK'))                                               AS active_ereput
;
