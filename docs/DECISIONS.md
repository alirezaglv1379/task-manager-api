# Project decision log — 16 approved items

This document records the implementation baseline approved before the rebuild.

1. **JWT secret:** load a strong secret from environment/`.env`; provide `.env.example`; never commit real secrets.
2. **Task filter:** use `is_completed is not None` so `false` remains a valid filter.
3. **Validation:** username 3–30 characters; password at least 8 characters and at most 72 UTF-8 bytes for Bcrypt; task title 1–200; description at most 2,000; completion status boolean.
4. **CORS:** configured by environment and `allow_credentials=False`; use a same-origin frontend proxy for refresh cookies.
5. **Access-token validation:** verify signature, require numeric `exp`, positive numeric-string `sub`, `type=access`, and an existing user; return standard 401 with `WWW-Authenticate: Bearer`.
6. **Database errors:** handle `IntegrityError`, use explicit rollback, close sessions, log safe technical errors and return generic messages.
7. **PUT/PATCH:** PUT replaces all editable fields (`title`, `description`, `is_completed`); PATCH changes only supplied fields; only `description` may be null; reject empty PATCH and unknown/system fields.
8. **Session lifecycle:** 30-minute Access Token; seven-day opaque Refresh Token in HttpOnly cookie; store only token hash; rotate on refresh; revoke on logout.
9. **Login rate limiting:** 20 requests per IP and 5 failed attempts per username per 15-minute window; SQLite counters; HTTP 429 and `Retry-After`; no permanent account lock.
10. **Current user:** add authenticated `GET /users/me`, returning only `id` and `username`.
11. **Task listing:** server-side pagination, default page 1 and size 20, maximum size 100, safe sorting, stable tie-breaker and structured page response.
12. **Migrations:** retain SQLite and use Alembic; backup before legacy migration; support fresh and recognized legacy databases; remove `create_all()` from normal startup.
13. **Time:** UTC-aware SQLAlchemy type for SQLite; ISO 8601 API output; local display in frontend; preserve legacy UTC clock values.
14. **Architecture:** modular monolith with API, Core, DB, Models, Schemas and Services; one `get_db`; `create_app()`; no Repository Layer for current scope.
15. **Dependencies:** minimal changes; retain FastAPI/Uvicorn and current JWT/password libraries temporarily; keep JWT fixed to HS256; preserve Bcrypt compatibility; remove unused async DB dependencies after full search; add Alembic/dotenv; separate dev tools; generate exact lock after successful resolution and tests.
16. **Quality and delivery:** unit, integration, API and frontend tests; at least 80% Core/Services coverage; Ruff, pip-audit and GitHub Actions; professional documentation; clean ZIP without secrets, caches, virtualenvs or `node_modules`.

## Implementation status

The source tree and implementation for these decisions are included in this archive. See `VALIDATION_REPORT.md` for the precise local test results and environment limitations. Dependency lock generation and real-package/frontend CI validation remain release gates because the build environment had no registry access.
