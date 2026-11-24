# Contract test plan — current coverage and pending contracts

This file distinguishes tests run against routes that exist on `yasmin` from scenarios waiting for other APIs/contracts. Pending business scenarios are not represented as passing or skipped pytest tests.

## Implemented routes covered by tests on `yasmin`

The current application registers only these HTTP API routes (see `app/main.py`):

- `GET /health` and `GET /health/db`.
- `GET /api/v1/catalogue/programmes` and `GET /api/v1/catalogue/programmes/{slug}`.
- `/docs` and `/openapi.json` are documentation endpoints, not domain APIs.

`tests/test_health.py`, `tests/test_catalogue_consultation.py` and `tests/test_sa22_catalogue_contract.py` cover successful responses, query validation, filters/search, empty results, public response shape, list/detail consistency, hidden draft/archive/inactive records, nonexistent resource 404, method 405, OpenAPI, the shared error envelope, sanitized 500, and mocked DB-health 503. The catalogue suite includes CAT-01 through CAT-18; CAT-18 specifically checks a slug that does not exist. On 24 November 2026 in WSL, the latest results were 22 SA-22 catalogue tests passed, 16 health tests passed and 102 backend tests passed after adding three positive filter tests (one Starlette/AnyIO deprecation warning; no failures or skips).

The 400/401/403 envelope checks use temporary test-only routes to exercise the shared exception handler; they do not prove that business routes implement authentication or role authorization. The catalogue GET routes are public. `/health/db` checks use a mocked connection in unit tests, not a live PostgreSQL connection.

Additional existing backend tests cover settings/CORS, protected port configuration, SQLAlchemy session cleanup, fixture validation and seed-planning behavior. They do not expose extra domain HTTP routes.

## Pending endpoint scenarios from SA-5

| Area / endpoints | Planned checks | Contract/dependency |
|---|---|---|
| `POST /api/v1/auth/register`, `/login`; `GET /auth/me` | 201 registration response, field validation, password hash only, role, Bearer token, session attachment, duplicate email outcome | Manar user schema; Amina final auth contract; duplicate outcome currently unspecified |
| `POST /api/v1/chat`, `GET /chat/historique`, `POST /chat/rattacher` | Message length 1–2000, required UUID v4 visitor session, JSON response when `stream=false`, SSE content type when enabled, history retrieval and atomic visitor-to-account attachment | Roua conversation/session contract; Manar session schema; agents API |
| `GET /api/v1/formations[/{id}]`, `POST/PATCH/DELETE /api/v1/formations` | Public visibility only for PUBLIE records under active establishment; admin-only writes; filter and payload validation; RAG source citations | These SA-20/Tasnime routes are not registered on `yasmin`; confirm final route/ID contract and integrate the owner implementation before route tests |
| `/api/v1/candidats/{id}/profil`, recommendations, conversations | Candidate self-ownership; admin reads; 403 for another candidate; profile completeness, enum/range/list constraints; private summary/history access | Manar profile schema + Amina contract; field-name mapping pending |
| `GET /preinscriptions/lien`, `POST /preinscriptions/webhook`, `/dossiers*`, complements | Webhook secret accepted/rejected; source ID idempotence; 201 creation; dossier visibility; admin-only decisions; candidate-owned complement submission; summary filtered for candidate | Amina SA-14 schema/migration and canonical user/catalogue IDs |
| `/qcm*` | Candidate ownership; save/reload progress; question index >= 0; reject edits after completion with 400; final score range; admin-only results | Amina QCM schema; profile/catalogue foreign keys |
| `/rendez-vous*` | Admin confirmation required before candidate notification; candidate own-resource checks; accepted/unavailable responses; replacement slot lifecycle; end after start | Amina SA-14 and mail/calendar integration contracts |
| `/api/v1/internal/tools/*` | Internal API key required; deny public/candidate access; verify each tool uses Backend data access only; no tool can decide admission | Amina internal-key contract; agent service owner |

## Cross-cutting expected assertions

- All domain endpoints use `/api/v1`; keep operational health probes separate unless the team elects a different convention.
- Errors match `{ "error": { "code": "...", "message": "...", "details": {} } }` for 400/401/403/404/422/500 (and the operational 503 DB health response).
- IDs accepted in JSON and path parameters match the approved SQL types or documented opaque-ID mapping; never coerce UUID, SERIAL and text IDs implicitly.
- Candidate ownership and service identities are checked independently from data validation.
- SQL integration tests use a disposable SmartCampus database or isolated test schema, never PostgreSQL Odoo on port 5432 or the local persistent cluster without explicit authorization.

## Formation repository and authorization plan (not yet executable)

The seven Tasnime Python files named in earlier coordination were not found in this checkout; the route inventory above confirms there are no formation-management endpoints registered on `yasmin`. This plan does not claim to test their implementation. Once Tasnime's files are integrated and the schema and route contract are approved, add tests for:

- Public `GET` list/detail filters, only published formations for active establishments, empty/not-found results, and stable response IDs.
- `POST`, `PATCH`, and `DELETE`: unauthenticated 401; authenticated non-admin 403; admin success; request validation and duplicate-code conflict.
- Repository SQLAlchemy behavior: persistence across independent sessions, list/detail ordering and filters, transaction rollback on failure, unique-constraint conflict mapping, and deletion behavior for referenced catalogue rows.
- Common SA-5 error envelope for route validation, 404, 409 duplicate conflict (if agreed), 401, 403 and 500 without leaking SQL, credentials or submitted secrets.
- OpenAPI documents role requirements, request/response schemas, and error responses consistently with Amina's contract.

The SQL tests must use an isolated disposable test database/schema. Do not connect these tests to the persistent local SmartCampus database until explicitly configured for test use.
