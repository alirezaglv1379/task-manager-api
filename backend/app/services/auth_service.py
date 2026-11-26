from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.types import utc_now
from app.models import RefreshSessionDB, UserDB


class InvalidRefreshToken(Exception):
    pass


def authenticate_user(db: Session, username: str, password: str) -> UserDB | None:
    user = db.query(UserDB).filter(UserDB.username == username).first()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def _hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_refresh_session(db: Session, user_id: int) -> str:
    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_refresh_token(raw_token)
    now = utc_now()
    session = RefreshSessionDB(
        user_id=user_id,
        token_hash=token_hash,
        family_id=secrets.token_hex(24),
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return raw_token


def rotate_refresh_session(db: Session, raw_token: str) -> tuple[str, str, int]:
    old_hash = _hash_refresh_token(raw_token)
    now = utc_now()
    current = db.query(RefreshSessionDB).filter(RefreshSessionDB.token_hash == old_hash).first()
    if current is None:
        raise InvalidRefreshToken

    if current.revoked_at is not None:
        # Reuse of an already rotated token revokes the remaining family sessions.
        db.query(RefreshSessionDB).filter(
            RefreshSessionDB.family_id == current.family_id,
            RefreshSessionDB.revoked_at.is_(None),
        ).update({RefreshSessionDB.revoked_at: now}, synchronize_session=False)
        db.commit()
        raise InvalidRefreshToken

    if current.expires_at <= now:
        current.revoked_at = now
        db.commit()
        raise InvalidRefreshToken

    # Atomic single-use transition. A concurrent request cannot rotate the same token twice.
    result = db.execute(
        update(RefreshSessionDB)
        .where(
            RefreshSessionDB.id == current.id,
            RefreshSessionDB.revoked_at.is_(None),
            RefreshSessionDB.expires_at > now,
        )
        .values(revoked_at=now)
    )
    if result.rowcount != 1:
        db.rollback()
        raise InvalidRefreshToken

    new_raw = secrets.token_urlsafe(48)
    new_hash = _hash_refresh_token(new_raw)
    new_session = RefreshSessionDB(
        user_id=current.user_id,
        token_hash=new_hash,
        family_id=current.family_id,
        created_at=now,
        expires_at=now + timedelta(days=settings.refresh_token_expire_days),
    )
    current.replaced_by_token_hash = new_hash
    db.add(new_session)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return create_access_token(current.user_id), new_raw, current.user_id


def revoke_refresh_session(db: Session, raw_token: str | None) -> None:
    if not raw_token:
        return
    token_hash = _hash_refresh_token(raw_token)
    current = db.query(RefreshSessionDB).filter(RefreshSessionDB.token_hash == token_hash).first()
    if current is None or current.revoked_at is not None:
        return
    current.revoked_at = utc_now()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
