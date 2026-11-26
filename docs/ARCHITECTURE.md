# Architecture

## Style

The application is a modular monolith. Backend and frontend are separate deployable folders, while the API remains a single FastAPI application backed by SQLite.

## Backend layers

```text
HTTP Request
    -> API Router
        -> Dependency / Authentication
        -> Service Layer
            -> SQLAlchemy Models / Session
                -> SQLite
```

- `app/api`: HTTP routes and request/response orchestration.
- `app/core`: settings and security primitives.
- `app/db`: SQLAlchemy base, engine/session dependency and UTC type.
- `app/models`: SQLAlchemy persistence models.
- `app/schemas`: Pydantic request/response schemas.
- `app/services`: business logic, refresh-session lifecycle, rate limiting and task operations.
- `alembic`: schema migrations.
- `tests`: unit, integration, API and migration tests.

`get_db` is defined once in `app/db/session.py`. The app is constructed through `create_app()`. Importing the application does not create or modify database tables.

## Frontend

React + TypeScript + Vite. The UI is Persian-first and RTL. The browser keeps Access Token only in memory. Refresh Token is an HttpOnly cookie and is never read by JavaScript.

During development, Vite proxies `/api/*` to FastAPI. In production, serve frontend assets and reverse-proxy `/api/*` through the same origin.

## API compatibility

Existing routes `/signup`, `/login`, `/tasks`, and `/tasks/{task_id}` are preserved. `GET /tasks` now returns a paginated envelope rather than a bare array, as agreed for the new frontend contract.

## Deliberate scope limits

- No microservices.
- No Repository Layer for this project's current size.
- SQLite remains the default database.
- No social login, file uploads, task sharing, or team workspaces in this release.
