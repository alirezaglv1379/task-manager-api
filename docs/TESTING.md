# Testing and quality gates

## Backend tests

From `backend/` with the development dependencies installed:

```bash
pytest
pytest --cov=app.core --cov=app.services --cov-report=term-missing --cov-fail-under=80
ruff check app tests scripts alembic
pip-audit -r requirements.txt
```

The coverage target is at least 80% across Core and Services. Coverage is a guardrail, not a substitute for scenario-based tests.

## Test groups

- Unit: validation, token claims, password length guard, UTC type and service logic.
- Integration: SQLAlchemy sessions, refresh-session rotation, persistent rate-limit counters and Alembic migration paths.
- API: signup/login, `/users/me`, task CRUD, ownership, PUT/PATCH, filters, sorting, pagination, 401/404/409/422/429 and cookie flows.
- Frontend: build/type-check in CI; manual smoke test of login, refresh, task creation/edit/delete, filters and pagination.

## Frontend tests

From `frontend/` after `npm install`:

```bash
npm run test
npm run build
```

Vitest + Testing Library cover the login/signup flow, task form submission and API query construction (including the `is_completed=false` filter).

## CI

GitHub Actions runs Ruff, pytest with coverage, pip-audit, a fresh database migration, and the frontend production build. A failed quality/security gate blocks the workflow.

## Important environment note

Run the full test suite using the actual packages installed from `requirements-dev.txt`. Test-only adapters or mocks for JWT/password libraries are not a substitute for verifying the pinned production dependencies.
