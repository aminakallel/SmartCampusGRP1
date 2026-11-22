# SmartCampus AI — Sprint 1 Delivery Report

Date: 20 November 2026
Scope: personal tasks SA-7, SA-9, SA-16, SA-18 and SA-22.

## Delivery summary

This audit confirms the FastAPI health/documentation routes, local SmartCampus PostgreSQL connection, package consistency and all 29 unit tests. Docker runtime and integration with teammates' business APIs were not available for verification. No business schema or endpoint owned by another teammate was added.

## Git and secret review

- `git rev-parse --show-toplevel` from both the workspace and `backend` reported that neither directory is inside a Git repository. Therefore `git status`, `git diff`, tracked/untracked classification and an index-based check of ignored files could not be performed. No commit or push was made.
- `.gitignore` contains entries for `.env`, `.venv/`, `__pycache__/`, `.pytest_cache/`, `.smartcampus_pgdata/`, `.smartcampus_pg.log` and `backups/`. This confirms the ignore rules exist, but cannot prove Git is applying them without repository metadata.
- `.env` was not read or displayed. A scan of source/document/config files (excluding `.env`, the virtual environment, caches and PostgreSQL data) found no non-placeholder secret assignments. `.env.example` contains the documented placeholder `change-me-local`, which is not a production credential. Without a Git index, this is not a claim about all versioned files.
- Prior audit notes list `tests/test_database.py` as created and application/configuration/tests/Docker/docs files as modified. During this final audit, `README.md` was corrected and this `SPRINT1_DELIVERY_REPORT.md` was created. These file-change lists are workspace observations/history, not verified Git status.

## SA-7 — FastAPI foundation and health/error handling

**Objective:** provide a configured FastAPI app, health and database-health endpoints, API docs, safe error handling and explicit CORS configuration.

**Implemented:** `/health`, `/health/db`, Swagger/OpenAPI; generic errors hide internal details; CORS accepts explicit HTTP(S) origins only and remains disabled when none are configured; local database URLs targeting Odoo's port 5432 are rejected.

**Files:** `app/main.py`, `app/api/routes/health.py`, `app/core/config.py`, `.env.example`, `tests/test_health.py`, `tests/test_config.py`.

**Evidence:** fresh local GET checks returned HTTP 200 for `/health`, `/health/db`, `/docs` and `/openapi.json`. The health tests cover 404, 405, sanitized 500, CORS policy, simulated DB success/failure and no secret leakage in responses/logs.

## SA-9 — Docker configuration

**Objective:** define the backend/PostgreSQL Compose services, health ordering, environment and persistent storage.

**Implemented:** backend image runs as non-root `app`; Compose defines PostgreSQL 16 and backend, health checks, backend dependency on healthy DB, named `postgres_data` volume and private project network. PostgreSQL has no published host port. Environment variables are declared in Compose and documented in `.env.example`.

**Files:** `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `README.md`.

**Evidence and limitation:** PyYAML parsing plus static assertions passed for services, health checks, dependency, named volume/network, non-published DB port and non-root Docker user. Docker CLI is unavailable; `docker compose config`, image build, container startup, PostgreSQL 16 health and backend-to-container DB connectivity were not tested.

## SA-16 — PostgreSQL and SQLAlchemy connection

**Objective:** keep database access configured for SmartCampus, manage SQLAlchemy sessions safely and provide a safe local startup path.

**Implemented:** psycopg SQLAlchemy engine with `pool_pre_ping`, `SessionLocal`, and `get_db` cleanup; configuration rejects local port 5432. The Windows start script checks the existing cluster and binary major version, then targets only `.smartcampus_pgdata` at `127.0.0.1:55432`. README includes backup/restore examples that target a new database for restore rehearsal; these examples were not run.

**Files:** `app/db/database.py`, `app/core/config.py`, `scripts/start_smartcampus_postgres.ps1`, `docker-compose.yml`, `README.md`, `tests/test_database.py`, `tests/test_config.py`.

**Evidence:** the startup script exited successfully and reported PID 7316 already running against `backend/.smartcampus_pgdata` on `127.0.0.1:55432`; it did not start another process. A read-only SQLAlchemy query returned database `smartcampus`, address `127.0.0.1/32`, port `55432`. `/health/db` returned 200. Port 5432 remained listening under existing PID 8972 and was not stopped or modified. The local cluster is PostgreSQL 12; PostgreSQL 16 in Compose remains unverified.

## SA-18 — Demo seed data

**Objective:** validate fictional demo fixtures and insert them safely and idempotently into isolated staging storage.

**Implemented:** typed fixture validation, required fields, provisional-only records, unique IDs and sanitized fixture/database errors; idempotent upsert into `smartcampus_demo.seed_records` only.

**Files:** `scripts/seed_demo.py`, `seed_data/demo_records.json`, `tests/test_seed_demo.py`, `README.md`.

**Evidence:** six seed tests passed, including fictional/provisional validation, invalid fixture cases and repeated upsert statements. Earlier QA records document two actual seed executions with five staging rows (2 establishments, 2 programs, 1 demo user) after each. The seed was not executed during this final audit. It is not mapped to Manar's profile or Tasnime's catalogue schemas.

## SA-22 — Automated QA and API safety

**Objective:** automate checks for the implemented backend contract and safe failure/configuration behavior.

**Implemented:** 29 unit tests across configuration, health/API, database-session lifecycle and seed validation. Tests use TestClient, mocks and a recording fake for seed upserts; they do not modify the live PostgreSQL data.

**Files:** `tests/test_config.py`, `tests/test_health.py`, `tests/test_database.py`, `tests/test_seed_demo.py`, `tests/README.md`, `pytest.ini`, `requirements.txt`.

**Evidence:** full suite completed successfully outside the Codex sandbox: **29 passed, 0 failed, 1 upstream Starlette/AnyIO deprecation warning, 1.47 s**. `python -m pip check` reported `No broken requirements found`. The sandbox hang was traced to its restriction on Windows local socket creation in `asyncio`/AnyIO `TestClient`; no tests were disabled or changed to simulate success.

## Commands and outcomes

Commands run from `backend` unless stated otherwise:

| Command/check | Outcome |
|---|---|
| `git rev-parse --show-toplevel` (workspace and backend) | No Git repository found; status/diff/index checks unavailable |
| `.\.venv\Scripts\python.exe -m pip check` | Pass: no broken requirements |
| `.\.venv\Scripts\python.exe -m pytest -v -o faulthandler_timeout=10` | Pass: 29 passed, 0 failed, 1 warning, 1.47 s; run outside sandbox |
| `.\.venv\Scripts\python.exe -m pytest -vv -o faulthandler_timeout=10 tests/test_health.py::test_health_returns_200` | Pass: 1 passed |
| Same pytest command for `tests/test_health.py` | Pass: 11 passed |
| Same pytest command for `tests/test_config.py` | Pass: 11 passed |
| Same pytest command for `tests/test_seed_demo.py` | Pass: 6 passed |
| Same pytest command for `tests/test_database.py` | Pass: 1 passed |
| `Invoke-WebRequest` GET `/health`, `/health/db`, `/docs`, `/openapi.json` | All HTTP 200 |
| SQLAlchemy read-only identity query | `smartcampus`, `127.0.0.1/32`, port 55432 |
| `scripts/start_smartcampus_postgres.ps1` | Pass; reported existing PID 7316 and exact dedicated data directory; no second server launched |
| Compose YAML/static checks | Pass; Docker CLI unavailable, so runtime commands not run |
| `.gitignore`/source secret scan | Ignore rules present; no non-placeholder secret assignment found in scanned source; Git tracking cannot be established |

## Evidence to present

- Pytest terminal output showing the complete 29/29 run and `pip check` success.
- HTTP status output for the four live endpoints.
- `pg_ctl`/startup-script output showing PID 7316, `.smartcampus_pgdata` and port 55432, plus the read-only database identity result.
- Static Compose check output documenting which configuration properties were checked.
- Previously supplied screenshots show `/health` responding and the Swagger page/routes. They are useful UI evidence, but the screenshot showing `/health/db` as unavailable is from before the PostgreSQL repair and must not be presented as a successful current DB check.

## Remaining limits and team dependencies

- **Docker:** install/enable Docker, then run `docker compose config`, build and start; verify PostgreSQL 16 health and backend connectivity. No Docker claim is made from YAML-only checks.
- **Manar:** provide the validated user/profile schema (noted as SA-13/SA-17 in the prior task allocation) before integrating the demo user fixture.
- **Roua:** provide the consultation API (SA-21) and coordinate Backend/Frontend integration checks.
- **Tasnime:** provide the catalogue schema/API and authentication contract (noted as SA-12/SA-20/SA-28) before mapping catalogue seed data or writing dependent authorization tests.
- **Amina:** provide the API contract and access rules (SA-5) for meaningful 400/401/403 and payload-validation scenarios.
- Business endpoints, shared schemas, migrations, authentication and authorization have not been invented or tested. PostgreSQL backup/restore examples are documentation only and were not executed.
- Git review remains incomplete until this workspace is opened as a Git checkout; do not infer an index or clean working tree from `.gitignore` alone.

## Final status

| Task | Status | Reason |
|---|---|---|
| SA-7 | **PASS** | Implemented API safety/health scope and current HTTP/test checks pass; no claim about absent business APIs. |
| SA-9 | **PARTIAL** | Docker configuration passes static checks; container build and runtime unavailable. |
| SA-16 | **PASS** | Dedicated local PostgreSQL connection and health endpoint verified; Compose PostgreSQL 16 remains outside this task's verified scope. |
| SA-18 | **PARTIAL** | Validation/idempotence tests pass and prior real seed evidence exists; final-audit seed was not rerun and shared-schema mapping awaits owners. |
| SA-22 | **PARTIAL** | All 29 available tests pass; business and authorization contracts are pending from teammates. |

## Follow-up after team documents — 22 November 2026

The attached team documents were reviewed in full and key diagram/table pages were visually checked. See `SCHEMA_MAPPING_PROPOSAL.md` for the detailed proposed schema comparison and owner decisions still required. The schema mapping has **not** been approved; the files remain a proposal.

Independent SA-7 work now applies the SA-5 `{error: {code, message, details}}` envelope to HTTP, validation and generic failures. The latest suite is **34 passed, 0 failed, 1 upstream warning**; `pip check` is clean. `tests/CONTRACT_TEST_PLAN.md` records business tests that are pending final contracts.

Added `migrations/0000_enable_extensions.sql` for `pgcrypto` and pgvector only. It has not been applied, creates no tables and must not be run against a server without both extensions. The Compose image remains `postgres:16-alpine`; Docker CLI is unavailable and changing the image was deferred because the compatibility of a persistent volume cannot be checked here.

No schema-dependent models/FKs, migrations, production seed or business endpoints were added. No seed, backup, database mutation, commit or push was performed in this follow-up. The working branch remains `yasmin`.

| Task | Updated status | Current evidence / outstanding |
|---|---|---|
| SA-7 | **PARTIAL** | Error envelope now matches SA-5 and tests pass; versioned business routers/auth remain unimplemented and owned contracts are incomplete. |
| SA-9 | **PARTIAL** | Static Compose config remains reviewed; Docker runtime unavailable and pgvector image/volume plan is unresolved. |
| SA-16 | **PARTIAL** | SQLAlchemy/local PostgreSQL verification was previously successful; only independent extension SQL is prepared. Tables/FKs/migrations await schema approval. |
| SA-18 | **PARTIAL** | Existing staging seed remains isolated; no relational seed until canonical IDs, tables and FKs are approved. |
| SA-22 | **PARTIAL** | 34 available tests pass; pending API test matrix is documented but no missing business routes are simulated. |

## Présence réelle du code Formation — 22 novembre 2026

Les sept fichiers attribués à Tasnime (`schemas/formation.py`, `api/v1/formations.py`, `core/security.py`, `services/formation_service.py`, `repositories/formation_repository.py`, `core/errors.py`, `api/responses.py`) ne sont pas présents dans le checkout ni dans la branche `origin/tasnime` disponible localement, dont l'arbre contient uniquement `README.md`. Aucun tableau séparé plus récent n'était disponible dans les pièces jointes accessibles. Le code annoncé comme stockant les formations dans un dictionnaire n'a donc pas pu être vérifié.

Le backend possède déjà la session SQLAlchemy request-scoped. La proposition décrit l'adaptation future sans modifier les fichiers de Tasnime ni inventer ses modèles : repository injecté avec `get_db()`, contraintes de doublons en base à définir, transactions et erreurs alignées sur l'enveloppe SA-5. Les tests Formation/Admin sont planifiés mais restent en attente de l'intégration réelle des routes et des validations de schéma.

Vérification du 22 novembre 2026 : `python -m pip check` réussi; suite complète **34 réussis, 0 échec, 1 avertissement amont en 1,59 s** hors restriction socket Windows. Aucun seed relationnel ni migration métier exécuté. Aucun commit ni push effectué; branche `yasmin` conservée.
