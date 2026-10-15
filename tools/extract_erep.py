#!/usr/bin/env python3
"""Extrait les marts E-réputation -> dashboard/erep.json (même forme qu'insight.json)."""
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
        "customers": q(cur, f"""SELECT *, active_erep_users AS active_insight_users
                                FROM {DB}.MART_EREP_CUSTOMER_30D ORDER BY connected_users DESC"""),
        "users30d": q(cur, f"""SELECT USERNAME, CUSTOMER_ID, CUSTOMER_NAME, ROLE, JOB_CATEGORY,
                                   N_ADMIN_PLACES, CAN_GOOGLE_SCORE, EREP_BENCH_ENABLED,
                                   SCORE AS OVERVIEW, BENCHMARK AS SYNTHESIS, 0 AS THEMATIC,
                                   EREP_ACTIONS AS INSIGHT_ACTIONS, IS_ACTIVE
                                FROM {DB}.MART_EREP_USER_30D"""),
        "daily": q(cur, f"""SELECT CUSTOMER_ID, ACTIVITY_DATE, ACTIVE_USERS,
                                SCORE_USERS AS OVERVIEW_USERS, BENCH_USERS AS SYNTHESIS_USERS,
                                0 AS THEMATIC_USERS,
                                SCORE_ACTIONS AS OVERVIEW_ACTIONS, BENCH_ACTIONS AS SYNTHESIS_ACTIONS,
                                0 AS THEMATIC_ACTIONS
                            FROM {DB}.MART_EREP_DAILY ORDER BY ACTIVITY_DATE"""),
        # noms de champs alignés sur insight.json (overview=score, synthesis=benchmark, thematic=0)
        # place_names NON embarqués au niveau unité (volumétrie).
        "units": q(cur, f"""SELECT CUSTOMER_ID, LEVEL, UNIT_NAME, CONNECTED_USERS,
                                   ACTIVE_EREP_USERS AS ACTIVE_INSIGHT_USERS,
                                   EREP_ACTIONS      AS INSIGHT_ACTIONS,
                                   SCORE_ACTIONS     AS OVERVIEW_ACTIONS,
                                   BENCH_ACTIONS     AS SYNTHESIS_ACTIONS,
                                   PLACE_COUNT
                            FROM {DB}.MART_EREP_UNIT_30D"""),
    }

    up = q(cur, f"""
        SELECT pa.USERNAME, pa.CUSTOMER_ID,
            COUNT(DISTINCT p.PLACE_NAME) AS total_places,
            ARRAY_SLICE(ARRAY_UNIQUE_AGG(p.PLACE_NAME), 0, 25) AS place_names
        FROM MARTING_BUSINESS.ANALYTICS.PLACE_ADMINISTRATIONS pa
        JOIN {DB}.MART_EREP_USER_30D u ON u.USERNAME = pa.USERNAME AND u.CUSTOMER_ID = pa.CUSTOMER_ID
        JOIN MARTING_BUSINESS.ANALYTICS.PLACES p ON p.PLACE_ID = CAST(pa.PLACE_ID AS VARCHAR)
        GROUP BY 1, 2""")
    out["user_places"] = {
        f"{r['username']}|{r['customer_id']}": {"total": r["total_places"], "names": r["place_names"] or []}
        for r in up
    }

    du = q(cur, f"SELECT * FROM {DB}.MART_EREP_DAILY_USER")
    out["daily_user"] = [   # ov=score, sy=benchmark (th/mv absents => lus comme 0 côté JS)
        {"k": f"{r['username']}|{r['customer_id']}", "d": str(r["activity_date"]),
         "ov": r["n_score"], "sy": r["n_benchmark"]}
        for r in du
    ]
    SAL = ["sal_place", "sal_zone", "sal_sector", "sal_subtype", "sal_region",
           "sal_department", "sal_country", "sal_type", "sal_brand"]
    di = q(cur, f"SELECT * FROM {DB}.DIM_EREP_USER")

    def sal_compact(r):
        pairs = [[i, r[c]] for i, c in enumerate(SAL) if r[c] is not None]
        return pairs or None   # None = accès multi-strates

    out["user_dim"] = {
        f"{r['username']}|{r['customer_id']}": {
            "cn": r["customer_name"], "role": r["role"],
            "np": r["n_admin_places"], "cgs": bool(r["can_google_score"]), "be": bool(r["erep_bench_enabled"]),
            "s": sal_compact(r),
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
        WHERE EXISTS (SELECT 1 FROM {DB}.MART_EREP_DAILY_USER d
                      WHERE d.USERNAME = uu.USERNAME AND d.CUSTOMER_ID = uu.CUSTOMER_ID)""")
    umap = {}
    for r in uu:
        umap.setdefault(f"{r['username']}|{r['customer_id']}", []).append(r["level"] + SEP + r["unit_name"])
    out["user_units"] = umap
    out["perimeters"] = q(cur, f"SELECT * FROM {DB}.MART_EREP_PERIMETER_30D")
    # adoption a la maille etablissement (2026-09-23) : etablissements dont un
    # utilisateur LOCAL a ete actif, sur les etablissements ayant un tel utilisateur.
    # Index periode identique aux connectes : 0=30j, 1=mois prec., 2=trimestre, 3=annee.
    out["place_adoption"] = {
        str(r["customer_id"]): [r["places_local"], r["erep_30d"], r["erep_prevmonth"],
                                r["erep_quarter"], r["erep_year"]]
        for r in q(cur, f"SELECT * FROM {DB}.MART_PLACE_ADOPTION_CUSTOMER")
    }
    out["place_adoption_unit"] = [
        [r["customer_id"], r["level"] + SEP + r["unit_name"], r["places_local"],
         r["erep_30d"], r["erep_prevmonth"], r["erep_quarter"], r["erep_year"]]
        for r in q(cur, f"SELECT * FROM {DB}.MART_PLACE_ADOPTION_UNIT")
    ]
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

    # value driver "Acquisition" — note Google / avis / réponse (périmètre = places)
    SAL_IDX_COLS = ["u_place", "u_zone", "u_sector", "u_subtype", "u_region",
                    "u_department", "u_country", "u_type", "u_brand"]
    snap = q(cur, f"SELECT * FROM {DB}.MART_EREP_GOOGLE_PLACE_SNAPSHOT")
    out["google_place_snapshot"] = [
        {"p": r["place_id"], "c": r["customer_id"], "sc": r["score"], "rv": r["reviews"],
         "sly": r["score_ly"], "u": [r[c] for c in SAL_IDX_COLS]}
        for r in snap
    ]
    cday = q(cur, f"SELECT * FROM {DB}.FCT_EREP_GOOGLE_REVIEW_CUSTOMER_DAY")
    out["google_customer_day"] = [
        {"k": r["customer_id"], "d": str(r["activity_date"]),
         "n": r["n_reviews"], "r": r["n_replied"], "s": r["sum_reply_days"]}
        for r in cday
    ]
    out["google_perimeter_30d"] = q(cur, f"SELECT * FROM {DB}.MART_EREP_GOOGLE_PERIMETER_30D")

    p = ROOT / "dashboard" / "erep.json"
    p.write_text(json.dumps(out, default=str))
    conn.close()
    print(f"customers {len(out['customers'])} | users30d {len(out['users30d'])} | daily {len(out['daily'])}"
          f" | daily_user {len(out['daily_user'])} | user_dim {len(out['user_dim'])} | span {out.get('data_min')}..{out.get('data_max')}")
    tot = sum(c["active_erep_users"] for c in out["customers"])
    print(f"actifs E-rép (somme customers 30j) = {tot}  -> {p} ({p.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
