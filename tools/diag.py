#!/usr/bin/env python3
import os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

def run(cur, sql, label):
    print(f"\n=== {label} ===")
    try:
        cur.execute(sql)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
        if cols:
            print("  " + " | ".join(cols))
        for r in rows[:60]:
            print("  " + " | ".join("" if v is None else str(v) for v in r))
    except Exception as e:
        print(f"  ! {e}")

def main():
    load_env()
    import snowflake.connector
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None,
    )
    cur = conn.cursor()
    run(cur, "SHOW GRANTS TO ROLE REPORTER", "grants to ROLE REPORTER")
    run(cur, "SHOW WAREHOUSES", "warehouses visibles")
    run(cur, "ALTER WAREHOUSE REPORTING RESUME IF SUSPENDED", "tentative RESUME REPORTING")
    for i in range(6):
        try:
            cur.execute("USE WAREHOUSE REPORTING")
            cur.execute("SELECT CURRENT_WAREHOUSE() wh, 1 ok")
            print(f"\nsmoke test OK (essai {i+1}): {cur.fetchall()}")
            break
        except Exception as e:
            print(f"  smoke essai {i+1}: {e}")
            time.sleep(10)
    conn.close()

if __name__ == "__main__":
    main()
