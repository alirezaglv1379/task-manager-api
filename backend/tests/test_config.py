from dataclasses import replace

import pytest

from app.core.config import settings


def test_settings_reject_non_positive_token_lifetimes():
    with pytest.raises(ValueError):
        replace(settings, access_token_expire_minutes=0).validate()
    with pytest.raises(ValueError):
        replace(settings, refresh_token_expire_days=0).validate()


def test_settings_reject_invalid_rate_limits():
    with pytest.raises(ValueError):
        replace(settings, login_ip_limit=0).validate()
    with pytest.raises(ValueError):
        replace(settings, login_username_failure_limit=0).validate()
    with pytest.raises(ValueError):
        replace(settings, login_rate_window_seconds=30).validate()


def test_settings_reject_invalid_cookie_configuration():
    with pytest.raises(ValueError):
        replace(settings, cookie_samesite="invalid").validate()
    with pytest.raises(ValueError):
        replace(settings, cookie_samesite="none", cookie_secure=False).validate()


def test_production_requires_a_strong_secret():
    with pytest.raises(ValueError):
        replace(settings, environment="production", secret_key="short-secret").validate()
    with pytest.raises(ValueError):
        replace(settings, environment="production", secret_key="a" * 48).validate()
    replace(
        settings, environment="production", secret_key="a" * 48, cookie_secure=True
    ).validate()


def test_wildcard_origins_and_non_sqlite_are_rejected():
    with pytest.raises(ValueError):
        replace(settings, cors_origins=("*",)).validate()
    with pytest.raises(ValueError):
        replace(settings, database_url="postgresql://example").validate()
