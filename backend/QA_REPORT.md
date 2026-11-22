# QA report — Sprint 1 backend foundation

## Environment and dependencies

- Project virtual environment: `backend/.venv` (Python 3.12.3).
- All entries from `requirements.txt` installed; `python -m pip check` reports no broken requirements.
- Added `python-dotenv` because Pydantic Settings needs it to load `.env`.
- Created a Git-ignored `.env` for the isolated local test database. No credential is committed.

## Automated tests

Command: `python -m pytest -v` from `backend` with `.venv` active.

Result: **10 passed, 0 failed**, with one upstream Starlette/AnyIO deprecation warning.

Coverage includes environment variable settings, `/health` 200, unknown route 404, Swagger 200, unsupported method 405, sanitized generic 500, database health success/failure, provisional fixture validation and repeat-safe upsert generation.

## Live application checks

Started an API process on `127.0.0.1:8766` after configuring `.env`; a separate user process was left running on port 8000.

| Request/check | Actual result |
|---|---|
| `GET /health` on port 8766 | HTTP 200 |
| `GET /health/db` on port 8766 | HTTP 200; connection to dedicated SmartCampus database succeeded |
| `GET /docs` on port 8766 | HTTP 200 |
| Existing API process on port 8000 | It was started before `.env` was created and continued to return HTTP 503 from its old settings; restart it to load the new `.env` |
| Existing Odoo PostgreSQL service | Left untouched on port 5432 |
| Dedicated SmartCampus test cluster | PostgreSQL 12.4, isolated data directory `.smartcampus_pgdata`, loopback port 55432 |

The 500 handler was verified through an isolated test app. The production API has no route that should deliberately raise an unexpected error.

## Seed data

- Ran `python -m scripts.seed_demo` twice against the isolated SmartCampus database; both runs completed.
- Queried the table after both runs: **5 rows total** — 2 establishments, 2 programs and 1 fictional demo user. This confirms seed idempotency for the current staging schema.
- All data is fictitious and stored only in `smartcampus_demo.seed_records`; no team-owned tables were created.
- The actual IIT/ISB/user models are not yet integrated. Adapt these fixtures after Manar's user/profile and Tasnime's catalogue schemas are validated.

## Docker / Compose

- Docker CLI is unavailable, so `docker compose up --build`, container health, Compose PostgreSQL and container-to-database connectivity were not run.
- Compose YAML parsed successfully. Static checks confirm PostgreSQL 16, the persistent `postgres_data` volume, DB health check, backend dependency on DB health, and Dockerfile install/start commands.
- The separate local test cluster uses Odoo-bundled PostgreSQL 12.4 binaries only to validate this backend's SQLAlchemy connectivity and seed; it does not validate the configured PostgreSQL 16 container image.

## Task status

- **SA-7:** application startup, environment settings, health route and Swagger verified.
- **SA-9:** Dockerfile and Compose configuration statically verified; Docker runtime remains pending Docker availability.
- **SA-16:** successful SQLAlchemy/PostgreSQL connection verified against the isolated local test database; PostgreSQL 16 Compose connection remains pending Docker.
- **SA-18:** actual repeat seed and row count verified in the isolated staging schema; mapping into validated team-owned schemas remains pending.
- **SA-22:** all available backend endpoints and generic error handling tested; business and authorization scenarios await the team's API contracts.

## Next checks

- Restart the user's Uvicorn process on port 8000 so it reads the configured `.env`; confirm `/health/db` returns 200.
- When Docker is available, run `docker compose up --build` and repeat the DB and seed checks against PostgreSQL 16.
- Integrate catalogue/profile models only after their owners approve the shared schemas, then extend QA for delivered APIs and access rules.

## PostgreSQL repair — 20 November 2026

- Confirmed the previous PID 6212 was stale (no matching process, `pg_ctl` reported stopped, port 55432 closed). PostgreSQL logs show an unclean stop; WAL recovery completed successfully on normal startup. The PID file was not manually deleted.
- Started the existing SmartCampus-only cluster from `.smartcampus_pgdata` on `127.0.0.1:55432`; new PID 7316. PostgreSQL Odoo on port 5432 was not touched.
- Added `scripts/start_smartcampus_postgres.ps1` for repeatable, version-checked startup against that exact data directory. Its active-server check was verified not to launch a second instance.
- Changed the code/config example fallback to port 55432 so a missing `.env` will not target Odoo; `.env` itself was left unchanged.
- SQLAlchemy/psycopg read-only check confirmed database `smartcampus`, port 55432 and 5 staging rows.
- Restarted one FastAPI process on port 8000 and verified `/health`, `/health/db`, `/docs`, and `/openapi.json` all return 200; unknown route 404 and unsupported method 405.
- Added a configuration regression test. Latest suite: **11 passed**, one upstream deprecation warning; `pip check` clean.
- Docker remains unavailable, so the PostgreSQL 16 Compose image and container health are still unverified.

## Independent Sprint task improvements — 20 November 2026

- Added strict configurable CORS with explicit HTTP(S) origins only; wildcard, path-bearing, credential-bearing and invalid-port origins are rejected. No CORS origin is configured in the current `.env`, so browser CORS remains disabled until an explicit frontend origin is set.
- Database URL validation now rejects local port 5432 and malformed/non-PostgreSQL URLs while hiding values in validation errors. Compose's internal `db:5432` URL remains accepted.
- Error responses/logging omit exception text and sensitive request/connection details. Added tests for session closure, OpenAPI, CORS and invalid settings.
- Seed fixtures now have typed schema validation, unique IDs, required program fields, safe malformed-JSON/database errors and no secret-bearing exception messages. The real database seed was not rerun; its row count remained 5 in a read-only check.
- Dockerfile now runs as non-root. Compose now declares a project bridge network; PostgreSQL remains unexposed to the host and uses its named volume. PyYAML static checks pass; Docker CLI is still unavailable, so no build/up was claimed.
- Added documented non-destructive pg_dump/restore examples to a separate unused database; neither command was run.
- Final `python -m pip check`: clean. Final `python -m pytest -v`: **29 passed**, 1 upstream Starlette/AnyIO deprecation warning.
- Live after reload: `/health`, `/health/db`, `/docs`, `/openapi.json` all HTTP 200. SQLAlchemy connected to `smartcampus` on `127.0.0.1:55432`; 5 staging rows observed. No seed was executed and `.env` was not changed.

## Correction de vérification finale — 20 novembre 2026

- `python -m pip check` : **PASS**, aucune dépendance cassée.
- La dernière exécution `python -m pytest -v` après l'ajout des assertions de non-divulgation dans les logs est restée bloquée sur `tests/test_health.py::test_health_returns_200`. Le lancement isolé de ce seul test s'est également bloqué. Les deux processus de test ont été interrompus; le code de sortie final était 1 après interruption.
- Une exécution précédente sur la révision immédiatement antérieure a terminé avec **29 passed, 1 avertissement**. Ce résultat ne certifie pas la révision courante; le statut du jeu complet est donc **à revalider**. La cause du blocage n'est pas identifiée.

## Diagnostic pytest — 20 novembre 2026

Cause exacte du blocage précédent : **restriction des sockets locales dans le contexte d'exécution sandboxé de Codex**, et non deadlock applicatif, fixture, DB ou assertion. Une capture `faulthandler_timeout=5` du test bloqué montrait AnyIO démarrant `TestClient`, dans `asyncio` Windows `ProactorEventLoop._make_self_pipe` → `socket.socketpair()` → `accept()` en attente, avant toute exécution de la route. La même commande `socket.socketpair()` se bloquait en sandbox et finissait immédiatement hors sandbox. Sans modification du code, le test santé seul et les tests complets passent hors sandbox. Aucun test supprimé/désactivé; aucune modification applicative nécessaire.

Résultats hors sandbox : test isolé santé **1 passed**; `test_health.py` **11 passed**; `test_config.py` **11 passed**; `test_seed_demo.py` **6 passed**; `test_database.py` **1 passed**; suite `python -m pytest -v -o faulthandler_timeout=10` **29 passed, 0 failed, 1 avertissement de dépréciation Starlette/AnyIO** en 2.77 s. `python -m pip check` : aucune dépendance cassée.

Contrôle sécurité en lecture seule : port 5432 toujours à l'écoute via PID 8972 (service existant non arrêté ni modifié); port 55432 PID 7316 lié à `127.0.0.1`, `pg_ctl` confirme que le cluster utilise exclusivement `.smartcampus_pgdata`; FastAPI reste actif sur 127.0.0.1:8000. Les tests API utilisent TestClient et mockent l'accès SQL; le test seed emploie une connexion mémoire d'enregistrement; aucun test ne cible/modifie la base SmartCampus réelle. Les cas de fuite de secrets dans réponse et logs passent.
## Integration follow-up — 22 November 2026

- Read and cross-checked all five supplied PDFs and the SA-14 Markdown design against the delivered backend. The ER/workflow/architecture/API diagram pages were rendered and visually reviewed.
- Added SA-5 error-envelope handlers for HTTP errors, request validation and unexpected exceptions. Validation errors omit submitted input values. Added tests for 400/401/403/404/405/422/500/503 behavior and sensitive-input redaction.
- Latest `python -m pip check`: no broken requirements. Latest full suite on branch `yasmin`: **34 passed, 0 failed, 1 Starlette/AnyIO deprecation warning** (4.41 s). Tests were run outside the Codex sandbox because its Windows socket restriction blocks TestClient.
- Added `SCHEMA_MAPPING_PROPOSAL.md`, `tests/CONTRACT_TEST_PLAN.md` and a technical-only extension migration. These are proposals/plans; the team has not validated canonical table names, ID types or profile aliases. No business tables or foreign keys were created; the extension SQL was not run.
- The Docker CLI is unavailable. Compose still uses `postgres:16-alpine`, which does not bundle pgvector; changing the image while a persistent volume may exist was deferred. Compose build/start, PG16 integration and pgvector runtime remain unverified.
- No business seed was run. No PostgreSQL data, `.env`, branch, commit or remote was changed. Current branch remains `yasmin`; modifications are uncommitted.

## Vérification du code Formation Tasnime — 22 novembre 2026

- Inspection du checkout `yasmin`, des fichiers suivis et de la branche locale `origin/tasnime` : les sept fichiers Python mentionnés sont absents. La branche `origin/tasnime` disponible localement ne contient que `README.md`. Aucun « dernier tableau » séparé n'a été trouvé parmi les pièces jointes disponibles; le PDF de conception du catalogue reste la référence de schéma disponible.
- Le backend Yasmin contient `Base`, `engine`, `SessionLocal` et `get_db()` mais aucune route Formation, modèle ORM Formation, repository, service métier ni dépendance Admin. Le comportement du dictionnaire annoncé ne peut donc pas être confirmé dans le code. Aucun fichier de Tasnime n'a été remplacé.
- La proposition de mapping documente le branchement futur du repository à la session SQLAlchemy, le choix `PUT`/`PATCH`, l'alignement des FK UUID/SERIAL et les validations requises. Le plan de test décrit les cas Formation et Admin en attente; aucun endpoint artificiel n'a été ajouté.
- Vérification fraîche : `pip check` propre; suite complète hors environnement restreint **34 réussis, 0 échec, 1 avertissement Starlette/AnyIO en 1,59 s**. Dans l'exécution restreinte, `test_health_returns_200` bloque au `socketpair` asyncio Windows, avant l'exécution de la route.
- Aucun seed ou migration métier lancé; aucune donnée, `.env`, branche, commit, push ou PostgreSQL Odoo modifié.
