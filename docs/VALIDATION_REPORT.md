# Build and Validation Report

**Last updated:** 2026-11-26
**Branch:** `fullstack-upgrade`

This report distinguishes locally verified checks from checks that are still pending in the final repository.

## 1. Frontend Validation

**Environment:**
- Node.js: 26.13.1
- npm: 11.20.0
- Vite: 6.4.6
- Vitest: 4.1.12

**Verified results:**

| Check | Result |
|---|---|
| Clean dependency installation (`npm ci`) | Passed |
| npm security audit | 0 vulnerabilities |
| Frontend tests | 4 passed, 0 failed |
| TypeScript type checking | Passed |
| Vite production build | Passed |
| Install script review | No unreviewed scripts |

Commands executed:

```bash
npm ci --no-audit --no-fund
npm audit --audit-level=moderate
npm test
npm run build
npm install-scripts ls
```

## 2. Backend Security Validation

The following command was executed from the backend directory:

```bash
python -m pip_audit -r requirements-dev.txt
```

Result:

**No known vulnerabilities found.**

This result covers the dependency audit only. It does not establish that all backend tests or runtime checks have passed.

## 3. Backend Validation (Local)

**Environment:**
- Python: 3.12.10

**Verified results:**

| Check | Result |
|---|---|
| Dependency installation | Passed |
| pip check | No broken requirements |
| Ruff | All checks passed |
| Backend tests | 33 passed |
| Core and Services coverage | 84.05% |
| Coverage threshold | 80% passed |
| pip-audit | No known vulnerabilities |
| Fresh SQLite migration | Passed |
| Alembic head verification | Passed |

### Migration Results

All three migrations were successfully applied to a fresh SQLite database:

- 0001_initial
- 0002_auth_rate_limits
- 0003_task_indexes

Alembic current revision:

`0003_task_indexes (head)`

The smoke-test database was created successfully.

### Commands Executed

```powershell
python -m pip check
ruff check app tests scripts alembic
pytest --cov=app.core --cov=app.services --cov-report=term-missing --cov-fail-under=80
python -m pip_audit -r requirements-dev.txt
python -m scripts.migrate_db
alembic current
```
## 4. Historical Offline Validation

During the initial archive preparation, 33 backend tests passed with 84.05% combined coverage.

That preliminary offline test run used temporary compatibility adapters for JWT and password hashing because the actual packages were unavailable.

**Superseding verification (2026-11-26):**

The backend was subsequently tested in a clean Python 3.12.10 virtual environment with dependencies installed from `requirements-dev.txt`.

The new verification completed successfully:

- 33 backend tests passed.
- 84.05% combined coverage achieved.
- Ruff checks passed.
- pip-audit reported no known vulnerabilities.
- Fresh SQLite migrations completed successfully.
- Alembic confirmed `0003_task_indexes (head)`.

The new local test run supersedes the preliminary adapter-based results for the test paths covered by the current suite.

A dedicated regression test using a real legacy Bcrypt password hash should be retained as an explicit compatibility check before production deployment.
## 5. GitHub Actions

The repository contains a GitHub Actions workflow configured to run:

- Backend dependency installation.
- Ruff.
- Backend tests and coverage.
- Backend dependency auditing.
- Fresh database migration.
- Migration head verification.
- Frontend clean installation.
- Frontend dependency auditing.
- Frontend tests.
- Production build.

The workflow has not yet been verified through a completed GitHub Actions run on this branch.

## 6. Release Criteria

This version must not be considered production-ready until:

1. All backend checks pass with the actual declared dependencies.
2. Frontend tests and production build pass.
3. Dependency audits report no known vulnerabilities.
4. Fresh database migration succeeds.
5. GitHub Actions completes successfully on the final branch.

A successful local dependency audit alone does not constitute a production release approval.
