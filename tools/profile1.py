#!/usr/bin/env python3
"""Profilage des tables d'usage BO_* + PRO_USERS. Une seule connexion."""
import csv
import time
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env  # noqa: E402

DATA = Path(__file__).resolve().parent.parent / "data"
DATA.mkdir(exist_ok=True)

DB = "MARTING_BUSINESS.ANALYTICS"

QUERIES = {
    "bo_activities_span": f"""
        SELECT MIN(OCCURRING_DATE) min_d, MAX(OCCURRING_DATE) max_d,
               COUNT(*) rows_, COUNT(DISTINCT USERNAME) users_, COUNT(DISTINCT CUSTOMER_ID) customers_,
               SUM(IFF(USERNAME IS NULL,1,0)) null_user, SUM(IFF(CUSTOMER_ID IS NULL,1,0)) null_cust
        FROM {DB}.BO_ACTIVITIES""",
    "bo_activities_type": f"""
        SELECT BO_ACTIVITY_TYPE, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_ACTIVITIES GROUP BY 1 ORDER BY n DESC LIMIT 60""",
    "bo_activities_name": f"""
        SELECT BO_ACTIVITY_TYPE, BO_ACTIVITY_NAME, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_ACTIVITIES GROUP BY 1,2 ORDER BY n DESC LIMIT 100""",
    "bo_activities_platform": f"""
        SELECT BO_PLATFORM, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_ACTIVITIES GROUP BY 1 ORDER BY n DESC""",
    "bo_activities_recent_daily": f"""
        SELECT OCCURRING_DATE d, COUNT(*) n, COUNT(DISTINCT USERNAME) dau, COUNT(DISTINCT CUSTOMER_ID) customers_
        FROM {DB}.BO_ACTIVITIES WHERE OCCURRING_DATE >= DATEADD('day',-45,CURRENT_DATE)
        GROUP BY 1 ORDER BY 1""",
    "bo_events_span": f"""
        SELECT MIN(BO_EVENT_OCCURED_AT) min_t, MAX(BO_EVENT_OCCURED_AT) max_t,
               COUNT(*) rows_, COUNT(DISTINCT USERNAME) users_, COUNT(DISTINCT CUSTOMER_ID) customers_,
               COUNT(DISTINCT BO_SESSION_ID) sessions_, SUM(IFF(USERNAME IS NULL,1,0)) null_user
        FROM {DB}.BO_EVENTS""",
    "bo_events_page": f"""
        SELECT BO_PAGE_NAME, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_EVENTS GROUP BY 1 ORDER BY n DESC LIMIT 80""",
    "bo_wpv_span": f"""
        SELECT MIN(OCCURRING_DATE) min_d, MAX(OCCURRING_DATE) max_d, COUNT(*) rows_,
               COUNT(DISTINCT USERNAME) users_, COUNT(DISTINCT CUSTOMER_ID) customers_
        FROM {DB}.BO_WEB_PAGE_VIEWS""",
    "bo_wpv_page": f"""
        SELECT PAGE_NAME, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_WEB_PAGE_VIEWS GROUP BY 1 ORDER BY n DESC LIMIT 60""",
    "bo_wpv_metric": f"""
        SELECT METRIC_NAME, COUNT(*) n, COUNT(DISTINCT USERNAME) users_
        FROM {DB}.BO_WEB_PAGE_VIEWS GROUP BY 1 ORDER BY n DESC LIMIT 60""",
    "pro_users_overview": f"""
        SELECT COUNT(*) users_, COUNT(DISTINCT CUSTOMER_ID) customers_,
               SUM(IFF(IS_USER_ACTIVE,1,0)) active_, SUM(IFF(HAS_VALID_BO_ACCOUNT,1,0)) valid_bo_,
               MIN(JOINED_AT) min_joined, MAX(JOINED_AT) max_joined,
               SUM(IFF(FIRST_SEEN_AT IS NULL,1,0)) never_seen
        FROM {DB}.PRO_USERS""",
    "pro_users_by_role": f"""
        SELECT ROLE, JOB_CATEGORY, COUNT(*) n, SUM(IFF(IS_USER_ACTIVE,1,0)) active_
        FROM {DB}.PRO_USERS GROUP BY 1,2 ORDER BY n DESC LIMIT 60""",
    "pro_users_training": f"""
        SELECT TRAINING_STATUS, BO_MODE, COUNT(*) n FROM {DB}.PRO_USERS GROUP BY 1,2 ORDER BY n DESC""",
    "customers_overview": f"""
        SELECT COUNT(*) n FROM {DB}.CUSTOMERS""",
}


def main():
    load_env()
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None,
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE") or None,
    )
    cur = conn.cursor()
    try:
        cur.execute("USE WAREHOUSE " + (os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING"))
    except Exception as e:  # noqa: BLE001
        print(f"USE WAREHOUSE: {e}")

    def run_with_retry(sql, tries=4):
        for i in range(tries):
            try:
                cur.execute(sql)
                return True
            except Exception as e:  # noqa: BLE001
                if "No active warehouse" in str(e) and i < tries - 1:
                    time.sleep(8)
                    cur.execute("USE WAREHOUSE " + (os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING"))
                    continue
                print(f"  ! ERREUR: {e}")
                return False
        return False

    for name, sql in QUERIES.items():
        print(f"\n=== {name} ===")
        if not run_with_retry(sql):
            continue
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        with open(DATA / f"p_{name}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(rows)
        print("  " + " | ".join(cols))
        for r in rows[:40]:
            print("  " + " | ".join("" if v is None else str(v) for v in r))
        if len(rows) > 40:
            print(f"  ... (+{len(rows) - 40}) -> data/p_{name}.csv")
    conn.close()
    print("\nTerminé.")


if __name__ == "__main__":
    main()
