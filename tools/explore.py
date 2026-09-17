#!/usr/bin/env python3
"""Exploration one-shot : UNE seule connexion (donc un seul login SSO),
plusieurs requêtes d'inventaire, résultats écrits en CSV dans data/.

Usage : python3 tools/explore.py
"""
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data"
DATA.mkdir(exist_ok=True)


def dump(cur, sql, out_name, echo_rows=15):
    print(f"\n=== {out_name} ===")
    print(sql.strip().splitlines()[0][:120])
    try:
        cur.execute(sql)
    except Exception as e:  # noqa: BLE001
        print(f"  ! ERREUR: {e}")
        return
    cols = [c[0] for c in cur.description] if cur.description else []
    rows = cur.fetchall() if cur.description else []
    if out_name:
        with open(DATA / f"{out_name}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(rows)
    print(f"  {len(rows)} lignes -> data/{out_name}.csv" if out_name else f"  {len(rows)} lignes")
    print("  " + " | ".join(cols))
    for r in rows[:echo_rows]:
        print("  " + " | ".join("" if v is None else str(v) for v in r))
    if len(rows) > echo_rows:
        print(f"  ... (+{len(rows) - echo_rows})")


def main():
    load_env()
    import snowflake.connector

    db = os.environ.get("SNOWFLAKE_DATABASE", "MARTING_BUSINESS")
    wh = os.environ.get("SNOWFLAKE_WAREHOUSE", "REPORTING")

    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser",
        client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None,
    )
    cur = conn.cursor()

    dump(cur, "SELECT CURRENT_ROLE() r, CURRENT_SECONDARY_ROLES() sr, CURRENT_WAREHOUSE() wh, CURRENT_VERSION() v", "session_before")
    dump(cur, "SHOW GRANTS TO USER " + os.environ["SNOWFLAKE_USER"], "grants_to_user")

    # Essaie d'activer le warehouse
    for stmt in (f"USE WAREHOUSE {wh}", "USE SECONDARY ROLES ALL"):
        try:
            cur.execute(stmt)
            print(f"OK: {stmt}")
        except Exception as e:  # noqa: BLE001
            print(f"! {stmt} -> {e}")

    dump(cur, "SELECT CURRENT_ROLE() r, CURRENT_WAREHOUSE() wh", "session_after")

    dump(cur, f"SHOW SCHEMAS IN DATABASE {db}", "schemas")
    dump(
        cur,
        f"""SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE, ROW_COUNT, BYTES, LAST_ALTERED
            FROM {db}.INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA <> 'INFORMATION_SCHEMA'
            ORDER BY TABLE_SCHEMA, ROW_COUNT DESC NULLS LAST""",
        "tables_inventory",
        echo_rows=60,
    )
    dump(
        cur,
        f"""SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE, ORDINAL_POSITION, IS_NULLABLE
            FROM {db}.INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA <> 'INFORMATION_SCHEMA'
            ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION""",
        "columns_inventory",
        echo_rows=0,
    )

    conn.close()
    print("\nTerminé. Fichiers dans data/.")


if __name__ == "__main__":
    main()
