# QA final — SA-16 PostgreSQL / SQLAlchemy

**Date des preuves runtime :** 22 novembre 2026
**Projet / branche :** SmartCampusGRP1 / `yasmin`
**Périmètre :** critères de configuration, accès et vérification de PostgreSQL prévus pour SA-16. Cette mise à jour modifie uniquement ce rapport.

## Verdict final

# DONE — objectif SA-16 atteint

La répartition Sprint 1 attribue à SA-16 la mise en place/configuration de PostgreSQL, la configuration de l’accès et la vérification d’une connexion réussie. Elle attend une base accessible avec des paramètres de connexion testés. Aucun export Jira plus détaillé ni autre liste officielle de critères SA-16 n’a été trouvé dans le checkout; le verdict est donc fondé sur les objectifs/livrables SA-16 de la répartition Sprint 1.

Les preuves runtime WSL communiquées pour le 22 novembre 2026 satisfont ces critères : les deux services sont healthy, PostgreSQL 16.16 répond, la requête SQL indique la base et l’utilisateur attendus, le port local est publié sur `127.0.0.1:55432`, et `/health/db` renvoie HTTP 200. L’indisponibilité de Docker et du port localhost dans l’environnement d’audit indépendant est une différence d’environnement; elle ne contredit pas les résultats obtenus dans WSL.

## Critères SA-16 et preuves

| Statut | Critère SA-16 | Preuve / fichier |
|---|---|---|
| PASS | Configurer PostgreSQL pour SmartCampus | `backend/docker-compose.yml` configure `postgres:16-alpine`, les variables de base `smartcampus` et l’utilisateur `smartcampus`. Preuve runtime WSL communiquée : version effective **PostgreSQL 16.16** et conteneur `backend-db-1` healthy. |
| PASS | Configurer l’accès depuis le poste sur un port dédié, en préservant Odoo | `backend/docker-compose.yml` publie `127.0.0.1:55432:5432`; `.env.example` et `app/core/config.py` ciblent le port local `55432` et rejettent une URL locale sur `5432`. Preuve runtime WSL communiquée : PostgreSQL publié sur `127.0.0.1:55432`. Odoo/5432 n’a pas été ciblé dans cet audit. |
| PASS | Configurer l’accès backend → PostgreSQL dans Docker | Compose utilise le réseau `smartcampus`; l’URL du service backend vise `db:5432` sur le réseau interne Docker. `depends_on` attend le healthcheck du service `db`. Preuve runtime WSL communiquée : `backend-backend-1` et `backend-db-1` healthy. |
| PASS | Définir un stockage persistant et le contrôle de santé DB | Compose déclare `postgres_data:/var/lib/postgresql/data` et un healthcheck `pg_isready` pour l’utilisateur/base configurés. La preuve WSL indique que le conteneur DB est healthy. Aucune opération sur le volume n’a été effectuée pendant cet audit. |
| PASS | Configurer SQLAlchemy/psycopg | `backend/app/db/database.py` crée le moteur SQLAlchemy avec `pool_pre_ping=True`, un `SessionLocal` psycopg et `get_db()`. `requirements.txt` déclare SQLAlchemy et `psycopg[binary]`. L’endpoint DB utilise ce moteur. |
| PASS | Vérifier une vraie connexion PostgreSQL | Preuve runtime WSL communiquée : la requête réelle `SELECT current_database(), current_user, version()` réussit avec `smartcampus`, `smartcampus` et PostgreSQL 16.16. Preuve API WSL : `curl -i http://localhost:8000/health/db` retourne **HTTP 200**. Cette preuve WSL n’a pas pu être rejouée dans l’environnement d’audit indépendant, où Docker, le port 55432 et le port 8000 sont inaccessibles. |
| PASS | Protéger les secrets locaux | `backend/.gitignore` ignore `.env`; `git check-ignore` le confirme et `git ls-files` ne trouve pas `backend/.env` parmi les fichiers suivis. `.env.example` reste le modèle versionné. Les valeurs réelles du fichier local n’ont pas été affichées. |
| PASS | Vérifier le comportement applicatif d’accès DB | Suite pytest fraîche : `test_database_health_returns_200_when_database_responds` et les cas d’échec passent. Ces cas automatisés sont simulés; la preuve d’intégration réelle distincte est le test WSL HTTP 200 et la requête SQL fournis ci-dessus. |

## Tests automatisés exécutés dans l’environnement d’audit

- `python -m pip check` : **No broken requirements found**.
- `python -m pytest -v -o faulthandler_timeout=10` : **34 passed, 0 failed, 1 avertissement Starlette/AnyIO, en 5,01 s**.
- Les tests de santé DB de pytest remplacent l’engine/connexion par des mocks. Ils valident le comportement en isolation; ils ne sont pas présentés comme des tests d’intégration.
- L’intégration runtime WSL est établie séparément par les preuves communiquées : query PostgreSQL réelle + `/health/db` HTTP 200 + deux conteneurs healthy.

## Sessions, transactions, modèles et migrations — hors critères bloquants SA-16

`get_db()` crée la session et la ferme dans `finally`; `test_get_db_closes_session_when_dependency_finishes` réussit. Il n’y a pas de politique commune explicite de commit/rollback pour les futurs endpoints d’écriture. Ce travail relève de la conception des opérations métier et devra être fixé avant leur intégration; il ne remet pas en cause le critère SA-16 de configuration et de connexion.

`Base` est disponible, mais aucun modèle métier n’est enregistré. `backend/migrations/0000_enable_extensions.sql` est une migration technique d’extensions (`pgcrypto`, `vector`) uniquement; elle n’a pas été exécutée pendant cet audit. Les migrations métier SA-12, SA-13, SA-14 et SA-17 ne sont ni créées ni lancées ici. Leur ordre et leurs références doivent suivre les schémas communs validés. Ces éléments restent à coordonner pour l’intégration métier, mais ne sont pas des critères d’acceptation SA-16 indiqués dans la répartition Sprint 1.

Manar peut donc commencer SA-17 en utilisant le socle SQLAlchemy (`app/db/database.py`, `app/core/config.py`, `requirements.txt`, `.env.example`) et le PostgreSQL WSL disponible. Elle doit définir ses propres modèles/migration SA-17 en respectant le mapping convenu, sans supposer que les tables métier des autres tâches existent déjà.

## Portée Git et fichiers SA-16

Dans l’état Git observé, la modification applicative directement liée à l’accès hôte SA-16 est le changement de `backend/docker-compose.yml` ajoutant `127.0.0.1:55432:5432` (également utile à SA-9). Les fichiers d’infrastructure concernés sont :

- `backend/docker-compose.yml` — PostgreSQL 16, port dédié, volume, healthcheck, réseau et URL interne;
- `backend/.env.example` et `backend/app/core/config.py` — URL/variables et protection du port local 5432;
- `backend/app/db/database.py` — moteur, session SQLAlchemy et dépendance de session;
- `backend/app/api/routes/health.py` — sonde DB via `SELECT 1`;
- `backend/tests/test_config.py` et `backend/tests/test_database.py` — tests de configuration et de fermeture de session;
- `backend/scripts/start_smartcampus_postgres.ps1` — démarrage local de l’instance dédiée, distinct de Docker;
- `backend/migrations/0000_enable_extensions.sql` — prérequis techniques uniquement, pas une migration de schéma SA-16.

Le diff Git comporte aussi des changements de SA-7/SA-22 et des rapports/documents d’autres tâches. Ils n’ont pas été modifiés dans cette mise à jour. Les autres changements ouverts sont exclus du commit SA-16; cette publication ne modifie aucun fichier de coéquipière.

## Actions restantes

Aucune action restante n’empêche de déclarer l’objectif SA-16 de la répartition Sprint 1 terminé. Restent à coordonner séparément : politique transactionnelle des endpoints d’écriture, modèles/migrations métier SA-12/13/14/17 et tests d’intégration de ces schémas lorsqu’ils seront disponibles.

**Recommandation : tu peux annoncer à l’équipe que SA-16 est terminée**, en joignant les preuves WSL du 22 novembre 2026. Le verdict DONE porte sur la configuration PostgreSQL/SQLAlchemy et la connexion demandées par SA-16; il ne signifie pas que les migrations métier ou les transactions des futures routes sont achevées.
