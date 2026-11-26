from app.core.config import settings
from tests.conftest import auth_headers, login, signup


def test_signup_login_and_me(client):
    created = signup(client)
    assert created.status_code == 200
    assert set(created.json()) == {"id", "username"}

    headers = auth_headers(client)
    me = client.get("/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json() == created.json()
    assert "hashed_password" not in me.json()


def test_duplicate_username_returns_409(client):
    assert signup(client).status_code == 200
    response = signup(client)
    assert response.status_code == 409


def test_auth_required_and_invalid_token(client):
    missing = client.get("/users/me")
    assert missing.status_code == 401
    assert missing.headers.get("www-authenticate") == "Bearer"

    invalid = client.get("/users/me", headers={"Authorization": "Bearer not-a-token"})
    assert invalid.status_code == 401


def test_login_sets_httponly_refresh_cookie(client):
    signup(client)
    response = login(client)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    cookie = response.cookies.get(settings.refresh_cookie_name)
    assert cookie
    set_cookie = response.headers.get("set-cookie", "").lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_refresh_rotates_cookie_and_old_token_is_rejected(client):
    signup(client)
    first = login(client)
    old_refresh = first.cookies.get(settings.refresh_cookie_name)
    assert old_refresh

    refreshed = client.post("/auth/refresh", headers={"Origin": "http://testserver"})
    assert refreshed.status_code == 200, refreshed.text
    new_refresh = refreshed.cookies.get(settings.refresh_cookie_name)
    assert new_refresh and new_refresh != old_refresh

    client.cookies.set(
    settings.refresh_cookie_name,
    old_refresh,
    domain="testserver.local",
    path="/",
    )

    reused = client.post(
    "/auth/refresh",
    headers={"Origin": "http://testserver"},
    )
    reused = client.post(
    "/auth/refresh",
    headers={"Origin": "http://testserver"}
    )

    cookie_header = reused.request.headers.get("cookie", "")
    print(
    "SENT COOKIE NAMES:",
    [part.split("=", 1)[0].strip() for part in cookie_header.split(";") if part]
    )
    assert reused.status_code == 401
    assert "max-age=0" in reused.headers.get("set-cookie", "").lower()

    # Reuse detection revokes the rotated family, so the newest token also fails.
    client.cookies.set(settings.refresh_cookie_name, new_refresh)
    family_revoked = client.post("/auth/refresh", headers={"Origin": "http://testserver"})
    assert family_revoked.status_code == 401


def test_refresh_requires_trusted_origin(client):
    signup(client)
    login(client)
    response = client.post("/auth/refresh", headers={"Origin": "https://evil.example"})
    assert response.status_code == 403


def test_logout_revokes_session_and_clears_cookie(client):
    signup(client)
    login_response = login(client)
    refresh_token = login_response.cookies.get(settings.refresh_cookie_name)
    response = client.post("/auth/logout", headers={"Origin": "http://testserver"})
    assert response.status_code == 204
    assert "max-age=0" in response.headers.get("set-cookie", "").lower()

    client.cookies.set(settings.refresh_cookie_name, refresh_token)
    after_logout = client.post("/auth/refresh", headers={"Origin": "http://testserver"})
    assert after_logout.status_code == 401


def test_username_rate_limit_after_five_failures(client):
    signup(client)
    for _ in range(settings.login_username_failure_limit):
        response = login(client, password="WrongPassword123")
        assert response.status_code == 401
    blocked = login(client, password="WrongPassword123")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_ip_rate_limit_counts_login_requests(client):
    # Different usernames avoid triggering the per-username failed-attempt limit.
    for index in range(settings.login_ip_limit):
        response = login(client, username=f"unknown{index}", password="WrongPassword123")
        assert response.status_code == 401
    blocked = login(client, username="another-unknown", password="WrongPassword123")
    assert blocked.status_code == 429
