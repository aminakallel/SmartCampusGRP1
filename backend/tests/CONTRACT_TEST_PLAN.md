# Contract test plan — pending final schema/API validation

This file is a test plan, not a test result. No pending business scenario is represented as a passing or skipped pytest test. Add executable tests only after the route owners publish final schemas and response contracts.

## Ready against the current foundation

These are implemented and covered in the current unit suite:

- Health and DB health responses, Swagger/OpenAPI availability, 404/405 behavior.
- SA-5 error envelope for HTTP errors, validation errors and unexpected failures.
- Omission of submitted values, exception details and secrets from public errors/logs.
- CORS allowlist behavior, database URL protection for local port 5432, SQLAlchemy session closure, seed fixture validation/idempotent upsert logic.

## Pending endpoint scenarios from SA-5

| Area / endpoints | Planned checks | Contract/dependency |
|---|---|---|
| `POST /api/v1/auth/register`, `/login`; `GET /auth/me` | 201 registration response, field validation, password hash only, role, Bearer token, session attachment, duplicate email outcome | Manar user schema; Amina final auth contract; duplicate outcome currently unspecified |
| `POST /api/v1/chat`, `GET /chat/historique`, `POST /chat/rattacher` | Message length 1–2000, required UUID v4 visitor session, JSON response when `stream=false`, SSE content type when enabled, history retrieval and atomic visitor-to-account attachment | Roua conversation/session contract; Manar session schema; agents API |
| `GET /api/v1/formations[/{id}]`, `POST/PATCH/DELETE /api/v1/formations` | Public visibility only for PUBLIE records under active establishment; admin-only writes; filter and payload validation; RAG source citations | Tasnime catalogue schema; PATCH decision confirmed, source SA-5 document still needs update |
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

The seven Tasnime Python files named in the task were not found in the repository checkout or the locally available `origin/tasnime` branch, so this plan does not claim to test their implementation. Once Tasnime's files are integrated and the schema and route contract are approved, add tests for:

- Public `GET` list/detail filters, only published formations for active establishments, empty/not-found results, and stable response IDs.
- `POST`, `PATCH`, and `DELETE`: unauthenticated 401; authenticated non-admin 403; admin success; request validation and duplicate-code conflict.
- Repository SQLAlchemy behavior: persistence across independent sessions, list/detail ordering and filters, transaction rollback on failure, unique-constraint conflict mapping, and deletion behavior for referenced catalogue rows.
- Common SA-5 error envelope for route validation, 404, 409 duplicate conflict (if agreed), 401, 403 and 500 without leaking SQL, credentials or submitted secrets.
- OpenAPI documents role requirements, request/response schemas, and error responses consistently with Amina's contract.

The SQL tests must use an isolated disposable test database/schema. Do not connect these tests to the persistent local SmartCampus database until explicitly configured for test use.
