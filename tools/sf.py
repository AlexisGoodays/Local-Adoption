#!/usr/bin/env python3
"""Petit helper pour requêter Snowflake en auth key-pair.

Config : variables d'environnement, ou un fichier `.snowflake.env` à la racine
du projet (format KEY=VALUE, une par ligne). La clé privée n'est JAMAIS lue
ici en clair : on ne manipule que son chemin (SNOWFLAKE_PRIVATE_KEY_PATH).

Usage :
    python3 tools/sf.py "SELECT CURRENT_VERSION()"
    python3 tools/sf.py -f sql/exploration.sql
    python3 tools/sf.py -f sql/mart_active_users.sql --csv data/active_users.csv
    echo "SHOW TABLES" | python3 tools/sf.py
"""
import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".snowflake.env"


def load_env():
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def get_private_key():
    key_path = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH")
    if not key_path:
        sys.exit("SNOWFLAKE_PRIVATE_KEY_PATH manquant (chemin vers la clé privée .p8).")
    key_path = os.path.expanduser(key_path)
    if not os.path.exists(key_path):
        sys.exit(f"Clé privée introuvable : {key_path}")

    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    passphrase = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
    with open(key_path, "rb") as fh:
        p_key = serialization.load_pem_private_key(
            fh.read(),
            password=passphrase.encode() if passphrase else None,
            backend=default_backend(),
        )
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def connect():
    import snowflake.connector

    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        sys.exit("Variables manquantes : " + ", ".join(missing))

    # Auth : externalbrowser (SSO) par défaut ; key-pair si une clé est fournie.
    authenticator = os.environ.get("SNOWFLAKE_AUTHENTICATOR", "").strip().lower()
    if not authenticator:
        authenticator = "snowflake_jwt" if os.environ.get("SNOWFLAKE_PRIVATE_KEY_PATH") else "externalbrowser"

    kwargs = dict(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        role=os.environ.get("SNOWFLAKE_ROLE"),
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE"),
        database=os.environ.get("SNOWFLAKE_DATABASE"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA"),
        client_session_keep_alive=False,
    )

    if authenticator == "externalbrowser":
        kwargs["authenticator"] = "externalbrowser"
        # cache le token SSO (Keychain macOS) pour éviter de ré-authentifier à chaque requête
        kwargs["client_store_temporary_credential"] = True
    elif authenticator == "snowflake_jwt":
        kwargs["private_key"] = get_private_key()
    else:
        kwargs["authenticator"] = authenticator

    return snowflake.connector.connect(**kwargs)


def main():
    parser = argparse.ArgumentParser(description="Requête Snowflake (auth key-pair).")
    parser.add_argument("query", nargs="?", help="Requête SQL inline.")
    parser.add_argument("-f", "--file", help="Fichier .sql à exécuter (dernière requête retournée).")
    parser.add_argument("--csv", help="Écrire le résultat dans ce fichier CSV.")
    parser.add_argument("--json", help="Écrire le résultat dans ce fichier JSON.")
    parser.add_argument("--max-rows", type=int, default=50, help="Lignes affichées en console (défaut 50).")
    args = parser.parse_args()

    load_env()

    if args.file:
        sql_text = Path(args.file).read_text()
    elif args.query:
        sql_text = args.query
    elif not sys.stdin.isatty():
        sql_text = sys.stdin.read()
    else:
        sys.exit("Aucune requête fournie.")

    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    if not statements:
        sys.exit("Aucune requête exécutable.")

    conn = connect()
    try:
        cur = conn.cursor()
        for stmt in statements:
            cur.execute(stmt)
        cols = [c[0] for c in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
    finally:
        conn.close()

    if args.csv:
        import csv
        with open(args.csv, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            w.writerows(rows)
        print(f"{len(rows)} lignes -> {args.csv}")

    if args.json:
        import json
        payload = [dict(zip(cols, r)) for r in rows]
        Path(args.json).write_text(json.dumps(payload, default=str, indent=2))
        print(f"{len(rows)} lignes -> {args.json}")

    if not args.csv and not args.json:
        print("\t".join(cols))
        for r in rows[: args.max_rows]:
            print("\t".join("" if v is None else str(v) for v in r))
        if len(rows) > args.max_rows:
            print(f"... ({len(rows)} lignes au total, {args.max_rows} affichées)")


if __name__ == "__main__":
    main()
