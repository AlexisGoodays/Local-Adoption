-- ============================================================
-- Controles d'invariants de la couche REPORTING.ADOPTION
--
-- A rejouer apres TOUT changement de definition, et apres chaque
-- rafraichissement complet. Chaque ligne doit afficher le statut OK.
-- Une seule ligne "A VERIFIER" suffit a considerer que le dashboard
-- ne doit pas etre diffuse en l'etat.
--
--     python3 tools/sf.py -f sql/check_invariants.sql --max-rows 60
--
-- Les violations remontent en premier, avec un exemple nomme pour
-- savoir ou regarder.
--
-- Ce fichier est un filet de securite, pas une formalite. Les trois
-- incoherences majeures corrigees en septembre 2026 auraient toutes
-- ete attrapees ici : un meme libelle affichant deux nombres selon
-- l'ecran, un taux d'adoption superieur a 100 %, et des actifs sans
-- connectes correspondants.
--
-- NE PAS mettre de point-virgule dans les commentaires : tools/sf.py
-- decoupe naivement le fichier sur ce caractere.
-- ============================================================

WITH checks AS (

-- ---------- GARDE : les tables doivent contenir des donnees ----------
-- Sans ce controle, tous les autres passeraient au vert sur une base vide
-- ou partiellement construite, ce qui donnerait une fausse assurance.
SELECT 'T00 garde  un mart cle est vide' AS chk,
       (IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D) = 0, 1, 0)
      + IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D) = 0, 1, 0)
      + IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D) = 0, 1, 0)
      + IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D) = 0, 1, 0)
      + IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_PLACE_ADOPTION_CUSTOMER) = 0, 1, 0)
      + IFF((SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_CONNECTED_PERIOD_UNIT) = 0, 1, 0)) AS n,
       'comptes portefeuille : ' || (SELECT COUNT(*) FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D) AS exemple

-- ---------- ECRAN PORTEFEUILLE ----------
UNION ALL SELECT 'P01 portefeuille  connectes superieurs aux crees' AS chk, COUNT(*) AS n,
       MAX(customer_name || ' (' || connected_users || ' / ' || created_users || ')') AS exemple
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D WHERE connected_users > created_users
UNION ALL SELECT 'P02 portefeuille  actifs Inbox superieurs aux connectes', COUNT(*),
       MAX(customer_name || ' (' || active_inbox || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D WHERE active_inbox > connected_users
UNION ALL SELECT 'P03 portefeuille  actifs E-rep superieurs aux connectes', COUNT(*),
       MAX(customer_name || ' (' || active_ereput || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D WHERE active_ereput > connected_users
UNION ALL SELECT 'P04 portefeuille  actifs Insight superieurs aux connectes', COUNT(*),
       MAX(customer_name || ' (' || active_insight || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D WHERE active_insight > connected_users
UNION ALL SELECT 'P05 portefeuille  ratio connectes sur crees incoherent', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D
WHERE created_users > 0 AND ABS(ratio_connected_created - connected_users/NULLIF(created_users,0)) > 0.0001
UNION ALL SELECT 'P06 portefeuille  ratio Inbox incoherent', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D
WHERE connected_users > 0 AND ABS(ratio_inbox - active_inbox/NULLIF(connected_users,0)) > 0.0001
UNION ALL SELECT 'P07 portefeuille  ratio E-rep incoherent', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D
WHERE connected_users > 0 AND ABS(ratio_ereput - active_ereput/NULLIF(connected_users,0)) > 0.0001
UNION ALL SELECT 'P08 portefeuille  ratio Insight incoherent', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D
WHERE connected_users > 0 AND ABS(ratio_insight - active_insight/NULLIF(connected_users,0)) > 0.0001
UNION ALL SELECT 'P09 portefeuille  reponses IA superieures au total des reponses', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D WHERE inbox_replies_ai > inbox_replies

-- ---------- MODULE INSIGHT ----------
UNION ALL SELECT 'I01 Insight  actifs superieurs aux connectes (compte)', COUNT(*),
       MAX(customer_name || ' (' || active_insight_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D WHERE active_insight_users > connected_users
UNION ALL SELECT 'I02 Insight  connectes superieurs au parc de comptes', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D WHERE connected_users > roster
UNION ALL SELECT 'I03 Insight  une fonctionnalite depasse le total des actifs', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D
WHERE GREATEST(overview_users, thematic_users, synthesis_users) > active_insight_users
UNION ALL SELECT 'I04 Insight  actifs superieurs aux connectes (unite)', COUNT(*),
       MAX(unit_name || ' (' || active_insight_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_INSIGHT_UNIT_30D WHERE active_insight_users > connected_users

-- ---------- MODULE E-REPUTATION ----------
UNION ALL SELECT 'E01 E-rep  actifs superieurs aux connectes (compte)', COUNT(*),
       MAX(customer_name || ' (' || active_erep_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D WHERE active_erep_users > connected_users
UNION ALL SELECT 'E02 E-rep  acces score ou benchmark superieurs aux connectes', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D
WHERE GREATEST(connected_score_access, connected_bench_access) > connected_users
UNION ALL SELECT 'E03 E-rep  une fonctionnalite depasse le total des actifs', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D
WHERE GREATEST(score_users, bench_users) > active_erep_users
UNION ALL SELECT 'E04 E-rep  actifs superieurs aux connectes (unite)', COUNT(*),
       MAX(unit_name || ' (' || active_erep_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_EREP_UNIT_30D WHERE active_erep_users > connected_users

-- ---------- MODULE INBOX ----------
UNION ALL SELECT 'X01 Inbox  actifs superieurs aux connectes Inbox (compte)', COUNT(*),
       MAX(customer_name || ' (' || active_inbox_users || ' / ' || connected_inbox_users || ')')
FROM REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D WHERE active_inbox_users > connected_inbox_users
UNION ALL SELECT 'X02 Inbox  connectes Inbox superieurs aux connectes globaux (compte)', COUNT(*),
       MAX(customer_name || ' (' || connected_inbox_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D WHERE connected_inbox_users > connected_users
UNION ALL SELECT 'X03 Inbox  actifs superieurs aux connectes Inbox (unite)', COUNT(*),
       MAX(unit_name || ' (' || active_inbox_users || ' / ' || connected_inbox_users || ')')
FROM REPORTING.ADOPTION.MART_INBOX_UNIT_30D WHERE active_inbox_users > connected_inbox_users
UNION ALL SELECT 'X04 Inbox  connectes Inbox superieurs aux connectes (unite)', COUNT(*),
       MAX(unit_name || ' (' || connected_inbox_users || ' / ' || connected_users || ')')
FROM REPORTING.ADOPTION.MART_INBOX_UNIT_30D WHERE connected_inbox_users > connected_users
UNION ALL SELECT 'X05 Inbox  reponses IA superieures au total des reponses (compte)', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D WHERE replies_ai > replies

-- ---------- COHERENCE ENTRE ECRANS ----------
-- Un meme libelle doit afficher le meme nombre partout. C'est la regle
-- que le Portefeuille respecte en relisant les marts des modules.
UNION ALL SELECT 'C01 connectes  Portefeuille different du mart Inbox', COUNT(*),
       MAX(p.customer_name || ' (' || p.connected_users || ' vs ' || i.connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D i ON i.customer_id = p.customer_id
WHERE p.connected_users <> i.connected_users
UNION ALL SELECT 'C02 connectes  Portefeuille different du mart E-rep', COUNT(*),
       MAX(p.customer_name || ' (' || p.connected_users || ' vs ' || e.connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D e ON e.customer_id = p.customer_id
WHERE p.connected_users <> e.connected_users
UNION ALL SELECT 'C03 connectes  Portefeuille different du mart Insight', COUNT(*),
       MAX(p.customer_name || ' (' || p.connected_users || ' vs ' || s.connected_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D s ON s.customer_id = p.customer_id
WHERE p.connected_users <> s.connected_users
UNION ALL SELECT 'C04 actifs Insight  Portefeuille different de l onglet', COUNT(*),
       MAX(p.customer_name || ' (' || p.active_insight || ' vs ' || s.active_insight_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_INSIGHT_CUSTOMER_30D s ON s.customer_id = p.customer_id
WHERE p.active_insight <> s.active_insight_users
UNION ALL SELECT 'C05 actifs E-rep  Portefeuille different de l onglet', COUNT(*),
       MAX(p.customer_name || ' (' || p.active_ereput || ' vs ' || e.active_erep_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_EREP_CUSTOMER_30D e ON e.customer_id = p.customer_id
WHERE p.active_ereput <> e.active_erep_users
UNION ALL SELECT 'C06 actifs Inbox  Portefeuille different de l onglet', COUNT(*),
       MAX(p.customer_name || ' (' || p.active_inbox || ' vs ' || i.active_inbox_users || ')')
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D p
JOIN REPORTING.ADOPTION.MART_INBOX_CUSTOMER_30D i ON i.customer_id = p.customer_id
WHERE p.active_inbox <> i.active_inbox_users

-- ---------- ADOPTION A LA MAILLE ETABLISSEMENT ----------
UNION ALL SELECT 'L01 etablissements  actifs superieurs au parc local (compte)', COUNT(*), MAX(TO_VARCHAR(customer_id))
FROM REPORTING.ADOPTION.MART_PLACE_ADOPTION_CUSTOMER
WHERE GREATEST(insight_30d, erep_30d, inbox_30d, insight_year, erep_year, inbox_year) > places_local
UNION ALL SELECT 'L02 etablissements  actifs superieurs au parc local (unite)', COUNT(*), MAX(unit_name)
FROM REPORTING.ADOPTION.MART_PLACE_ADOPTION_UNIT
WHERE GREATEST(insight_30d, erep_30d, inbox_30d, insight_year, erep_year, inbox_year) > places_local
-- Un etablissement appartient a exactement une unite par niveau. La somme des
-- unites ne doit donc jamais depasser le total du compte. Elle peut en revanche
-- etre inferieure, quand des etablissements n'ont pas de valeur a ce niveau.
UNION ALL SELECT 'L03 etablissements  double comptage entre unites d un meme niveau', COUNT(*),
       MAX(u.level || ' / compte ' || TO_VARCHAR(u.customer_id))
FROM (SELECT customer_id, level, SUM(places_local) AS sp
      FROM REPORTING.ADOPTION.MART_PLACE_ADOPTION_UNIT GROUP BY 1, 2) u
JOIN REPORTING.ADOPTION.MART_PLACE_ADOPTION_CUSTOMER c ON c.customer_id = u.customer_id
WHERE u.sp > c.places_local

-- ---------- VALEURS ABERRANTES ----------
UNION ALL SELECT 'V01 unites  nom vide ou absent', COUNT(*), MAX(level)
FROM (SELECT level, unit_name FROM REPORTING.ADOPTION.MART_INSIGHT_UNIT_30D
      UNION ALL SELECT level, unit_name FROM REPORTING.ADOPTION.MART_EREP_UNIT_30D
      UNION ALL SELECT level, unit_name FROM REPORTING.ADOPTION.MART_INBOX_UNIT_30D
      UNION ALL SELECT level, unit_name FROM REPORTING.ADOPTION.MART_PLACE_ADOPTION_UNIT)
WHERE unit_name IS NULL OR TRIM(unit_name) = ''
UNION ALL SELECT 'V02 Inbox  unite sans connecte mais avec des consultations', COUNT(*), MAX(unit_name)
FROM REPORTING.ADOPTION.MART_INBOX_UNIT_30D WHERE connected_users = 0 AND inbox_actions > 0
UNION ALL SELECT 'V03 portefeuille  valeur negative', COUNT(*), MAX(customer_name)
FROM REPORTING.ADOPTION.MART_PORTFOLIO_30D
WHERE LEAST(created_users, connected_users, active_inbox, active_ereput, active_insight, inbox_replies) < 0

)
SELECT chk AS controle, n AS violations,
       IFF(n = 0, 'OK', 'A VERIFIER') AS statut,
       exemple
FROM checks
ORDER BY n DESC, chk;
