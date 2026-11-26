from __future__ import annotations

import os
import sqlite3
import subprocess
from datetime import timezone
import sys
from pathlib import Path


def test_fresh_database_migrates_to_head(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    database = tmp_path / "fresh.db"
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database}"
    env["PYTHONPATH"] = str(backend)
    subprocess.run(
        [sys.executable, "-m", "scripts.migrate_db"],
        cwd=backend, env=env, check=True, capture_output=True, text=True
    )

    connection = sqlite3.connect(database)
    try:
        version = connection.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert version == "0003_task_indexes"
        assert {"users", "tasks", "refresh_sessions", "login_rate_limits"}.issubset(tables)
    finally:
        connection.close()


def test_legacy_database_is_backed_up_and_data_is_preserved(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    database = tmp_path / "legacy.db"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE users (id INTEGER NOT NULL PRIMARY KEY, "
        "username VARCHAR NOT NULL UNIQUE, hashed_password VARCHAR NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE tasks (id INTEGER NOT NULL PRIMARY KEY, title VARCHAR NOT NULL, "
        "description VARCHAR, is_completed BOOLEAN, created_at DATETIME NOT NULL, "
        "owner_id INTEGER NOT NULL, FOREIGN KEY(owner_id) REFERENCES users(id))"
    )
    connection.execute("CREATE INDEX ix_users_id ON users (id)")
    connection.execute("CREATE INDEX ix_tasks_id ON tasks (id)")
    connection.execute(
        "INSERT INTO users (id, username, hashed_password) "
        "VALUES (1, 'legacy-user', 'legacy-hash')"
    )
    connection.execute(
        "INSERT INTO tasks (id, title, description, is_completed, created_at, owner_id) "
        "VALUES (1, 'legacy task', 'keep me', 0, '2026-11-25 10:30:00', 1)"
    )
    connection.commit()
    connection.close()

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{database}"
    env["PYTHONPATH"] = str(backend)
    subprocess.run(
        [sys.executable, "-m", "scripts.migrate_db"],
        cwd=backend, env=env, check=True, capture_output=True, text=True
    )

    connection = sqlite3.connect(database)
    try:
        username = connection.execute(
            "SELECT username FROM users WHERE id=1"
        ).fetchone()[0]
        assert username == "legacy-user"
        task = connection.execute(
            "SELECT title, description, created_at FROM tasks WHERE id=1"
        ).fetchone()
        assert task == (
            "legacy task", "keep me", "2026-11-25 10:30:00"
        )
        version = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
        assert version == "0003_task_indexes"
    finally:
        connection.close()
    backups = list(tmp_path.glob("legacy.backup-*.db"))
    assert len(backups) == 1

    # The legacy naive timestamp is interpreted as UTC by the SQLAlchemy type.
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models import TaskDB

    engine = create_engine(f"sqlite:///{database}")
    with Session(engine) as db:
        migrated_task = db.query(TaskDB).filter(TaskDB.id == 1).one()
        assert migrated_task.created_at.tzinfo == timezone.utc
        assert migrated_task.created_at.hour == 10
    engine.dispose()
