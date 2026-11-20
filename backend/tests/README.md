# Backend API tests

Run from `backend` with `.venv` active: `python -m pip check` then `python -m pytest -v`. Current tests cover environment and `.env` configuration, safe rejection of the Odoo port, explicit CORS policy, session closure, fixture validation and idempotent upsert generation, HTTP 200 health/OpenAPI/Swagger, mocked DB-health 200/503, HTTP 404/405, and sanitized 500 handling on an isolated test app. Tests do not seed or write to the configured database.

## Prepared for integration

When the other owners publish contracts, add tests for valid/invalid bodies (422 and applicable 400), creation responses (201), resource 404s, and authentication/authorization (401/403). Use dependency overrides and mocks for external services. Do not assert access rules until SA-5 and SA-28 contracts are available. Exercise unexpected errors in an isolated test app to verify the generic 500 handler without exposing internals. Keep an optional PostgreSQL integration check read-only unless an explicit seed test is requested.

The current suite does not claim coverage for routes that have not been implemented or specified.
