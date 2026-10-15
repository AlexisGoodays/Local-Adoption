#!/usr/bin/env python3
"""Exécute plusieurs requêtes nommées en UNE connexion (un seul login SSO).

Fichier SQL : blocs séparés par une ligne `-- name: <nom>`.
Usage : python3 tools/multi.py fichier.sql [--out dossier] [--echo 20]
"""
import argparse, csv, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sf import load_env, connect  # noqa: E402

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file"); ap.add_argument("--out", default=None); ap.add_argument("--echo", type=int, default=20)
    a = ap.parse_args()
    text = Path(a.file).read_text()
    blocks = re.split(r"^--\s*name:\s*(\S+)\s*$", text, flags=re.M)
    queries = [(blocks[i], blocks[i + 1].strip().rstrip(";")) for i in range(1, len(blocks), 2)]
    out = Path(a.out) if a.out else None
    if out: out.mkdir(parents=True, exist_ok=True)
    load_env(); conn = connect(); cur = conn.cursor()
    for name, sql in queries:
        print(f"\n=== {name} ===")
        for attempt in range(3):
            try:
                cur.execute(sql); break
            except Exception as e:  # noqa: BLE001
                if "No active warehouse" in str(e) and attempt < 2:
                    time.sleep(3); continue
                print(f"  ! ERREUR: {e}"); cur = conn.cursor(); break
        else:
            continue
        if not cur.description: continue
        cols = [c[0] for c in cur.description]; rows = cur.fetchall()
        if out:
            with open(out / f"{name}.csv", "w", newline="") as fh:
                w = csv.writer(fh); w.writerow(cols); w.writerows(rows)
        print(f"  {len(rows)} lignes | " + " | ".join(cols))
        for r in rows[: a.echo]:
            print("  " + " | ".join("" if v is None else str(v)[:120] for v in r))
        if len(rows) > a.echo: print(f"  ... (+{len(rows) - a.echo})")
    conn.close()

if __name__ == "__main__":
    main()
