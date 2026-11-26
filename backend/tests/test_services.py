from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.db.types import utc_now
from app.models import RefreshSessionDB, UserDB
from app.services.auth_service import (
    InvalidRefreshToken,
    create_refresh_session,
    revoke_refresh_session,
    rotate_refresh_session,
)
from app.services.rate_limit_service import (
    clear_username_failures,
    enforce_username_failure_limit,
    record_failed_username,
)


def _make_user(db_session_factory):
    db = db_session_factory()
    user = UserDB(username="service-user", hashed_password="test-hash")
    db.add(user)
    db.commit()
    db.refresh(user)
    return db, user


def test_refresh_session_rotation_and_reuse_revokes_family(db_session_factory):
    db, user = _make_user(db_session_factory)
    old_raw = create_refresh_session(db, user.id)
    access, new_raw, returned_user_id = rotate_refresh_session(db, old_raw)
    assert access
    assert new_raw != old_raw
    assert returned_user_id == user.id

    with pytest.raises(InvalidRefreshToken):
        rotate_refresh_session(db, old_raw)
    new_hash_session = db.query(RefreshSessionDB).filter(RefreshSessionDB.user_id == user.id).all()
    assert len(new_hash_session) == 2
    assert all(item.revoked_at is not None for item in new_hash_session)
    db.close()


def test_expired_and_unknown_refresh_tokens_are_rejected(db_session_factory):
    db, user = _make_user(db_session_factory)
    with pytest.raises(InvalidRefreshToken):
        rotate_refresh_session(db, "unknown-refresh-token")

    from app.services.auth_service import _hash_refresh_token
    expired_raw = "expired-refresh-token"
    db.add(RefreshSessionDB(
        user_id=user.id,
        token_hash=_hash_refresh_token(expired_raw),
        family_id="expired-family",
        created_at=utc_now() - timedelta(days=9),
        expires_at=utc_now() - timedelta(seconds=1),
    ))
    db.commit()
    with pytest.raises(InvalidRefreshToken):
        rotate_refresh_session(db, expired_raw)
    db.close()


def test_revoke_refresh_session_is_idempotent(db_session_factory):
    db, user = _make_user(db_session_factory)
    revoke_refresh_session(db, None)
    revoke_refresh_session(db, "not-found")
    raw = create_refresh_session(db, user.id)
    revoke_refresh_session(db, raw)
    revoke_refresh_session(db, raw)
    session = db.query(RefreshSessionDB).filter(RefreshSessionDB.user_id == user.id).one()
    assert session.revoked_at is not None
    db.close()


def test_username_rate_limit_can_be_cleared(db_session_factory):
    db, _user = _make_user(db_session_factory)
    for _ in range(5):
        record_failed_username(db, "rate-user")
    with pytest.raises(HTTPException) as blocked:
        enforce_username_failure_limit(db, "rate-user")
    assert blocked.value.status_code == 429
    clear_username_failures(db, "rate-user")
    enforce_username_failure_limit(db, "rate-user")
    db.close()
