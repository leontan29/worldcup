"""STEP-6: Auth API — register, login, logout."""
import pytest
from app import create_app
from app.db.connection import execute, query
from app.db.redis_client import get_redis

GOOD = {"username": "testauth1", "email": "testauth1@example.com", "password": "Password1!"}


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def cleanup():
    yield
    execute("DELETE FROM session_audit WHERE user_id IN (SELECT id FROM users WHERE username LIKE '_auth_%')")
    execute("DELETE FROM users WHERE username LIKE '_auth_%'")
    r = get_redis()
    for key in r.scan_iter("ratelimit:register:*"):
        r.delete(key)
    for key in r.scan_iter("ratelimit:login:*"):
        r.delete(key)


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "username": "_auth_user1", "email": "_auth1@example.com", "password": "Password1!"
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["username"] == "_auth_user1"
    assert "session_id" in resp.headers.get("Set-Cookie", "")


def test_register_creates_user_in_db(client):
    client.post("/api/auth/register", json={
        "username": "_auth_user2", "email": "_auth2@example.com", "password": "Password1!"
    })
    rows = query("SELECT username FROM users WHERE username = %s", ("_auth_user2",))
    assert rows and rows[0]["username"] == "_auth_user2"


def test_register_password_is_hashed(client):
    client.post("/api/auth/register", json={
        "username": "_auth_user3", "email": "_auth3@example.com", "password": "Password1!"
    })
    rows = query("SELECT password_hash FROM users WHERE username = %s", ("_auth_user3",))
    assert rows[0]["password_hash"] != "Password1!"


def test_register_duplicate_username_returns_409(client):
    client.post("/api/auth/register", json={
        "username": "_auth_dup", "email": "_authdup1@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/register", json={
        "username": "_auth_dup", "email": "_authdup2@example.com", "password": "Password1!"
    })
    assert resp.status_code == 409


def test_register_duplicate_email_returns_409(client):
    client.post("/api/auth/register", json={
        "username": "_auth_em1", "email": "_authsame@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/register", json={
        "username": "_auth_em2", "email": "_authsame@example.com", "password": "Password1!"
    })
    assert resp.status_code == 409


def test_register_weak_password_returns_400(client):
    resp = client.post("/api/auth/register", json={
        "username": "_auth_wp", "email": "_authwp@example.com", "password": "weak"
    })
    assert resp.status_code == 400
    assert "password" in resp.get_json()["details"]


def test_register_invalid_username_returns_400(client):
    resp = client.post("/api/auth/register", json={
        "username": "ab", "email": "_authiu@example.com", "password": "Password1!"
    })
    assert resp.status_code == 400
    assert "username" in resp.get_json()["details"]


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success_by_username(client):
    client.post("/api/auth/register", json={
        "username": "_auth_login1", "email": "_authl1@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/login", json={
        "username": "_auth_login1", "password": "Password1!"
    })
    assert resp.status_code == 200
    assert "session_id" in resp.headers.get("Set-Cookie", "")


def test_login_success_by_email(client):
    client.post("/api/auth/register", json={
        "username": "_auth_login2", "email": "_authl2@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/login", json={
        "email": "_authl2@example.com", "password": "Password1!"
    })
    assert resp.status_code == 200


def test_login_wrong_password_returns_401(client):
    client.post("/api/auth/register", json={
        "username": "_auth_login3", "email": "_authl3@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/login", json={
        "username": "_auth_login3", "password": "WrongPass1!"
    })
    assert resp.status_code == 401


def test_login_ten_failures_locks_account(client):
    client.post("/api/auth/register", json={
        "username": "_auth_lockme", "email": "_authlk@example.com", "password": "Password1!"
    })
    # Use distinct IPs for each attempt so no single IP hits the rate limit
    for i in range(10):
        client.post("/api/auth/login",
            json={"username": "_auth_lockme", "password": "WrongPass1!"},
            environ_base={"REMOTE_ADDR": f"10.0.{i}.1"},
        )
    # Check that the account is now locked (use a fresh IP to avoid rate limit)
    resp = client.post("/api/auth/login",
        json={"username": "_auth_lockme", "password": "Password1!"},
        environ_base={"REMOTE_ADDR": "10.1.0.1"},
    )
    assert resp.status_code == 423


def test_login_nonexistent_user_returns_401(client):
    resp = client.post("/api/auth/login", json={
        "username": "nobody_exists", "password": "Password1!"
    })
    assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

def test_logout_destroys_session(client):
    r = client.post("/api/auth/register", json={
        "username": "_auth_logout1", "email": "_authlo1@example.com", "password": "Password1!"
    })
    cookie = next(c for c in r.headers.getlist("Set-Cookie") if "session_id" in c)
    session_id = cookie.split("session_id=")[1].split(";")[0]

    client.post("/api/auth/logout")

    from app.auth.session import get_session
    assert get_session(session_id) is None


def test_logout_clears_cookie(client):
    client.post("/api/auth/register", json={
        "username": "_auth_logout2", "email": "_authlo2@example.com", "password": "Password1!"
    })
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "session_id=" in set_cookie
    assert "Max-Age=0" in set_cookie or "expires=" in set_cookie.lower()
