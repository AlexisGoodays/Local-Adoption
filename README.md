# Adoption des utilisateurs locaux

Dashboard d'adoption produit destiné aux Adoption Managers : il mesure, compte client
par compte client, combien d'utilisateurs locaux (les équipes en magasin / point de
vente) se connectent au back-office et utilisent réellement chaque module.

Le livrable est une page HTML autonome, alimentée par une couche de tables
construites dans Snowflake. Aucune infrastructure à déployer : on rafraîchit les
données avec quelques commandes, on ouvre la page dans un navigateur.

---

## Ce que le dashboard affiche

Quatre onglets :

| Onglet | Contenu |
|---|---|
| **Vue Portefeuille** | Les 139 comptes clients sur une ligne chacun : créés, connectés, actifs par module, réponses Inbox. C'est l'écran d'entrée. |
| **Module Insight** | Adoption détaillée d'Insight (comptes éligibles uniquement), par utilisateur ou par niveau hiérarchique. |
| **E-réputation** | Idem pour la note Google et le benchmark concurrentiel. |
| **Module Inbox** | Idem pour l'Inbox, plus le value driver « Culture Client ». |

Sur chaque onglet module : filtre par compte, par période, par niveau d'agrégation
(région, zone, enseigne…) et par périmètre, un classement d'adoption trié, les
meilleurs et les moins bons adopteurs, et une courbe d'évolution quotidienne.

### Le funnel

```
Créés  ──►  Connectés  ──►  Actifs <module>
```

- **Créés** — comptes utilisateurs actifs et valides sur le back-office.
- **Connectés** — a généré au moins un événement de tracking sur la période,
  tous modules confondus. Inclut aussi le fait d'avoir envoyé une réponse Inbox :
  certaines réponses (surtout assistées par IA) n'émettent aucun événement de
  consultation, et sans ce signal on comptait des utilisateurs « actifs » sans
  qu'ils soient « connectés ».
- **Actifs** — dépend du module :

| Module | Définition d'« actif » |
|---|---|
| Inbox | a envoyé **au moins une réponse** (l'ouverture de la page seule compte comme « Connecté Inbox », pas comme actif) |
| E-réputation | a consulté la note Google **ou** le benchmark concurrentiel |
| Insight | a utilisé l'une des 3 features (Quick Overview, carte de synthèse, page thématique) ou vu une page monitorée |

> **Règle structurante : un même libellé = un même chiffre sur tous les écrans.**
> Le Portefeuille ne recalcule jamais sa propre notion d'« actif » : il relit les
> marts des modules. C'est pour cela que `sql/build_portfolio.sql` s'exécute en
> dernier. Si vous ajoutez un module, suivez le même principe — une définition
> vit à un seul endroit.

---

## Mise en route

### Prérequis

- Python 3.9 ou plus
- Un accès Snowflake en SSO, avec un rôle qui peut **lire** `MARTING_BUSINESS.ANALYTICS`
  et **écrire** dans `REPORTING.ADOPTION`
- Un navigateur

### Installation

```bash
git clone https://github.com/AlexisGoodays/Local-Adoption.git
cd Local-Adoption
pip install -r requirements.txt
cp .snowflake.env.example .snowflake.env
```

Puis remplissez `.snowflake.env` (les commentaires du fichier indiquent où trouver
chaque valeur). Rien de secret n'y est stocké : l'authentification passe par une
fenêtre SSO qui s'ouvre au premier appel. Ce fichier est volontairement ignoré par
git — ne le committez pas.

Vérifiez que la connexion fonctionne :

```bash
python3 tools/sf.py "SELECT CURRENT_USER(), CURRENT_ROLE()"
```

---

## Rafraîchir les données

### ⚠️ L'ordre compte, et il n'est pas négociable

Chaque table « 30 jours glissants » ancre sa fenêtre sur la date à laquelle **elle**
est construite. Reconstruire un seul module des jours après les autres crée un
décalage entre numérateurs et dénominateurs : c'est comme ça qu'un taux d'adoption
Inbox a pu afficher 107 % en cours de projet. **Rejouez toujours la séquence
entière, le même jour.**

```bash
# 1. Couche SQL — dans cet ordre exact
python3 tools/build.py sql/build_adoption.sql          # dimensions + fait de base (400 j)
python3 tools/build.py sql/build_insight.sql
python3 tools/build.py sql/build_erep.sql
python3 tools/build.py sql/build_inbox.sql
python3 tools/build.py sql/build_hierarchy.sql         # rattachement hiérarchique + marts par unité
python3 tools/build.py sql/build_erep_acquisition.sql
python3 tools/build.py sql/build_portfolio.sql         # EN DERNIER : relit les marts des modules

# 2. Extraction Snowflake -> JSON
python3 tools/extract_insight.py
python3 tools/extract_erep.py
python3 tools/extract_inbox.py
python3 tools/extract_portfolio.py

# 3. Génération du dashboard
python3 tools/build_dashboard.py
```

Comptez quelques minutes au total. Une fenêtre SSO peut s'ouvrir à chaque script.

### Visualiser

Les fichiers de données pèsent plusieurs dizaines de Mo et sont chargés à la
demande : il faut donc un vrai serveur HTTP, l'ouverture directe du fichier ne
fonctionne pas.

```bash
cd dashboard
python3 -m http.server 8777
```

Puis ouvrez **http://localhost:8777/index.html** (rechargement forcé après un
rebuild, le navigateur garde les anciens fichiers en cache).

Le dashboard a un mode clair / sombre (bouton en haut à droite), clair par défaut.

---

## Organisation du dépôt

```
sql/      les tables Snowflake, une par domaine — à lire dans l'ordre du pipeline
tools/    les scripts Python
dashboard/  sortie générée (ignorée par git)
data/     exports d'exploration (ignorés par git)
```

### Les scripts

| Script | Rôle |
|---|---|
| `tools/sf.py` | requête ad hoc : `python3 tools/sf.py "SELECT ..."`, ou `-f fichier.sql`, `--csv`, `--json` |
| `tools/build.py` | exécute un `.sql` instruction par instruction et affiche le nombre de lignes produites |
| `tools/extract_*.py` | exportent les marts vers `dashboard/*.json` |
| `tools/build_dashboard.py` | génère `index.html` + les bundles JS. **Tout le front vit dans ce fichier** |
| `tools/explore.py`, `profile1.py`, `diag.py`, `v1check.py` | exploration et contrôles ponctuels |

Pour modifier le dashboard (un libellé, un KPI, une colonne), éditez
`tools/build_dashboard.py` puis relancez-le — ne touchez pas à `dashboard/index.html`,
qui est écrasé à chaque build.

> `tools/build.py` est préférable à `tools/sf.py -f` pour exécuter un fichier :
> `sf.py` découpe naïvement sur les `;`, y compris ceux présents dans les
> commentaires, ce qui produit des erreurs difficiles à lire.

---

## Lire les chiffres correctement

Trois subtilités à connaître avant de conclure quoi que ce soit d'un écran.

**Le rattachement hiérarchique.** Un utilisateur compte dans une unité s'il
l'administre directement **ou** si l'un de ses magasins administrés en dépend. Les
profils administrant plus de 60 magasins (siège, national) sont exclus des
classements par niveau, sinon ils écrasent tout.

**Ne sommez pas les lignes d'un classement.** Un utilisateur peut appartenir à
plusieurs unités d'un même niveau (il administre deux régions) : il est alors
compté dans chacune. Additionner toutes les lignes dépasse le total du compte —
de quelques pourcents en général, jusqu'à +50 % sur les comptes très maillés.
Comparez les unités entre elles, ne les additionnez pas.

**Les fenêtres temporelles.** Le sélecteur de période recalcule numérateur *et*
dénominateur sur Insight et E-réputation. Sur une période personnalisée, le
dénominateur n'est pas précalculable : le ratio est masqué plutôt qu'approximatif.
Le bloc Adoption de l'Inbox reste sur une fenêtre fixe de 30 jours (son fait
détaillé fait plus de 4 millions de lignes, non embarquable côté navigateur) —
c'est signalé sur le bloc.

### Vérifier la cohérence

Le projet tient un jeu de contrôles d'invariants (actifs ≤ connectés ≤ créés à
tous les niveaux, ratios stockés cohérents avec leurs composants, « connectés »
identique entre les marts, concordance Portefeuille ↔ onglets). Après un
changement de définition, rejouez-les : tout doit rester à zéro violation.

---

## Limites connues

- **Fenêtre de 400 jours** sur le fait de base, ce qui borne l'historique disponible.
- **Comptes vs personnes** : certains comptes sont des boîtes génériques partagées
  par un magasin, pas des individus. Les volumes « par utilisateur » sont à lire
  avec cette réserve.
- **Consultations Inbox** : il s'agit d'un décompte d'événements bruts, pas
  d'actions distinctes — un rechargement de page compte. Le détail par type
  d'activité est accessible en cliquant sur la valeur.
- **Périmètre fonctionnel** : les modules Statistiques et Enquêtes ne sont pas couverts.
