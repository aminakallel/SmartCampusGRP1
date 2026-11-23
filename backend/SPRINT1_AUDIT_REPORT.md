# Audit technique Sprint 1 — SmartCampus AI

Date de l'audit : 20 novembre 2026
Périmètre : SA-7, SA-9, SA-16, SA-18 et SA-22
Mode : inspection et vérifications non destructives. Aucun code métier, donnée existante ou cluster Odoo n'a été modifié pendant cet audit. Seul ce rapport a été créé.

## 1. Résumé général

Le dossier projet contient un backend FastAPI autonome. Le code expose deux routes : `GET /health` et `GET /health/db`. Les tests couvrent les contrats présents et passent. Les modèles et routes métier d'autres membres ne sont pas présents, conformément aux limites de responsabilité.

L'état runtime actuel n'est pas « tout fonctionne » : au moment de l'audit, aucun serveur API n'écoute sur le port 8000 et le cluster SmartCampus isolé n'écoute pas sur le port 55432. Les preuves d'une exécution antérieure montrent toutefois une API et une base qui avaient répondu correctement, et un seed exécuté deux fois avec 5 lignes. Ces preuves antérieures sont distinguées des contrôles courants ci-dessous.

## 2. Structure constatée

Le workspace contient essentiellement `backend/`, avec :

```text
backend/
├── app/
│   ├── api/routes/health.py
│   ├── core/config.py
│   ├── db/database.py
│   └── main.py
├── scripts/seed_demo.py
├── seed_data/demo_records.json
├── tests/test_config.py
├── tests/test_health.py
├── tests/test_seed_demo.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
└── QA_REPORT.md
```

L'environnement local `.venv`, le `.env` et le répertoire de données PostgreSQL `.smartcampus_pgdata` existent aussi. Ils sont ignorés par `.gitignore`. Le `.env` n'a pas été affiché ni son mot de passe divulgué.

## 3. Commandes et résultats exécutés pendant cet audit

| Vérification | Résultat constaté |
|---|---|
| `python --version` | Python 3.12.3 |
| `.venv\Scripts\python.exe --version` | Python 3.12.3 |
| `.venv\Scripts\python.exe -m pip check` | `No broken requirements found` |
| `.venv\Scripts\python.exe -m pytest -v` | **10 passed**, 0 failed ; un avertissement de dépréciation Starlette/AnyIO |
| Parse YAML de `docker-compose.yml` avec PyYAML | Réussi ; services `backend` et `db` détectés |
| `pg_ctl -D .smartcampus_pgdata status` | Aucun serveur PostgreSQL en cours |
| Test de port local 55432 | Fermé au moment de l'audit |
| Test HTTP sur `127.0.0.1:8000` | Connexion refusée pour toutes les requêtes testées : l'API n'était pas démarrée |
| Recherche de la commande `docker` | Docker CLI indisponible |

Les dix tests passés couvrent : paramètres d'environnement, santé API, 404, Swagger, 405, gestion 500 dans une application de test isolée, réponses `/health/db` simulées 200/503, validation des fixtures fictives et génération d'upserts idempotents.

## 4. SA-7 — Backend FastAPI

**Fichiers :** `app/main.py`, `app/core/config.py`, `app/api/routes/health.py`, `app/db/database.py`, `requirements.txt`, `tests/test_config.py`, `tests/test_health.py`.

- FastAPI, Uvicorn, SQLAlchemy, psycopg, Pydantic Settings, python-dotenv, pytest et HTTPX sont déclarés dans `requirements.txt`.
- La configuration Pydantic Settings charge `.env` si le processus est lancé depuis `backend`. Le réglage courant, affiché sans secret, cible `postgresql+psycopg` sur `127.0.0.1:55432`, base `smartcampus`, utilisateur `smartcampus`.
- OpenAPI est généré ; les chemins listés par l'application sont `/health` et `/health/db`. Swagger est configuré sur `/docs`.
- Le handler générique renvoie un message 500 assaini. Le test 500 utilise une application de test isolée, pas une route artificielle ajoutée au produit.
- Les tests confirment 404 pour une route inconnue et 405 pour une méthode non autorisée.
- **Exécution antérieure documentée :** une instance sur le port 8766 avait renvoyé 200 pour `/health`, `/health/db` et `/docs`. Elle a été arrêtée après cette vérification.
- **État courant :** le test HTTP sur le port 8000 a reçu `WinError 10061` (connexion refusée). Aucun serveur n'a été lancé pendant l'audit, conformément à la consigne de ne pas démarrer d'instances supplémentaires.

### Problème de configuration à corriger

`app/core/config.py` a une URL de base par défaut vers `localhost:5432` avec des identifiants codés dans le source. `.env.example` propose aussi le port 5432. Or ce port est réservé au PostgreSQL Odoo sur cette machine. Le `.env` courant évite cette cible en utilisant 55432, mais si ce fichier manque ou n'est pas chargé, l'application pourrait tenter de joindre Odoo. Il faut remplacer ce fallback par une configuration obligatoire ou explicitement sûre avant de distribuer le projet. Ce code n'a pas été modifié pendant l'audit.

## 5. SA-9 — Docker

**Fichiers :** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`.

Constats statiques :

- Le Dockerfile installe `requirements.txt`, copie l'application et démarre Uvicorn sur `0.0.0.0:8000`.
- Compose définit `backend` et `db`, utilise `postgres:16-alpine`, un volume nommé `postgres_data`, un healthcheck par service et attend la santé de `db` avant le backend.
- Seul le port backend `8000:8000` est publié ; PostgreSQL est accessible au backend par le réseau Compose sous le nom `db`, sans port DB publié sur l'hôte.
- `.dockerignore` exclut `.env`, `.venv`, les caches et les fichiers bytecode.
- Le parse YAML a réussi.
- Docker n'étant pas installé/disponible, `docker --version`, `docker compose config`, le build, le démarrage des conteneurs et la communication réseau n'ont pas pu être testés.

**Point de durcissement :** le Dockerfile ne définit pas d'utilisateur non privilégié ; le conteneur s'exécuterait en root par défaut. À corriger avant un usage hors développement local.

## 6. SA-16 — PostgreSQL

**Fichiers :** `app/db/database.py`, `app/core/config.py`, `.env`, `.env.example`, `docker-compose.yml`.

- SQLAlchemy crée le moteur avec `pool_pre_ping=True`; `Base`, `SessionLocal` et le générateur de session `get_db` sont présents.
- Le driver déclaré est `psycopg[binary]` et le schéma d'URL est `postgresql+psycopg://`.
- La base configurée dans le `.env` est la base dédiée `smartcampus` sur `127.0.0.1:55432`, distincte de l'instance Odoo sur 5432.
- **Preuve antérieure :** l'endpoint `/health/db` a répondu 200 sur l'API lancée avec ce `.env` et PostgreSQL 12.4 isolé.
- **État courant :** `pg_ctl` indique qu'aucun serveur n'est démarré et le port 55432 est fermé. La connexion réelle n'a donc pas été répétée pendant cette session. L'instance Odoo n'a pas été touchée.
- La configuration attendue par Compose est PostgreSQL 16 ; seule la connexion à l'instance isolée avec les binaires locaux PostgreSQL 12.4 a déjà été éprouvée. La compatibilité runtime avec PostgreSQL 16 Compose n'est pas vérifiée.

## 7. SA-18 — Seed data

**Fichiers :** `seed_data/demo_records.json`, `scripts/seed_demo.py`, `tests/test_seed_demo.py`.

- Le JSON comporte cinq exemples fictifs/provisoires : deux établissements, deux programmes et un compte de démonstration. Les conditions d'admission, niveaux et durées sont à valider, pas présentés comme officiels.
- Le script crée uniquement le namespace de staging `smartcampus_demo.seed_records` et utilise `ON CONFLICT (id) DO UPDATE`. Il ne déclare pas les modèles partagés du catalogue ou des profils.
- **Preuve antérieure :** le seed a été lancé deux fois ; la requête de comptage a montré 5 lignes (2 establishments, 2 programs, 1 user) après les deux exécutions.
- **Pendant cet audit :** le seed n'a pas été relancé, car il écrit dans la base et la consigne de cet audit demandait de ne pas modifier les données. Le cluster est de toute façon arrêté au moment des contrôles courants.
- Le seed reste un stockage de démonstration générique ; il n'est pas intégré aux tables métier validées par Manar/Tasnime.

## 8. SA-22 — QA et sécurité API

**Fichiers :** `tests/test_config.py`, `tests/test_health.py`, `tests/test_seed_demo.py`, `tests/README.md`, `pytest.ini`, `QA_REPORT.md`.

- Les 10 tests existants passent.
- Contrats réellement implémentés : 200, 404, 405, 503 pour DB indisponible ; 500 vérifié dans un harness isolé. Swagger/OpenAPI a été contrôlé par tests et précédemment par HTTP.
- Aucun endpoint de création n'existe : 201 et 400 ne peuvent pas être testés sans contrat métier. Aucune authentification n'existe : 401/403 ne sont pas testables et ne doivent pas être inventés. Aucun endpoint avec corps validé n'existe pour produire un test 422 utile.
- L'instance API courante étant arrêtée, les requêtes HTTP de cette session vers le port 8000 ont échoué au niveau connexion avant d'atteindre FastAPI.
- Il n'y a pas de test automatisé qui se connecte à PostgreSQL réel ; les tests DB du dépôt utilisent des mocks. L'intégration réelle est prouvée par l'exécution précédente, pas par pytest.

## 9. Tableau de statut

| Tâche | Implémentée | Testée réellement | Résultat | Travail restant |
|---|---|---|---|---|
| SA-7 | Oui | Partiel | 10 tests passent ; preuve HTTP antérieure positive, serveur arrêté au moment de l'audit | Démarrer une seule instance après configuration sûre ; supprimer le fallback qui vise 5432 |
| SA-9 | Oui, configuration | Non pour le runtime Docker | Compose YAML valide ; aucune commande Docker disponible | Installer/activer Docker puis faire config, build et up sans supprimer de volume |
| SA-16 | Partiel | Partiel | URL `.env` cible SmartCampus:55432 ; connexion réussie antérieurement, cluster arrêté actuellement | Redémarrer le cluster dédié, refaire health check ; vérifier PostgreSQL 16 Compose quand Docker disponible |
| SA-18 | Partiel | Oui, lors d'une exécution antérieure | Deux exécutions antérieures, 5 lignes après chacune ; pas de réexécution pendant cet audit | Relier les fixtures aux schémas validés par les responsables du catalogue et des profils |
| SA-22 | Partiel | Oui pour les routes présentes | 10 tests passent ; routes métier/auth absentes | Ajouter les tests 201/400/401/403/422 dès publication des contrats et réexécuter sur serveur actif |

## 10. Dépendances équipe et éléments non implémentés

- Manar : schéma utilisateur/profil et tables (SA-13/SA-17), nécessaires à l'intégration du seed utilisateur.
- Tasnime : modèle catalogue et API de gestion/authentification (SA-12/SA-20/SA-28), nécessaires aux données catalogue et aux tests d'accès.
- Amina : contrats API et règles d'accès (SA-5), nécessaires aux cas 400/401/403 et aux formats attendus.
- Roua : API de consultation (SA-21), et interfaces Backend/Frontend à tester à mesure de leur livraison.
- Les endpoints catalogue, profil, authentification, session, préinscription, rendez-vous et conversation ne sont pas implémentés dans ce backend audité. Ils ont été laissés aux membres désignés.

## 11. Corrections/actions restantes — priorité

1. **Sécurité / isolation DB :** remplacer le fallback source et le port 5432 de l'exemple local par une exigence de configuration explicite qui ne peut pas viser PostgreSQL Odoo.
2. **Runtime local :** redémarrer uniquement le cluster SmartCampus isolé `.smartcampus_pgdata` sur 55432, puis démarrer une seule instance Uvicorn depuis `backend`; vérifier `/health`, `/health/db`, `/docs` et `/openapi.json`.
3. **Docker :** quand Docker est disponible, exécuter `docker --version`, `docker compose config`, `docker compose build`, puis `docker compose up -d`; vérifier `docker compose ps`, les healthchecks, `/health/db` et le seed. Ne pas utiliser `docker compose down -v`.
4. **Schémas partagés :** obtenir les modèles validés, adapter les fixtures/seeders aux tables concernées sans créer de schéma métier en parallèle.
5. **QA intégrée :** compléter les scénarios de validation et d'autorisation dès que les API et règles SA-5/SA-28 seront disponibles. Garder les erreurs 500 et détails internes hors des réponses publiques.
6. **Durcissement du conteneur :** ajouter un utilisateur non-root avant de considérer l'image durcie.

## Addendum — réparation PostgreSQL SmartCampus (20 novembre 2026)

### Cause constatée

- Le cluster existant utilise `PG_VERSION=12` et les binaires PostgreSQL 12.4 présents dans l'installation Odoo. Son dossier est bien `.smartcampus_pgdata` ; l'instance Odoo sur le port 5432 n'a pas été utilisée.
- `postmaster.pid` contenait le PID 6212, mais Windows ne trouvait aucun processus à cet identifiant. `pg_ctl status` déclarait le cluster arrêté et le port 55432 était fermé. Le PID était donc obsolète.
- Le journal PostgreSQL indique que le serveur avait été interrompu sans arrêt propre. Au redémarrage, PostgreSQL a effectué sa récupération WAL et a fini par indiquer qu'il était prêt à accepter les connexions. Les journaux établissent l'arrêt non propre, mais n'identifient pas la cause externe qui a tué/arrêté le processus.
- Le PID n'a pas été supprimé manuellement. Le démarrage normal avec `pg_ctl` a réussi et a remplacé l'ancien PID par 7316. Aucun `initdb`, effacement, restauration manuelle ou modification du `.env` n'a été effectué.

### Corrections et vérifications après réparation

- Ajout de `scripts/start_smartcampus_postgres.ps1`. Il valide l'existence du cluster et la correspondance de version, cible uniquement `.smartcampus_pgdata`, écoute sur `127.0.0.1:55432`, ne réinitialise jamais les données et ne touche pas au service Odoo. Testé lorsque le serveur était déjà actif : il a détecté le PID 7316 et n'a pas lancé de seconde instance. Le démarrage à froid a été réalisé auparavant avec le même `pg_ctl` et les mêmes paramètres.
- `app/core/config.py` et `.env.example` ont été corrigés : leur fallback utilise maintenant le port SmartCampus 55432, au lieu de risquer de viser le port Odoo 5432. Le `.env` utilisateur est resté intact.
- Ajout d'un test de non-régression assurant que la configuration par défaut ne cible pas le port 5432.
- Connexion SQLAlchemy/psycopg réussie : URL masquée dans le terminal ; identité observée `smartcampus`, hôte `127.0.0.1`, port `55432`, version `12.4`; 5 lignes de seed présentes.
- Tests HTTP après redémarrage de l'unique API sur 8000 : `/health` 200, `/health/db` 200, `/docs` 200, `/openapi.json` 200 avec `/health` et `/health/db`; route inconnue 404 et `POST /health` 405.
- Derniers contrôles : `python -m pip check` sans dépendance cassée ; `python -m pytest -v` : **11 passed**, un avertissement Starlette/AnyIO.
- Aucun seed n'a été relancé pendant cette réparation ; le comptage a été fait en lecture seule. La preuve antérieure des deux exécutions du seed reste inchangée.

### État restant

- L'API de test est démarrée sur `127.0.0.1:8000` et le cluster SmartCampus sur `127.0.0.1:55432` au terme de la vérification.
- Docker reste indisponible ; le runtime PostgreSQL 16/Compose n'est donc pas vérifié. La preuve PostgreSQL réelle concerne le cluster local 12.4 isolé.
- Les intégrations de données dans les vrais modèles catalogue/profil et les tests d'autorisations métier attendent les contrats des membres responsables.

## Addendum — finalisation des parties autonomes (20 novembre 2026)

### État constaté avant modifications

- Le cluster SmartCampus PID 7316 et une seule instance FastAPI sur 8000 étaient actifs. Les routes `/health`, `/health/db`, `/docs` et `/openapi.json` répondaient 200. Le comptage en lecture seule montrait 5 lignes de staging.
- La base active utilisait `127.0.0.1:55432`; PostgreSQL Odoo sur 5432 n'a pas été interrogé ni modifié.
- Les 11 tests de la précédente révision passaient. Les routes métier/contrats des autres membres restaient absents.

### Changements réalisés

- **SA-7** : ajouté `CORS_ORIGINS` configurable, strictement limité à des origines HTTP(S) explicites ; CORS désactivé si vide, wildcard/paths/identifiants/ports incorrects rejetés. Les URLs de DB locales sur le port Odoo 5432 sont refusées. Les erreurs génériques et DB n'enregistrent/renvoient plus le texte des exceptions.
- **SA-9** : Dockerfile utilise maintenant `USER app`; Compose déclare un réseau bridge de projet, garde PostgreSQL sans port publié, conserve healthchecks, dépendance DB saine et volume persistant. Aucun build ni conteneur n'a été lancé, Docker CLI étant indisponible.
- **SA-16** : moteur, pool `pre_ping`, SessionLocal et get_db étaient déjà corrects ; ajout d'un test de fermeture de session. URL masquée et connexion réelle relues avec succès vers `smartcampus` sur 55432. README contient maintenant des procédures de sauvegarde et de restauration vers une base neuve uniquement ; aucune sauvegarde/restauration n'a été exécutée.
- **SA-18** : ajout de schémas Pydantic stricts pour les fixtures, champs requis, types, unicité des IDs et erreurs de lecture JSON sûres. Le seed n'a pas été exécuté pendant cette passe ; les données existantes ont été comptées en lecture seule (5).
- **SA-22** : ajout de tests configuration/.env, CORS autorisé/refusé, OpenAPI, session fermée, données invalides/IDs dupliqués et fuite de secrets. Aucun faux endpoint métier n'a été créé.

### Vérification finale

- Python système et venv : 3.12.3. `python -m pip check` : aucune dépendance cassée.
- `python -m pytest -v` : **29 passed**, 1 avertissement upstream Starlette/AnyIO, 0 échec.
- HTTP après rechargement du code : `/health` 200, `/health/db` 200, `/docs` 200, `/openapi.json` 200 ; réponse OpenAPI limitée aux deux routes réellement présentes. Contrôles de routage 404/405 et 500 assaini couverts par tests.
- Connexion SQLAlchemy/psycopg effective ; `current_database=smartcampus`, `inet_server_port=55432`, 5 lignes staging. Aucun mot de passe n'est affiché.
- Contrôles Docker statiques PASS : YAML, deux services, healthchecks, dépendance DB, volume, réseau, port DB non publié et utilisateur non-root. Docker CLI indisponible : `docker compose config/build/up` restent non vérifiés.
- Le `.env`, les données seed, le cluster SmartCampus et PostgreSQL Odoo n'ont pas été modifiés pendant cette passe.

### Fichiers créés/modifiés pendant cette passe

- Créé : `tests/test_database.py`.
- Modifiés : `app/core/config.py`, `app/main.py`, `app/api/routes/health.py`, `scripts/seed_demo.py`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`, `tests/test_config.py`, `tests/test_health.py`, `tests/test_seed_demo.py`, `tests/README.md`, `QA_REPORT.md`, ce rapport.
- Non modifiés : `requirements.txt` (déjà complet), `.env`, `seed_data/demo_records.json`, `scripts/start_smartcampus_postgres.ps1`, `.smartcampus_pgdata`, contenu de la base, volumes Docker et tout fichier de responsabilité d'un autre membre.

### À attendre

- Runtime Docker/PostgreSQL 16 lorsque Docker sera disponible.
- Origines CORS réelles à renseigner quand l'URL du frontend sera convenue.
- Mapping des données vers modèles validés par Manar/Tasnime.
- Tests 201/400/401/403/422 après livraison des contrats par Amina et des routes métier.

### Rectificatif de la dernière exécution — 20 novembre 2026

Le compte rendu ci-dessus mentionne une exécution complète de 29 tests réussis. Après l'ajout des dernières assertions de non-divulgation dans les logs, le nouveau `python -m pytest -v` s'est bloqué sur `tests/test_health.py::test_health_returns_200`; le test lancé seul s'est bloqué au même endroit. Les processus ont été interrompus. Par conséquent, **29 passed correspond à la révision antérieure** et la suite sur l'état actuel reste à revalider. `python -m pip check` a réussi sans dépendance cassée. La cause du blocage reste à diagnostiquer.

### Diagnostic pytest résolu — 20 novembre 2026

La cause était l'exécution pytest dans le sandbox qui bloque la création de sockets loopback. Une trace `faulthandler` localise l'attente dans AnyIO/asyncio Windows au démarrage de `TestClient`, avant la route; `socket.socketpair()` seul reproduit le blocage sandboxé et passe immédiatement hors sandbox. Aucun problème applicatif ou de test n'a été trouvé, donc aucun code ni test n'a été affaibli ou modifié. En lançant les tests hors sandbox : test isolé **1/1**, santé **11/11**, config **11/11**, seed **6/6**, DB **1/1**, suite complète **29 passed, 0 failed** (2.77 s; un avertissement de dépréciation Starlette/AnyIO). `pip check` est propre. Les tests utilisent des mocks pour l'accès DB/seed. Contrôle en lecture seule : port Odoo 5432/PID 8972 intact; SmartCampus PID 7316 utilise `backend/.smartcampus_pgdata` sur 55432; API PID 12768 sur 8000. Aucun de ces processus n'a été arrêté.
