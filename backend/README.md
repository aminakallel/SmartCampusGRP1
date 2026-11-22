# SmartCampus AI Backend

FastAPI foundation for Sprint 1 tasks SA-7, SA-9, SA-16, SA-18 and SA-22. No validated shared catalogue, profile, authentication or business API contracts were present. Those schemas and routes remain owned by their assigned teammates.

## Local development

Requires Python 3.12+ and a PostgreSQL cluster whose major version matches the installed PostgreSQL tools. On this workstation, local development uses the existing SmartCampus-only PostgreSQL 12 cluster; Docker Compose uses PostgreSQL 16.

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
uvicorn app.main:app --reload
```

The health route is `GET /health`; Swagger is at `/docs`, and the OpenAPI JSON is at `/openapi.json`. API health does not depend on the database. `GET /health/db` runs `SELECT 1` and returns HTTP 503 when the database is unavailable. Configuration is loaded from `.env` or process environment. A local URL using port 5432 is rejected because that port is reserved for PostgreSQL Odoo on this workstation.

API errors use the SA-5 envelope `{ "error": { "code": "...", "message": "...", "details": {} } }`. Validation responses omit submitted input values, which can contain passwords or tokens.

### CORS

Set `CORS_ORIGINS` to a comma-separated list of explicit frontend origins, for example `http://localhost:3000`. CORS is disabled when the list is empty. Wildcard origins, URL paths and credentials in origins are rejected in every environment; the application never enables credentialed cross-origin requests.

## Docker Compose

If `.env` does not exist, copy `.env.example` to `.env`; otherwise preserve it and verify its PostgreSQL variables. Change the local development placeholder password before use. From this directory:

```powershell
docker compose up --build
docker compose down
```

Compose starts PostgreSQL and the API, waits for PostgreSQL's health check, and stores database files in the named `postgres_data` volume. `docker compose down` retains the volume; `docker compose down -v` deletes it and its data. The committed fallback password is a local placeholder and must not be used in deployment.

## Database

SQLAlchemy engine, declarative `Base`, and request-scoped `get_db` live in `app/db/database.py`. The URL uses `postgresql+psycopg://`. Shared feature tables and ORM models are not declared because the attached user/catalogue/management schemas have unresolved key/table-name differences. `migrations/0000_enable_extensions.sql` is a technical prerequisite only; it creates `pgcrypto` and `vector`, no application tables. Do not apply it until the target PostgreSQL installation supplies both extensions. The current Compose image is PostgreSQL 16 Alpine without pgvector; changing it requires checking the compatibility of any existing persistent `postgres_data` volume. Verify connectivity at `http://localhost:8000/health/db` after starting services.

On the current Windows workstation, the existing SmartCampus-only test cluster is in `.smartcampus_pgdata` and listens on `127.0.0.1:55432`. Start or verify it from `backend` with `.\scripts\start_smartcampus_postgres.ps1`. The script checks that the initialized cluster exists and that the PostgreSQL major version matches; it does not initialize, delete, or target the Odoo cluster. It uses the installed PostgreSQL bin directory or `SMARTCAMPUS_PG_BIN` when set. The cluster data directory and credentials are local-only and ignored by Git. Do not run `initdb` against an existing cluster.

For local runs, start the SmartCampus cluster script first, then Uvicorn. The Compose backend instead uses the internal hostname `db:5432`; Compose supplies that URL to the container independently of the host-local `.env` URL.

## Demo seed data

From `backend` (with the environment active and PostgreSQL reachable), run:

```powershell
python -m scripts.seed_demo
```

The script validates the fixture document and each record before opening a database transaction. It writes only to isolated `smartcampus_demo.seed_records` and is safe to rerun. All examples are fictitious. Program levels, durations and admission details are marked for validation; none are official IIT/ISB information. Map the fields into team models only after schema coordination. The JSON validator is a demo-data contract, not a replacement for the catalogue or user schemas.

## Backup and restore (local SmartCampus cluster)

These are manual, non-destructive examples for the isolated SmartCampus database at port 55432. They prompt for the database password rather than putting it in the command line. Use PostgreSQL tools compatible with the server version. Do not point them to port 5432 or the Odoo data directory.

```powershell
$pgBin = if ($env:SMARTCAMPUS_PG_BIN) { $env:SMARTCAMPUS_PG_BIN } else { 'C:\Program Files\Odoo 19.0.20260202\PostgreSQL\bin' }
New-Item -ItemType Directory -Force .\backups | Out-Null
$backup = Join-Path (Resolve-Path .\backups) ("smartcampus_" + (Get-Date -Format 'yyyyMMdd_HHmmss') + '.dump')
& (Join-Path $pgBin 'pg_dump.exe') --format=custom --host=127.0.0.1 --port=55432 --username=smartcampus --dbname=smartcampus --file=$backup --password
```

To rehearse a restore without replacing the live database, create a new, unused database name such as `smartcampus_restore_test` and restore without `--clean` or `--create`:

```powershell
& (Join-Path $pgBin 'createdb.exe') --host=127.0.0.1 --port=55432 --username=smartcampus --password smartcampus_restore_test
& (Join-Path $pgBin 'pg_restore.exe') --no-owner --host=127.0.0.1 --port=55432 --username=smartcampus --dbname=smartcampus_restore_test --password $backup
```

The restore commands above are documentation only; no backup or restore was run during the latest QA work.

## Tests and QA

From `backend` with `.venv` active, run `python -m pip check` and `python -m pytest -v`. Unit tests use FastAPI `TestClient` and mocks; no seed is executed and no database rows are changed. See [tests/README.md](tests/README.md), [QA_REPORT.md](QA_REPORT.md) and [SPRINT1_AUDIT_REPORT.md](SPRINT1_AUDIT_REPORT.md).

## Team schema integration status

See [SCHEMA_MAPPING_PROPOSAL.md](SCHEMA_MAPPING_PROPOSAL.md) for the column/key comparison and decisions awaiting Manar, Tasnime and Amina. See [tests/CONTRACT_TEST_PLAN.md](tests/CONTRACT_TEST_PLAN.md) for business API scenarios that are planned but not implemented or executed. Do not run the existing staging seed as if it were a production/team-schema seed.

## Integration points

- `Base`, engine and `get_db` are infrastructure hooks for team-owned models.
- `DATABASE_URL`, PostgreSQL 16 and the demo staging schema are provisional development conventions.
- No catalogue, profile, authentication, guest-session, pre-registration, appointment or conversation routes/models were added.
- No Alembic migrations were introduced before shared schemas are validated.
