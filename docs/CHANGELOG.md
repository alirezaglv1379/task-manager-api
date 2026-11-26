# Changelog

## 2.0.0 — Full-stack rebuild

- Reorganized the backend as a modular monolith.
- Added strict Pydantic request validation and separate PUT/PATCH schemas.
- Added strict Access Token claim validation and 30-minute lifetime.
- Added seven-day opaque Refresh Token sessions, HttpOnly cookie and rotation.
- Added persistent IP and username login rate limits.
- Added `/users/me`.
- Added server-side task pagination and safe sorting.
- Added UTC-aware SQLAlchemy datetime handling.
- Added Alembic migrations and a legacy SQLite backup/migration script.
- Added React + TypeScript RTL frontend.
- Added backend tests, documentation and GitHub Actions workflow.

## 1.0.0 — Original API

The original API baseline remains available in the repository's Git history (commit 807e053).