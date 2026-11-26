# Database migrations and backup

Alembic is the only schema migration mechanism in normal operation. `Base.metadata.create_all()` is not called during application import or startup.

## Revisions

- `0001_initial`: schema matching the original users/tasks tables.
- `0002_auth_rate_limits`: refresh sessions and persistent login rate-limit counters.
- `0003_task_indexes`: normalize legacy null completion flags, enforce task constraints and add task query indexes.

## Safe migration command

From `backend/`:

```bash
python -m scripts.migrate_db
```

The script:

1. Resolves the configured SQLite file.
2. Initializes a new database through `alembic upgrade head`, or inspects an existing database.
3. If a legacy database has the expected `users` and `tasks` columns but no Alembic version, creates a SQLite online backup.
4. Stamps `0001_initial` only after checking the baseline columns.
5. Applies remaining migrations.
6. Stops without changing an unrecognized/partial schema.

Backups are created beside the database with a timestamped `.backup-...db` filename. Keep backups outside web-served directories and verify restore procedures periodically.

## Manual commands

```bash
alembic current
alembic history
alembic upgrade head
alembic downgrade -1
```

Do not use `stamp` manually unless the live schema has been inspected and matches the target baseline exactly. `stamp` changes Alembic's revision marker; it does not create or alter tables.
