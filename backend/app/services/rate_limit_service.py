from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import LoginRateLimitDB


def _key_hash(scope: str, value: str) -> str:
    message = f"{scope}:{value.strip().lower()}".encode("utf-8")
    return hmac.new(settings.secret_key.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _window(now: datetime | None = None) -> tuple[int, datetime, int]:
    now = now or datetime.now(timezone.utc)
    timestamp = int(now.timestamp())
    start = timestamp - (timestamp % settings.login_rate_window_seconds)
    retry_after = max(1, start + settings.login_rate_window_seconds - timestamp)
    return start, now, retry_after


def _cleanup(db: Session, now: datetime) -> None:
    # Keep only a small safety margin of expired fixed-window counters.
    cutoff = now - timedelta(seconds=settings.login_rate_window_seconds * 2)
    db.execute(delete(LoginRateLimitDB).where(LoginRateLimitDB.expires_at < cutoff))


def _current_count(db: Session, scope: str, key_hash: str, window_start: int) -> int:
    row = db.execute(
        select(LoginRateLimitDB.count).where(
            LoginRateLimitDB.scope == scope,
            LoginRateLimitDB.key_hash == key_hash,
            LoginRateLimitDB.window_start == window_start,
        )
    ).scalar_one_or_none()
    return int(row or 0)


def _increment(db: Session, scope: str, key_hash: str, window_start: int) -> int:
    expires_at = datetime.fromtimestamp(
        window_start + settings.login_rate_window_seconds, tz=timezone.utc
    )
    statement = sqlite_insert(LoginRateLimitDB).values(
        scope=scope,
        key_hash=key_hash,
        window_start=window_start,
        count=1,
        expires_at=expires_at,
    )
    statement = statement.on_conflict_do_update(
        index_elements=["scope", "key_hash", "window_start"],
        set_={"count": LoginRateLimitDB.count + 1},
    ).returning(LoginRateLimitDB.count)
    count = int(db.execute(statement).scalar_one())
    db.commit()
    return count


def enforce_ip_limit(db: Session, ip_address: str, now: datetime | None = None) -> None:
    window_start, current, retry_after = _window(now)
    key = _key_hash("ip", ip_address or "unknown")
    try:
        _cleanup(db, current)
        count = _increment(db, "ip", key, window_start)
    except Exception:
        db.rollback()
        raise
    if count > settings.login_ip_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "تعداد درخواست‌های ورود از این نشانی بیش از حد مجاز است. "
                "کمی بعد دوباره تلاش کنید."
            ),
            headers={"Retry-After": str(retry_after)},
        )


def enforce_username_failure_limit(db: Session, username: str, now: datetime | None = None) -> None:
    window_start, _current, retry_after = _window(now)
    key = _key_hash("username", username)
    count = _current_count(db, "username", key, window_start)
    if count >= settings.login_username_failure_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="تلاش‌های ناموفق این حساب موقتاً به سقف مجاز رسیده است. بعداً دوباره تلاش کنید.",
            headers={"Retry-After": str(retry_after)},
        )


def record_failed_username(db: Session, username: str, now: datetime | None = None) -> None:
    window_start, current, _retry_after = _window(now)
    key = _key_hash("username", username)
    try:
        _cleanup(db, current)
        _increment(db, "username", key, window_start)
    except Exception:
        db.rollback()
        raise


def clear_username_failures(db: Session, username: str) -> None:
    key = _key_hash("username", username)
    try:
        db.execute(
            delete(LoginRateLimitDB).where(
                LoginRateLimitDB.scope == "username",
                LoginRateLimitDB.key_hash == key,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise


def resolve_client_ip(request) -> str:
    remote = request.client.host if request.client else "unknown"
    # Forwarded headers are accepted only when the direct peer is explicitly trusted.
    if remote in settings.trusted_proxy_ips:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first
    return remote
