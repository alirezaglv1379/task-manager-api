# Database

SQLite is retained for portability and simple local deployment. SQLAlchemy 2.0 is used synchronously.

## Tables

- `users`: user id, unique username and password hash.
- `tasks`: task content, completion state, UTC creation time and owner foreign key.
- `refresh_sessions`: hashed refresh token, session family, expiry and revocation timestamps.
- `login_rate_limits`: hashed IP/username key, fixed-window counter and expiry.
- `alembic_version`: applied migration revision.

## Ownership

Every task query is scoped by both `tasks.id` and `tasks.owner_id` where a single task is requested. A user cannot read, update or delete another user's task; inaccessible task IDs return 404.

## UTC handling

SQLite does not have a native timezone-aware datetime type. `UTCDateTime` normalizes aware input values to UTC before binding and returns aware UTC values after reading. Legacy naive timestamps created by the original application are interpreted as UTC, because the original task creation path explicitly used `datetime.now(timezone.utc)`.

Date-only concepts (for example a future due date without a time) should use a date type rather than being converted to a UTC instant.
