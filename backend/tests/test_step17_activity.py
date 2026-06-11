"""STEP-17: Activity Logging."""
import pytest
import bcrypt
from app import create_app
from app.auth.activity import log_activity
from app.auth.session import create_session
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
    rows = query("SELECT id FROM users WHERE username = '_act_user'")
    if rows:
        uid = rows[0]["id"]
        execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
        execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
        execute("DELETE FROM users WHERE id = %s", (uid,))
    pw_hash = bcrypt.hashpw(b"ActPass1!", bcrypt.gensalt(4)).decode()
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_act_user", "_act_user@test.com", pw_hash),
    )
    yield uid
    execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
    execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


def _login(client, user_id):
    sid = create_session(user_id, "_act_user", False, None)
    client.set_cookie("session_id", sid)
    return sid


def _logout(client):
    client.delete_cookie("session_id")


def test_log_activity_inserts_row(user):
    before = len(query("SELECT id FROM user_activity WHERE user_id = %s", (user,)))
    log_activity(user, "test_action", "127.0.0.1")
    after = len(query("SELECT id FROM user_activity WHERE user_id = %s", (user,)))
    assert after == before + 1


def test_get_activity_requires_auth(client):
    resp = client.get("/api/user/activity")
    assert resp.status_code == 401


def test_get_activity_returns_list(client, user):
    _login(client, user)
    resp = client.get("/api/user/activity")
    _logout(client)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_register_login_predict_produce_activity_rows(client, user, app):
    # clear existing activity for this user
    execute("DELETE FROM user_activity WHERE user_id = %s", (user,))

    # register via API (new temp user to trigger register log)
    rows = query("SELECT id FROM users WHERE username = '_act_reg'")
    if rows:
        old = rows[0]["id"]
        execute("DELETE FROM user_activity WHERE user_id = %s", (old,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (old,))
        execute("DELETE FROM users WHERE id = %s", (old,))

    resp = client.post("/api/auth/register", json={
        "username": "_act_reg",
        "email": "_act_reg@test.com",
        "password": "RegPass1!",
    })
    assert resp.status_code == 201
    reg_uid = resp.get_json()["id"]

    # login
    client.delete_cookie("session_id")
    resp = client.post("/api/auth/login", json={"username": "_act_reg", "password": "RegPass1!"})
    assert resp.status_code == 200

    # predict (need a scheduled match)
    scheduled = query("SELECT id FROM matches WHERE status = 'scheduled' LIMIT 1")
    if scheduled:
        mid = scheduled[0]["id"]
        resp = client.post(f"/api/predictions/{mid}", json={"home_score": 1, "away_score": 0})
        assert resp.status_code in (200, 201)

    client.delete_cookie("session_id")

    rows = query("SELECT action FROM user_activity WHERE user_id = %s ORDER BY created_at", (reg_uid,))
    actions = [r["action"] for r in rows]
    assert "register" in actions
    assert "login" in actions
    if scheduled:
        assert "predict" in actions

    # cleanup
    execute("DELETE FROM user_activity WHERE user_id = %s", (reg_uid,))
    execute("DELETE FROM predictions WHERE user_id = %s", (reg_uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (reg_uid,))
    execute("DELETE FROM users WHERE id = %s", (reg_uid,))
