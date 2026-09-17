#!/usr/bin/env python3
"""Exécute un fichier .sql instruction par instruction (une connexion).
Retry sur warehouse endormi. Affiche COUNT(*) après chaque CREATE TABLE.

Usage : python3 tools/build.py sql/build_adoption.sql
"""
import os, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

WH = None


def strip_sql_comments(text):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("--"):
            continue
        out.append(line)
    return "\n".join(out)


def split_statements(text):
    return [s.strip() for s in text.split(";") if s.strip()]


def exec_retry(cur, sql, tries=5):
    for i in range(tries):
        try:
            cur.execute(sql)
            return
        except Exception as e:
            if "No active warehouse" in str(e) and i < tries - 1:
                time.sleep(10)
                cur.execute("USE WAREHOUSE " + WH)
                continue
            raise


def main():
    global WH
    load_env()
    WH = os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING"
    path = Path(sys.argv[1])
    stmts = split_statements(strip_sql_comments(path.read_text()))

    import snowflake.connector
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser", client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None, warehouse=WH,
    )
    cur = conn.cursor()
    try:
        cur.execute("USE WAREHOUSE " + WH)
    except Exception as e:
        print("USE WAREHOUSE:", e)

    for n, stmt in enumerate(stmts, 1):
        head = re.sub(r"\s+", " ", stmt)[:90]
        print(f"\n[{n}/{len(stmts)}] {head}")
        t0 = time.time()
        try:
            exec_retry(cur, stmt)
        except Exception as e:
            print(f"  ! ERREUR: {e}")
            break
        dt = time.time() - t0
        m = re.search(r"CREATE\s+(?:OR\s+REPLACE\s+)?TABLE\s+([A-Z0-9_.]+)", stmt, re.I)
        if m:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {m.group(1)}")
                print(f"  OK {dt:.1f}s — {m.group(1)} = {cur.fetchone()[0]:,} lignes")
            except Exception as e:
                print(f"  OK {dt:.1f}s (count KO: {e})")
        else:
            print(f"  OK {dt:.1f}s")
    conn.close()
    print("\nTerminé.")


if __name__ == "__main__":
    main()
