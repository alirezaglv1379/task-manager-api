from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load a local .env when present. Environment variables always take precedence.
load_dotenv()


def _csv(value: str | None, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    if not value:
        return default
    return tuple(item.strip().rstrip("/") for item in value.split(",") if item.strip())


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Task Manager API")
    app_version: str = os.getenv("APP_VERSION", "2.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development").lower()
    secret_key: str = os.getenv(
        "SECRET_KEY", "development-only-secret-change-before-deployment-32-bytes"
    )
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./task_manager.db")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    refresh_cookie_name: str = os.getenv("REFRESH_COOKIE_NAME", "task_manager_refresh")
    cookie_secure: bool = _bool(
        os.getenv("COOKIE_SECURE"), os.getenv("ENVIRONMENT", "development").lower() == "production"
    )
    cookie_samesite: str = os.getenv("COOKIE_SAMESITE", "lax").lower()
    cookie_domain: str | None = os.getenv("COOKIE_DOMAIN") or None
    cors_origins: tuple[str, ...] = _csv(
        os.getenv("CORS_ORIGINS"),
        ("http://localhost:5173", "http://127.0.0.1:5173"),
    )
    csrf_trusted_origins: tuple[str, ...] = _csv(
        os.getenv("CSRF_TRUSTED_ORIGINS"),
        (
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ),
    )
    login_ip_limit: int = int(os.getenv("LOGIN_IP_LIMIT", "20"))
    login_username_failure_limit: int = int(os.getenv("LOGIN_USERNAME_FAILURE_LIMIT", "5"))
    login_rate_window_seconds: int = int(os.getenv("LOGIN_RATE_WINDOW_SECONDS", "900"))
    trusted_proxy_ips: tuple[str, ...] = _csv(os.getenv("TRUSTED_PROXY_IPS"))

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate(self) -> None:
        if self.access_token_expire_minutes <= 0 or self.refresh_token_expire_days <= 0:
            raise ValueError("Token lifetimes must be positive.")
        if self.login_ip_limit < 1 or self.login_username_failure_limit < 1:
            raise ValueError("Login rate limits must be positive.")
        if self.login_rate_window_seconds < 60:
            raise ValueError("LOGIN_RATE_WINDOW_SECONDS must be at least 60.")
        if self.cookie_samesite not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be lax, strict, or none.")
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError("SameSite=None requires COOKIE_SECURE=true.")
        weak_secret = (
            self.secret_key.startswith("development-only-")
            or "replace-with" in self.secret_key.lower()
            or len(self.secret_key.encode()) < 32
        )
        if self.is_production and weak_secret:
            raise ValueError("Set a strong SECRET_KEY (at least 32 bytes) in production.")
        if self.is_production and not self.cookie_secure:
            raise ValueError("COOKIE_SECURE must be true in production.")
        if "*" in self.cors_origins or "*" in self.csrf_trusted_origins:
            raise ValueError("Wildcard origins are not allowed for this application.")
        if not self.database_url.startswith("sqlite:"):
            raise ValueError("This release is configured for SQLite only.")


settings = Settings()
settings.validate()


def sqlite_database_path(database_url: str | None = None) -> Path:
    """Resolve a SQLite URL to a filesystem path for backup/migration tooling."""
    url = database_url or settings.database_url
    prefix = "sqlite:///"
    if not url.startswith(prefix):
        raise ValueError("Only file-backed SQLite URLs are supported by this helper.")
    raw_path = url[len(prefix) :]
    if raw_path in {":memory:", ""}:
        raise ValueError("A file-backed SQLite database is required for migration tooling.")
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else Path.cwd() / path
