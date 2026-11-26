from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import StatementError

from app.core.security import (
    InvalidAccessToken,
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.db.types import UTCDateTime
from sqlalchemy import Column, Integer, Table, MetaData, insert, select


def test_access_token_contains_required_claims():
    token = create_access_token(7)
    payload = decode_access_token(token)
    assert payload["sub"] == "7"
    assert payload["type"] == "access"
    assert "exp" in payload


def test_access_token_wrong_type_is_rejected():
    import jwt
    from app.core.config import settings

    token = jwt.encode(
        {
            "sub": "7",
            "type": "refresh",
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)


def test_bcrypt_password_hash_and_72_byte_limit():
    password = "StrongPass123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)
    with pytest.raises(ValueError):
        get_password_hash("é" * 40)  # 80 UTF-8 bytes


def test_utc_datetime_round_trip_and_naive_rejection(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'utc.db'}")
    metadata = MetaData()
    table = Table(
        "dates", metadata,
        Column("id", Integer, primary_key=True),
        Column("created_at", UTCDateTime(), nullable=False),
    )
    metadata.create_all(engine)
    original = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=3)))
    with engine.begin() as connection:
        connection.execute(insert(table).values(created_at=original))
        stored = connection.execute(select(table.c.created_at)).scalar_one()
    assert stored.tzinfo == timezone.utc
    assert stored.hour == 9

    with pytest.raises(StatementError):
        with engine.begin() as connection:
            connection.execute(insert(table).values(created_at=datetime(2026, 1, 1, 12, 0)))
    engine.dispose()


def test_access_token_requires_exp_sub_and_access_type():
    import jwt
    from app.core.config import settings

    future = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())
    payloads = [
        {"sub": "7", "type": "access"},
        {"type": "access", "exp": future},
        {"sub": "0", "type": "access", "exp": future},
        {"sub": "abc", "type": "access", "exp": future},
        {"sub": "7", "exp": future},
    ]
    for payload in payloads:
        token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
        with pytest.raises(InvalidAccessToken):
            decode_access_token(token)


def test_expired_access_token_is_rejected():
    import jwt
    from app.core.config import settings

    token = jwt.encode(
        {
            "sub": "7",
            "type": "access",
            "exp": int((datetime.now(timezone.utc) - timedelta(minutes=1)).timestamp()),
        },
        settings.secret_key,
        algorithm="HS256",
    )
    with pytest.raises(InvalidAccessToken):
        decode_access_token(token)
