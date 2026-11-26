from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import  jwt

from passlib.context import CryptContext

from app.core.config import settings

ALGORITHM = "HS256"  # Deliberately fixed; never accept an algorithm from the token header.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class InvalidAccessToken(Exception):
    pass


def get_password_hash(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Bcrypt passwords must not exceed 72 UTF-8 bytes.")
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if len(plain_password.encode("utf-8")) > 72:
        return False
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError as exc:
        raise InvalidAccessToken from exc

    if not isinstance(payload, dict):
        raise InvalidAccessToken

    ## PyJWT validates exp when present; we also require it to be present and numeric.
    exp = payload.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise InvalidAccessToken
    try:
        expires_at = datetime.fromtimestamp(float(exp), tz=timezone.utc)
    except (ValueError, OverflowError, OSError) as exc:
        raise InvalidAccessToken from exc
    if expires_at <= datetime.now(timezone.utc):
        raise InvalidAccessToken

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdecimal():
        raise InvalidAccessToken
    if int(subject) <= 0 or payload.get("type") != "access":
        raise InvalidAccessToken
    return payload
