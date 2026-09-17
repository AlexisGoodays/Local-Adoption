#!/usr/bin/env python3
"""Extrait les marts Inbox -> dashboard/inbox.json (même forme qu'insight.json/erep.json).

NB volumétrie : MART_INBOX_DAILY_USER (grain user x jour) fait 4,1M lignes —
l'inbox est consultée en continu, contrairement à Insight/E-rép. On n'exporte
donc PAS ce grain brut ; seule sa version agrégée customer x jour
(MART_INBOX_CUSTOMER_DAY, ~45k lignes) est embarquée, pour la courbe
d'évolution période-flexible. Le classement/top-adopters/KPIs d'usage
restent sur les marts *_30D (fenêtre fixe 30 j, comme les dénominateurs
"connectés" ailleurs dans le dashboard).
"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

ROOT = Path(__file__).resolve().parent.parent
SEP = ""  # separateur level/unit (aligne dashboard)
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
        "customers": q(cur, f"SELECT * FROM {DB}.MART_INBOX_CUSTOMER_30D ORDER BY connected_users DESC"),
        "users30d": q(cur, f"SELECT * FROM {DB}.MART_INBOX_USER_30D"),
        "units": q(cur, f"SELECT * FROM {DB}.MART_INBOX_UNIT_30D"),
    }

    cd = q(cur, f"SELECT * FROM {DB}.MART_INBOX_CUSTOMER_DAY ORDER BY activity_date")
    out["customer_day"] = [
        {"k": r["customer_id"], "d": str(r["activity_date"]),
         "au": r["active_users"], "rp": r["repliers"], "r": r["replies"],
         "ra": r["replies_ai"], "rt": r["replies_templated"], "m": r["mobile_actions"]}
        for r in cd
    ]
    if out["customer_day"]:
        out["data_min"] = min(x["d"] for x in out["customer_day"])
        out["data_max"] = max(x["d"] for x in out["customer_day"])

    # Inbox n'a pas de filtre d'éligibilité -> bien plus d'utilisateurs qu'Insight/E-rép
    # (35k+) -> cap plus bas sur les noms de places embarqués (inbox.json déjà ~70 MB).
    up = q(cur, f"""
        SELECT pa.USERNAME, pa.CUSTOMER_ID,
            COUNT(DISTINCT p.PLACE_NAME) AS total_places,
            ARRAY_SLICE(ARRAY_UNIQUE_AGG(p.PLACE_NAME), 0, 10) AS place_names
        FROM MARTING_BUSINESS.ANALYTICS.PLACE_ADMINISTRATIONS pa
        JOIN {DB}.DIM_INBOX_USER u ON u.USERNAME = pa.USERNAME AND u.CUSTOMER_ID = pa.CUSTOMER_ID
        JOIN MARTING_BUSINESS.ANALYTICS.PLACES p ON p.PLACE_ID = CAST(pa.PLACE_ID AS VARCHAR)
        GROUP BY 1, 2
        HAVING COUNT(DISTINCT p.PLACE_NAME) > 1""")
    out["user_places"] = {
        f"{r['username']}|{r['customer_id']}": {"total": r["total_places"], "names": r["place_names"] or []}
        for r in up
    }

    # détail "Consultations Inbox" par type d'activité (30 j), pour la modale au clic
    ba = q(cur, f"SELECT * FROM {DB}.MART_INBOX_USER_ACTIVITY_30D")
    bmap = {}
    for r in ba:
        bmap.setdefault(f"{r['username']}|{r['customer_id']}", []).append([r["bo_activity_name"], r["n"]])
    out["user_activity_breakdown"] = bmap

    SAL = ["sal_place", "sal_zone", "sal_sector", "sal_subtype", "sal_region",
           "sal_department", "sal_country", "sal_type", "sal_brand"]
    di = q(cur, f"SELECT * FROM {DB}.DIM_INBOX_USER")
    out["user_dim"] = {
        f"{r['username']}|{r['customer_id']}": {
            "cn": r["customer_name"], "role": r["role"], "jc": r["job_category"],
            "np": r["n_admin_places"], "sal": [r[c] for c in SAL],
        }
        for r in di
    }

    # rattachement hiérarchique (option B) pour le filtre "Périmètre"
    uu = q(cur, f"""
        SELECT uu.USERNAME, uu.CUSTOMER_ID, uu.LEVEL, uu.UNIT_NAME
        FROM {DB}.DIM_USER_UNIT uu
        WHERE EXISTS (SELECT 1 FROM {DB}.MART_INBOX_DAILY_USER d
                      WHERE d.USERNAME = uu.USERNAME AND d.CUSTOMER_ID = uu.CUSTOMER_ID)""")
    umap = {}
    for r in uu:
        umap.setdefault(f"{r['username']}|{r['customer_id']}", []).append(r["level"] + SEP + r["unit_name"])
    out["user_units"] = umap
    out["perimeters"] = q(cur, f"SELECT * FROM {DB}.MART_INBOX_PERIMETER_30D")
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

    # value driver "Culture Client" — grain place
    U_COLS = ["u_place", "u_zone", "u_sector", "u_subtype", "u_region",
              "u_department", "u_country", "u_type", "u_brand"]
    snap = q(cur, f"SELECT * FROM {DB}.MART_INBOX_CULTURE_PLACE_SNAPSHOT")
    out["culture_place_snapshot"] = [
        {"p": r["place_id"], "c": r["customer_id"],
         "es": r["engagement_score"], "esm1": r["engagement_score_m1"], "esly": r["engagement_score_ly"],
         "rr": r["reply_rate"], "rrm1": r["reply_rate_m1"],
         "rtime": r["reply_time"], "rtimem1": r["reply_time_m1"],
         "repc": r["replied_conversations"], "totc": r["total_conversations"],
         "notr": r["not_replied_conversations"], "notrm1": r["not_replied_conversations_m1"],
         "u": [r[c] for c in U_COLS]}
        for r in snap
    ]

    p = ROOT / "dashboard" / "inbox.json"
    p.write_text(json.dumps(out, default=str))
    conn.close()
    print(f"customers {len(out['customers'])} | users30d {len(out['users30d'])} | units {len(out['units'])}"
          f" | customer_day {len(out['customer_day'])} | culture_place_snapshot {len(out['culture_place_snapshot'])}"
          f" | span {out.get('data_min')}..{out.get('data_max')}")
    tot_active = sum(c["active_inbox_users"] for c in out["customers"])
    print(f"actifs Inbox (somme customers, 30j) = {tot_active}")
    print(f"-> {p} ({p.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
