#!/usr/bin/env python3
"""Extrait les marts Insight -> dashboard/insight.json"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

ROOT = Path(__file__).resolve().parent.parent
SEP = "\u0001"  # separateur level/unit (aligne dashboard)
DB = "REPORTING.ADOPTION"
WH = None


def q(cur, sql):
    for i in range(5):
        try:
            cur.execute(sql); break
        except Exception as e:
            if "No active warehouse" in str(e) and i < 4:
                time.sleep(10); cur.execute("USE WAREHOUSE " + WH); continue
            raise
    cols = [c[0].lower() for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    # les colonnes ARRAY Snowflake reviennent en chaîne JSON -> on les parse
    for row in rows:
        for k, v in row.items():
            if isinstance(v, str) and v[:1] in "[{":
                try:
                    row[k] = json.loads(v)
                except Exception:
                    pass
    return rows


def main():
    global WH
    load_env()
    WH = os.environ.get("SNOWFLAKE_WAREHOUSE") or "REPORTING"
    import snowflake.connector
    conn = snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"], user=os.environ["SNOWFLAKE_USER"],
        authenticator="externalbrowser", client_store_temporary_credential=True,
        role=os.environ.get("SNOWFLAKE_ROLE") or None, warehouse=WH,
    )
    cur = conn.cursor()
    cur.execute("USE WAREHOUSE " + WH)

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "window_days": 30,
        "customers": q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_CUSTOMER_30D ORDER BY connected_users DESC"),
        "users30d": q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_USER_30D"),
        "daily": q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_DAILY ORDER BY activity_date"),
        "units": q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_UNIT_30D"),
    }
    # noms de places par utilisateur -> dict "username|customer_id"
    up = q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_USER_PLACES")
    out["user_places"] = {
        f"{r['username']}|{r['customer_id']}": {"total": r["total_places"], "names": r["place_names"] or []}
        for r in up
    }

    # fait quotidien (filtre de période du classement) — clés compactes
    du = q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_DAILY_USER")
    out["daily_user"] = [
        {"k": f"{r['username']}|{r['customer_id']}", "d": str(r["activity_date"]),
         "ov": r["n_overview"], "sy": r["n_synthesis"], "th": r["n_thematic"], "mv": r["n_monitored_views"]}
        for r in du
    ]
    SAL = ["sal_place", "sal_zone", "sal_sector", "sal_subtype", "sal_region",
           "sal_department", "sal_country", "sal_type", "sal_brand"]
    di = q(cur, f"SELECT * FROM {DB}.DIM_INSIGHT_USER")
    out["user_dim"] = {
        f"{r['username']}|{r['customer_id']}": {
            "cn": r["customer_name"], "role": r["role"], "jc": r["job_category"],
            "np": r["n_admin_places"], "sal": [r[c] for c in SAL],
        }
        for r in di
    }
    if out["daily_user"]:
        out["data_min"] = min(x["d"] for x in out["daily_user"])
        out["data_max"] = max(x["d"] for x in out["daily_user"])

    # rattachement hiérarchique (option B) pour le filtre "Périmètre"
    uu = q(cur, f"""
        SELECT uu.USERNAME, uu.CUSTOMER_ID, uu.LEVEL, uu.UNIT_NAME
        FROM {DB}.DIM_USER_UNIT uu
        WHERE EXISTS (SELECT 1 FROM {DB}.MART_INSIGHT_DAILY_USER d
                      WHERE d.USERNAME = uu.USERNAME AND d.CUSTOMER_ID = uu.CUSTOMER_ID)""")
    umap = {}
    for r in uu:
        umap.setdefault(f"{r['username']}|{r['customer_id']}", []).append(r["level"] + SEP + r["unit_name"])
    out["user_units"] = umap
    out["perimeters"] = q(cur, f"SELECT * FROM {DB}.MART_INSIGHT_PERIMETER_30D")
    # dénominateurs "connectés" recalculés par période (2026-09-17) : permettent
    # d'afficher un ratio juste quand la période choisie n'est pas 30 j.
    out["connected_period"] = {
        str(r["customer_id"]): [r["connected_30d"], r["connected_prevmonth"],
                                r["connected_quarter"], r["connected_year"]]
        for r in q(cur, f"SELECT * FROM {DB}.MART_CONNECTED_PERIOD_CUSTOMER")
    }
    out["connected_period_unit"] = [
        [r["customer_id"], r["level"] + SEP + r["unit_name"], r["connected_30d"],
         r["connected_prevmonth"], r["connected_quarter"], r["connected_year"]]
        for r in q(cur, f"SELECT * FROM {DB}.MART_CONNECTED_PERIOD_UNIT")
    ]

    p = ROOT / "dashboard" / "insight.json"
    p.write_text(json.dumps(out, default=str))
    conn.close()
    print(f"customers {len(out['customers'])} | users30d {len(out['users30d'])} | daily {len(out['daily'])}"
          f" | daily_user {len(out.get('daily_user', []))} | user_dim {len(out.get('user_dim', {}))}"
          f" | span {out.get('data_min')}..{out.get('data_max')}")
    tot_active = sum(c["active_insight_users"] for c in out["customers"])
    print(f"actifs Insight (somme customers, 30j) = {tot_active}")
    print(f"-> {p} ({p.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
