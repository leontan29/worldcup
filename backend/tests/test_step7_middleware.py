"""STEP-7: Auth middleware — @require_auth and @require_admin decorators."""
import pytest
from flask import g, jsonify

from app import create_app
from app.auth.middleware import require_admin, require_auth
from app.auth.session import create_session
from app.db.connection import execute


@pytest.fixture(scope="module")
def app():
    app = create_app()
    app.config["TESTING"] = True

    @app.get("/test/auth-only")
    @require_auth
    def auth_only():
        return jsonify({"user": g.user["username"]})

    @app.get("/test/admin-only")
    @require_admin
    def admin_only():
        return jsonify({"ok": True})

    return app


@pytest.fixture(scope="module")
def users(app):
    uid_user, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_mw_user", "_mw_user@example.com", "placeholder"),
    )
    uid_admin, _ = execute(
        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, 1)",
        ("_mw_admin", "_mw_admin@example.com", "placeholder"),
    )
    yield {"user": uid_user, "admin": uid_admin}
    execute("DELETE FROM session_audit WHERE user_id IN (%s, %s)", (uid_user, uid_admin))
    execute("DELETE FROM users WHERE id IN (%s, %s)", (uid_user, uid_admin))


@pytest.fixture(scope="module")
def client(app):
    with app.test_client() as c:
        yield c


# ── @require_auth ─────────────────────────────────────────────────────────────

def test_no_cookie_returns_401(client):
    resp = client.get("/test/auth-only")
    assert resp.status_code == 401


def test_invalid_session_returns_401(client):
    client.set_cookie("session_id", "not-a-real-session")
    resp = client.get("/test/auth-only")
    client.delete_cookie("session_id")
    assert resp.status_code == 401


def test_valid_session_passes_through(client, users):
    sid = create_session(users["user"], "_mw_user", False, None)
    client.set_cookie("session_id", sid)
    resp = client.get("/test/auth-only")
    client.delete_cookie("session_id")
    assert resp.status_code == 200
    assert resp.get_json()["user"] == "_mw_user"


def test_require_auth_attaches_user_to_g(client, users):
    sid = create_session(users["user"], "_mw_user", False, None)
    client.set_cookie("session_id", sid)
    resp = client.get("/test/auth-only")
    client.delete_cookie("session_id")
    assert resp.get_json()["user"] == "_mw_user"


# ── @require_admin ────────────────────────────────────────────────────────────

def test_no_cookie_on_admin_route_returns_401(client):
    resp = client.get("/test/admin-only")
    assert resp.status_code == 401


def test_non_admin_session_returns_403(client, users):
    sid = create_session(users["user"], "_mw_user", False, None)
    client.set_cookie("session_id", sid)
    resp = client.get("/test/admin-only")
    client.delete_cookie("session_id")
    assert resp.status_code == 403


def test_admin_session_passes_through(client, users):
    sid = create_session(users["admin"], "_mw_admin", True, None)
    client.set_cookie("session_id", sid)
    resp = client.get("/test/admin-only")
    client.delete_cookie("session_id")
    assert resp.status_code == 200
