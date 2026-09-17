#!/usr/bin/env python3
"""Extrait MART_PORTFOLIO_30D + tendance quotidienne + totaux -> dashboard/data.json"""
import json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env

ROOT = Path(__file__).resolve().parent.parent
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
    return [dict(zip(cols, r)) for r in cur.fetchall()]


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

    portfolio = q(cur, f"SELECT * FROM {DB}.MART_PORTFOLIO_30D ORDER BY created_users DESC")
    totals = q(cur, f"""
        SELECT SUM(created_users) created_users, SUM(connected_users) connected_users,
               SUM(active_inbox) active_inbox, SUM(active_ereput) active_ereput,
               SUM(active_insight) active_insight, SUM(inbox_replies) inbox_replies,
               SUM(inbox_replies_ai) inbox_replies_ai, COUNT(*) customers
        FROM {DB}.MART_PORTFOLIO_30D""")[0]
    # la courbe vient de MART_PORTFOLIO_TREND_90D (sql/build_portfolio.sql) : elle est
    # construite à partir des faits des 3 modules, donc alignée sur les définitions
    # "actif" de leurs onglets respectifs (avant 2026-09-17 elle était recalculée ici
    # sur des drapeaux du fait global qui avaient divergé — cf. audit de cohérence).
    trend = q(cur, f"""
        SELECT ACTIVITY_DATE AS d, CONNECTED AS connected, INBOX AS inbox,
               EREPUT AS ereput, INSIGHT AS insight
        FROM {DB}.MART_PORTFOLIO_TREND_90D ORDER BY 1""")

    out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M"),
        "window_days": 30,
        "totals": totals,
        "portfolio": portfolio,
        "trend": trend,
    }
    (ROOT / "dashboard").mkdir(exist_ok=True)
    p = ROOT / "dashboard" / "data.json"
    p.write_text(json.dumps(out, default=str, indent=1))
    conn.close()

    t = totals
    print(f"portfolio: {len(portfolio)} clients | trend: {len(trend)} jours")
    print(f"TOTAUX 30j — créés {t['created_users']:,} | connectés {t['connected_users']:,} "
          f"| inbox {t['active_inbox']:,} | e-rép {t['active_ereput']:,} | insight {t['active_insight']:,}")
    print(f"réponses inbox {t['inbox_replies']:,} (IA {t['inbox_replies_ai']:,})")
    print(f"-> {p}")


if __name__ == "__main__":
    main()
