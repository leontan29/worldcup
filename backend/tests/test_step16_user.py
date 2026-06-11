"""STEP-16: User Profile API."""
import pytest
import bcrypt
from app import create_app
from app.auth.session import create_session, destroy_all_sessions
from app.db.connection import execute, query


@pytest.fixture(scope="module")
def app():
    return create_app()


@pytest.fixture(scope="module")
def client(app):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def user(app):
    rows = query("SELECT id FROM users WHERE username = '_profile_user'")
    if rows:
        uid = rows[0]["id"]
        execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
        execute("DELETE FROM users WHERE id = %s", (uid,))
    pw_hash = bcrypt.hashpw(b"OldPass1!", bcrypt.gensalt(4)).decode()
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_profile_user", "_profile_user@test.com", pw_hash),
    )
    yield uid
    execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
    execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


@pytest.fixture(scope="module")
def other_user(app):
    rows = query("SELECT id FROM users WHERE username = '_profile_other'")
    if rows:
        uid = rows[0]["id"]
        execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
        execute("DELETE FROM users WHERE id = %s", (uid,))
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_profile_other", "_profile_other@test.com", "placeholder"),
    )
    yield uid
    execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


def _login(client, user_id):
    sid = create_session(user_id, "_profile_user", False, None)
    client.set_cookie("session_id", sid)
    return sid


def _logout(client):
    client.delete_cookie("session_id")


def test_get_profile_requires_auth(client):
    resp = client.get("/api/user/profile")
    assert resp.status_code == 401


def test_get_profile_returns_user(client, user):
    _login(client, user)
    resp = client.get("/api/user/profile")
    _logout(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["username"] == "_profile_user"
    assert "password_hash" not in data


def test_update_profile_email_persists(client, user):
    _login(client, user)
    resp = client.put("/api/user/profile", json={"email": "_profile_updated@test.com"})
    _logout(client)
    assert resp.status_code == 200
    rows = query("SELECT email FROM users WHERE id = %s", (user,))
    assert rows[0]["email"] == "_profile_updated@test.com"


def test_update_profile_duplicate_email_returns_409(client, user, other_user):
    _login(client, user)
    resp = client.put("/api/user/profile", json={"email": "_profile_other@test.com"})
    _logout(client)
    assert resp.status_code == 409


def test_set_favorite_team(client, user):
    _login(client, user)
    resp = client.put("/api/user/favorite-team", json={"team_id": 1})
    _logout(client)
    assert resp.status_code == 200
    rows = query("SELECT favorite_team_id FROM users WHERE id = %s", (user,))
    assert rows[0]["favorite_team_id"] == 1


def test_set_favorite_team_invalid_returns_404(client, user):
    _login(client, user)
    resp = client.put("/api/user/favorite-team", json={"team_id": 99999})
    _logout(client)
    assert resp.status_code == 404


def test_change_password_wrong_old_returns_401(client, user):
    _login(client, user)
    resp = client.post("/api/user/change-password",
                       json={"old_password": "WrongPass1!", "new_password": "NewPass1!"})
    _logout(client)
    assert resp.status_code == 401


def test_change_password_invalidates_other_sessions(client, user):
    # create a second session to verify it gets destroyed
    extra_sid = create_session(user, "_profile_user", False, None)

    _login(client, user)
    resp = client.post("/api/user/change-password",
                       json={"old_password": "OldPass1!", "new_password": "NewPass2@"})
    assert resp.status_code == 200
    # extra session should be gone
    from app.auth.session import get_session
    assert get_session(extra_sid) is None
    # response sets a new cookie
    assert "session_id" in resp.headers.get("Set-Cookie", "")
    _logout(client)
    # update stored hash for subsequent tests
    new_hash = bcrypt.hashpw(b"NewPass2@", bcrypt.gensalt(4)).decode()
    execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user))


def test_soft_delete_blocks_login(client, user, app):
    _login(client, user)
    resp = client.delete("/api/user/profile")
    assert resp.status_code == 200
    _logout(client)

    # login should fail (is_active = 0)
    rows = query("SELECT username FROM users WHERE id = %s", (user,))
    username = rows[0]["username"]
    resp = client.post("/api/auth/login",
                       json={"username": username, "password": "NewPass2@"})
    assert resp.status_code == 401

    # restore for fixture teardown
    execute("UPDATE users SET is_active = 1 WHERE id = %s", (user,))
