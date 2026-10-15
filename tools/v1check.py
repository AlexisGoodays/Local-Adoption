#!/usr/bin/env python3
"""Validation V1 : une connexion, plusieurs contrôles alignés sur la Définition des metrics Notion."""
import csv, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

DATA = Path(__file__).resolve().parent.parent / "data"
DB = "MARTING_BUSINESS.ANALYTICS"

PERIMETER = f"""
    SELECT pu.USERNAME, pu.CUSTOMER_ID, pu.CUSTOMER_NAME
    FROM {DB}.PRO_USERS pu
    WHERE pu.ACCOUNT_STATUS = 'active'
      AND pu.HAS_VALID_BO_ACCOUNT = TRUE
    -- Filtre USER_INSIGHT_REPORT_CONFIGURATION retire le 2026-10-15, en meme temps
    -- que dans build_adoption.sql. Ce script recalcule le perimetre depuis les
    -- sources brutes : il doit donc suivre la meme definition, sinon il signale
    -- des ecarts qui n'existent pas.
    QUALIFY ROW_NUMBER() OVER (PARTITION BY pu.USERNAME, pu.CUSTOMER_ID
        ORDER BY pu.JOINED_AT DESC NULLS LAST, pu.USER_ID DESC) = 1
"""

QUERIES = {
    "activity_name_presence": f"""
        SELECT BO_ACTIVITY_NAME, COUNT(*) n_30d, COUNT(DISTINCT USERNAME) users_30d
        FROM {DB}.BO_ACTIVITIES
        WHERE OCCURRING_DATE >= DATEADD('day',-30,CURRENT_DATE)
          AND BO_ACTIVITY_NAME IN (
            'Topic drill-down · overview','Topic drill-down · thematic','Metric · SENTIMENT',
            'Metric · SENTIMENT_OVERVIEW','Insight Report Center','Inbox','Inbox list','Inbox show',
            'Inbox search','Inbox action','Conversation','Metric · MESSAGES',
            'Metric · GOOGLE_SCORE','Metric · GOOGLE_BENCHMARK')
        GROUP BY 1 ORDER BY n_30d DESC""",
    "insight_monitoring_status": f"""
        SELECT INSIGHT_MONITORING_STATUS, COUNT(*) n
        FROM {DB}.BO_WEB_PAGE_VIEWS
        WHERE OCCURRING_DATE >= DATEADD('day',-30,CURRENT_DATE)
        GROUP BY 1 ORDER BY n DESC""",
    "perimeter_size": f"SELECT COUNT(*) created_users, COUNT(DISTINCT CUSTOMER_ID) customers FROM ({PERIMETER})",
    "funnel_30d": f"""
        WITH perimeter AS ({PERIMETER}),
        act AS (
            SELECT ba.USERNAME, ba.CUSTOMER_ID, ba.BO_ACTIVITY_NAME
            FROM {DB}.BO_ACTIVITIES ba
            JOIN perimeter p ON p.USERNAME=ba.USERNAME AND p.CUSTOMER_ID=ba.CUSTOMER_ID
            WHERE ba.OCCURRING_DATE >= DATEADD('day',-30,CURRENT_DATE)
        ),
        wpv AS (
            SELECT bpv.USERNAME, bpv.CUSTOMER_ID
            FROM {DB}.BO_WEB_PAGE_VIEWS bpv
            JOIN perimeter p ON p.USERNAME=bpv.USERNAME AND p.CUSTOMER_ID=bpv.CUSTOMER_ID
            WHERE bpv.OCCURRING_DATE >= DATEADD('day',-30,CURRENT_DATE)
              AND bpv.INSIGHT_MONITORING_STATUS='monitored'
        )
        SELECT
          (SELECT COUNT(*) FROM perimeter) AS created_users,
          (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act) AS connected_users,
          (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM (
             SELECT USERNAME,CUSTOMER_ID FROM act WHERE BO_ACTIVITY_NAME IN
               ('Topic drill-down · overview','Metric · SENTIMENT','Metric · SENTIMENT_OVERVIEW')
             UNION SELECT USERNAME,CUSTOMER_ID FROM wpv)) AS active_insight,
          (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act WHERE BO_ACTIVITY_NAME IN
             ('Inbox','Inbox list','Inbox show','Inbox search','Inbox action','Conversation','Metric · MESSAGES')) AS active_inbox,
          (SELECT COUNT(DISTINCT USERNAME||'|'||CUSTOMER_ID) FROM act WHERE BO_ACTIVITY_NAME IN
             ('Metric · GOOGLE_SCORE','Metric · GOOGLE_BENCHMARK')) AS active_ereput
    """,
    "customers_semantic": f"""
        SELECT SEMANTIC_PROVIDER, COUNT(*) n,
               SUM(IFF(COALESCE(SEMANTIC_CLASSIFICATION_PLAN,'') NOT LIKE '-%',1,0)) plan_ok
        FROM {DB}.CUSTOMERS GROUP BY 1 ORDER BY n DESC""",
    "csm_lifecycle": f"""
        SELECT CSM_OWNER, RENEWAL_STATUS, COUNT(*) n FROM {DB}.CUSTOMERS
        GROUP BY 1,2 ORDER BY n DESC LIMIT 40""",
}


def main():
    load_env()
    import snowflake.connector
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser", client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None,
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE") or None,
    )
    cur = conn.cursor()
    try:
        cur.execute("USE WAREHOUSE " + (os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING"))
    except Exception as e:
        print("USE WAREHOUSE:", e)
    for name, sql in QUERIES.items():
        print(f"\n=== {name} ===")
        for i in range(4):
            try:
                cur.execute(sql); break
            except Exception as e:
                if "No active warehouse" in str(e) and i < 3:
                    time.sleep(8); cur.execute("USE WAREHOUSE " + (os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING")); continue
                print("  ! ERREUR:", e); sql = None; break
        if sql is None:
            continue
        cols = [c[0] for c in cur.description]; rows = cur.fetchall()
        with open(DATA / f"v1_{name}.csv", "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
        print("  " + " | ".join(cols))
        for r in rows[:40]:
            print("  " + " | ".join("" if v is None else str(v) for v in r))
    conn.close()
    print("\nTerminé.")


if __name__ == "__main__":
    main()
