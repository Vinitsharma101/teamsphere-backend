from tests.conftest import login, signup


def test_signup_returns_user_and_sets_cookies(client):
    r = signup(client, "user@example.com")
    body = r.json()
    assert body["user"]["email"] == "user@example.com"
    assert body["user"]["id"] > 0
    assert "access_token" in r.cookies
    assert "refresh_token" in r.cookies


def test_signup_duplicate_email_conflicts(client):
    signup(client, "dup@example.com")
    r = client.post(
        "/api/v1/auth/signup",
        json={"name": "Other", "email": "dup@example.com", "password": "password123"},
    )
    assert r.status_code == 409


def test_signup_invalid_email_rejected(client):
    r = client.post(
        "/api/v1/auth/signup",
        json={"name": "X", "email": "not-an-email", "password": "password123"},
    )
    assert r.status_code == 422


def test_signup_short_password_rejected(client):
    r = client.post(
        "/api/v1/auth/signup",
        json={"name": "X", "email": "ok@example.com", "password": "short"},
    )
    assert r.status_code == 422


def test_login_with_valid_credentials(client):
    signup(client, "login@example.com", password="strongpass1")
    client.cookies.clear()

    r = login(client, "login@example.com", "strongpass1")
    assert r.json()["user"]["email"] == "login@example.com"
    assert "access_token" in r.cookies


def test_login_with_wrong_password_unauthorized(client):
    signup(client, "wrong@example.com")
    client.cookies.clear()

    r = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "incorrect"},
    )
    assert r.status_code == 401


def test_login_unknown_user_unauthorized(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert r.status_code == 401


def test_me_requires_authentication(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401


def test_me_returns_current_user(auth_client):
    r = auth_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_refresh_rotates_tokens(client):
    signup(client, "refresh@example.com")
    old_access = client.cookies.get("access_token")
    old_refresh = client.cookies.get("refresh_token")

    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 200
    assert client.cookies.get("access_token") != old_access
    assert client.cookies.get("refresh_token") != old_refresh


def test_refresh_without_cookie_unauthorized(client):
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


def test_refresh_with_access_token_rejected(client):
    signup(client, "swap@example.com")
    access = client.cookies.get("access_token")
    client.cookies.clear()
    client.cookies.set("refresh_token", access)
    r = client.post("/api/v1/auth/refresh")
    assert r.status_code == 401


def test_logout_clears_cookies_and_blocks_subsequent_requests(auth_client):
    r = auth_client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    auth_client.cookies.clear()

    r2 = auth_client.get("/api/v1/auth/me")
    assert r2.status_code == 401


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["database"] == "ok"
