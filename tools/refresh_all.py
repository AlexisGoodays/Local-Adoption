#!/usr/bin/env python3
"""Rafraîchit toute la chaîne : couche SQL, extractions, génération du dashboard.

Pourquoi ce script existe : chaque table « 30 jours glissants » ancre sa fenêtre
sur la date à laquelle ELLE est construite. Rejouer une partie seulement de la
chaîne désynchronise les fenêtres entre tables, et les ratios deviennent faux
sans que rien ne le signale. L'ordre ci-dessous est donc une dépendance, pas une
préférence.

    python3 tools/refresh_all.py              # tout rafraîchir
    python3 tools/refresh_all.py --dry-run    # afficher les étapes sans rien lancer
    python3 tools/refresh_all.py --from 5     # reprendre à l'étape 5 après un échec

Une fenêtre de connexion SSO peut s'ouvrir à la première étape.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# L'ordre compte. build_portfolio doit rester en dernier parmi les SQL : il relit
# les marts des trois modules au lieu de recalculer ses propres chiffres.
ETAPES = [
    ("SQL  · dimensions, fait de base, connectés par période", "sql/build_adoption.sql"),
    ("SQL  · module Insight", "sql/build_insight.sql"),
    ("SQL  · module E-réputation", "sql/build_erep.sql"),
    ("SQL  · module Inbox", "sql/build_inbox.sql"),
    ("SQL  · rattachement hiérarchique, marts par unité, adoption établissement", "sql/build_hierarchy.sql"),
    ("SQL  · value driver Acquisition (E-réputation)", "sql/build_erep_acquisition.sql"),
    ("SQL  · écran Portefeuille (doit rester en dernier)", "sql/build_portfolio.sql"),
    ("DATA · extraction Insight", "tools/extract_insight.py"),
    ("DATA · extraction E-réputation", "tools/extract_erep.py"),
    ("DATA · extraction Inbox", "tools/extract_inbox.py"),
    ("DATA · extraction Portefeuille", "tools/extract_portfolio.py"),
    ("HTML · génération du dashboard", "tools/build_dashboard.py"),
]


def commande(cible):
    if cible.endswith(".sql"):
        return [sys.executable, "tools/build.py", cible]
    return [sys.executable, cible]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="affiche les étapes sans les exécuter")
    ap.add_argument("--from", dest="depart", type=int, default=1, metavar="N",
                    help="reprendre à l'étape N (voir la numérotation ci-dessous)")
    args = ap.parse_args()

    total = len(ETAPES)
    if not 1 <= args.depart <= total:
        sys.exit(f"--from doit être compris entre 1 et {total}.")

    manquants = [c for _, c in ETAPES if not (ROOT / c).exists()]
    if manquants:
        sys.exit("Fichiers introuvables : " + ", ".join(manquants))

    if args.dry_run:
        print(f"{total} étapes, dans cet ordre :\n")
        for i, (libelle, cible) in enumerate(ETAPES, 1):
            marque = " " if i >= args.depart else "·"
            print(f" {marque} {i:2}. {libelle}\n        {' '.join(commande(cible))}")
        return

    if args.depart > 1:
        print(f"Reprise à l'étape {args.depart}. Attention : les étapes sautées gardent "
              f"la fenêtre de leur dernier build.\n")

    debut = time.time()
    for i, (libelle, cible) in enumerate(ETAPES, 1):
        if i < args.depart:
            continue
        print(f"\n[{i}/{total}] {libelle}", flush=True)
        t0 = time.time()
        res = subprocess.run(commande(cible), cwd=ROOT)
        if res.returncode != 0:
            print(f"\nÉchec à l'étape {i} ({cible}).")
            print(f"Corrigez, puis reprenez avec :  python3 tools/refresh_all.py --from {i}")
            print("Tant que la chaîne n'est pas allée au bout, le dashboard mélange "
                  "des fenêtres de dates différentes.")
            sys.exit(res.returncode)
        print(f"      terminé en {time.time() - t0:.0f} s", flush=True)

    print(f"\nChaîne complète terminée en {(time.time() - debut) / 60:.1f} min.")
    print("Dashboard à jour : lancez un serveur depuis dashboard/ puis ouvrez index.html.")


if __name__ == "__main__":
    main()
