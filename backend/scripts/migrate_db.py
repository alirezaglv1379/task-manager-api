from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings, sqlite_database_path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REQUIRED_LEGACY_COLUMNS = {
    "users": {"id", "username", "hashed_password"},
    "tasks": {"id", "title", "description", "is_completed", "created_at", "owner_id"},
}


def _alembic_config() -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
    return config


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _columns(connection: sqlite3.Connection, table: str) -> set[str]:
    return {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}


def _backup(database_path: Path) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup_name = f"{database_path.stem}.backup-{timestamp}{database_path.suffix}"
    backup_path = database_path.with_name(backup_name)
    source = sqlite3.connect(str(database_path))
    destination = sqlite3.connect(str(backup_path))
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()
    return backup_path


def main() -> None:
    database_path = sqlite_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    config = _alembic_config()

    if not database_path.exists() or database_path.stat().st_size == 0:
        command.upgrade(config, "head")
        print(f"Database initialized: {database_path}")
        return

    connection = sqlite3.connect(str(database_path))
    try:
        existing_tables = _tables(connection)
        if not existing_tables:
            connection.close()
            command.upgrade(config, "head")
            print(f"Database initialized: {database_path}")
            return

        version_rows = []
        if "alembic_version" in existing_tables:
            version_rows = connection.execute("SELECT version_num FROM alembic_version").fetchall()

        if version_rows:
            connection.close()
            backup_path = _backup(database_path)
            command.upgrade(config, "head")
            print(f"Backup created: {backup_path}")
            print("Database upgraded to the latest migration.")
            return

        core_tables = {"users", "tasks"}
        if not core_tables.issubset(existing_tables):
            # An empty Alembic marker is safe to initialize only when there are no app tables.
            if existing_tables.issubset({"alembic_version"}):
                connection.close()
                command.upgrade(config, "head")
                print(f"Database initialized: {database_path}")
                return
            raise RuntimeError(
                "Existing SQLite database has an unrecognized or partial schema. "
                "No changes were made."
            )
        for table, required in REQUIRED_LEGACY_COLUMNS.items():
            missing = required - _columns(connection, table)
            if missing:
                raise RuntimeError(
                    f"Legacy table '{table}' is missing columns: {', '.join(sorted(missing))}. "
                    "No changes were made."
                )
    finally:
        try:
            connection.close()
        except Exception:
            pass

    backup_path = _backup(database_path)
    # stamp only after verifying that the existing schema matches the baseline migration.
    command.stamp(config, "0001_initial")
    command.upgrade(config, "head")
    print(f"Verified legacy database and created backup: {backup_path}")
    print("Legacy data preserved; new migrations applied.")


if __name__ == "__main__":
    main()
