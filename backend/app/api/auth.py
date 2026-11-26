from __future__ import annotations

import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.models import UserDB
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import (
    InvalidRefreshToken,
    authenticate_user,
    create_refresh_session,
    revoke_refresh_session,
    rotate_refresh_session,
)
from app.services.rate_limit_service import (
    clear_username_failures,
    enforce_ip_limit,
    enforce_username_failure_limit,
    record_failed_username,
    resolve_client_ip,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Authentication"])


def _set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def _require_csrf_origin(request: Request) -> None:
    origin = request.headers.get("origin", "").rstrip("/")
    if not origin or origin not in settings.csrf_trusted_origins:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="درخواست از مبدأ مجاز ارسال نشده است.",
        )


@router.post("/signup", response_model=UserResponse)
def signup(user_new: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(UserDB).filter(UserDB.username == user_new.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="این نام کاربری قبلاً ثبت شده است.")

    user = UserDB(username=user_new.username, hashed_password=get_password_hash(user_new.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="این نام کاربری قبلاً ثبت شده است.") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("User registration failed")
        raise HTTPException(status_code=500, detail="خطا در ذخیره اطلاعات.") from exc
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    response: Response,
    user_form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    enforce_ip_limit(db, resolve_client_ip(request))
    enforce_username_failure_limit(db, user_form.username)

    user = authenticate_user(db, user_form.username, user_form.password)
    if user is None:
        record_failed_username(db, user_form.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    clear_username_failures(db, user_form.username)
    access_token = create_access_token(
        user.id, timedelta(minutes=settings.access_token_expire_minutes)
    )
    try:
        refresh_token = create_refresh_session(db, user.id)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Could not create refresh session")
        raise HTTPException(status_code=500, detail="امکان ایجاد نشست وجود ندارد.") from exc
    _set_refresh_cookie(response, refresh_token)
    return Token(access_token=access_token)


@router.post("/auth/refresh", response_model=Token)
def refresh(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    _require_csrf_origin(request)
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        error_response = JSONResponse(
            status_code=401,
            content={"detail": "نشست منقضی شده است. دوباره وارد شوید."},
            headers={"WWW-Authenticate": "Bearer"},
        )
        _clear_refresh_cookie(error_response)
        return error_response
    try:
        access_token, new_refresh_token, _user_id = rotate_refresh_session(db, raw_token)
    except InvalidRefreshToken:
        error_response = JSONResponse(
            status_code=401,
            content={"detail": "نشست معتبر نیست یا منقضی شده است. دوباره وارد شوید."},
            headers={"WWW-Authenticate": "Bearer"},
        )
        _clear_refresh_cookie(error_response)
        return error_response
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Refresh token rotation failed")
        raise HTTPException(status_code=500, detail="خطا در تمدید نشست.") from exc
    _set_refresh_cookie(response, new_refresh_token)
    return Token(access_token=access_token)


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    _require_csrf_origin(request)
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    try:
        revoke_refresh_session(db, raw_token)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Logout session revocation failed")
        raise HTTPException(status_code=500, detail="خطا در خروج از حساب.") from exc
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
