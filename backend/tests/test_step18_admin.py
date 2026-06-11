"""STEP-18: Admin API."""
import pytest
import bcrypt
from app import create_app
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
def admin_user(app):
    rows = query("SELECT id FROM users WHERE username = '_admin_user'")
    if rows:
        uid = rows[0]["id"]
        execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
        execute("DELETE FROM users WHERE id = %s", (uid,))
    pw_hash = bcrypt.hashpw(b"AdminPass1!", bcrypt.gensalt(4)).decode()
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash, is_admin) VALUES (%s, %s, %s, 1)",
        ("_admin_user", "_admin_user@test.com", pw_hash),
    )
    yield uid
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


@pytest.fixture(scope="module")
def regular_user(app):
    rows = query("SELECT id FROM users WHERE username = '_admin_target'")
    if rows:
        uid = rows[0]["id"]
        execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
        execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
        execute("DELETE FROM users WHERE id = %s", (uid,))
    pw_hash = bcrypt.hashpw(b"TargetPass1!", bcrypt.gensalt(4)).decode()
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_admin_target", "_admin_target@test.com", pw_hash),
    )
    yield uid
    execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
    execute("DELETE FROM user_activity WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


def _login_admin(client, admin_id):
    sid = create_session(admin_id, "_admin_user", True, None)
    client.set_cookie("session_id", sid)


def _logout(client):
    client.delete_cookie("session_id")


def test_admin_requires_auth(client):
    resp = client.get("/api/admin/users")
    assert resp.status_code == 401


def test_admin_requires_admin_role(client, regular_user):
    sid = create_session(regular_user, "_admin_target", False, None)
    client.set_cookie("session_id", sid)
    resp = client.get("/api/admin/users")
    _logout(client)
    assert resp.status_code == 403


def test_list_users_returns_all(client, admin_user):
    _login_admin(client, admin_user)
    resp = client.get("/api/admin/users")
    _logout(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "password_hash" not in data[0]


def test_lock_user_blocks_login(client, admin_user, regular_user):
    _login_admin(client, admin_user)
    resp = client.post(f"/api/admin/users/{regular_user}/lock")
    _logout(client)
    assert resp.status_code == 200

    resp = client.post("/api/auth/login",
                       json={"username": "_admin_target", "password": "TargetPass1!"})
    assert resp.status_code == 423


def test_unlock_user_allows_login(client, admin_user, regular_user):
    _login_admin(client, admin_user)
    resp = client.post(f"/api/admin/users/{regular_user}/unlock")
    _logout(client)
    assert resp.status_code == 200

    resp = client.post("/api/auth/login",
                       json={"username": "_admin_target", "password": "TargetPass1!"})
    assert resp.status_code == 200
    client.delete_cookie("session_id")


def test_update_match_score(client, admin_user):
    row = query("SELECT id, status FROM matches WHERE status = 'completed' LIMIT 1")[0]
    mid = row["id"]
    original_status = row["status"]

    _login_admin(client, admin_user)
    resp = client.put(f"/api/admin/matches/{mid}/score",
                      json={"home_score": 2, "away_score": 1, "status": "completed"})
    _logout(client)
    assert resp.status_code == 200
    assert resp.get_json()["updated"] is True


def test_score_update_triggers_prediction_scoring(client, admin_user):
    scheduled = query("SELECT id FROM matches WHERE status = 'scheduled' LIMIT 1")
    if not scheduled:
        pytest.skip("no scheduled matches available")
    mid = scheduled[0]["id"]

    # create a prediction for that match
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_score_trig", "_score_trig@test.com", "placeholder"),
    )
    execute(
        "INSERT INTO predictions (user_id, match_id, home_score, away_score) VALUES (%s, %s, %s, %s)",
        (uid, mid, 1, 0),
    )

    # admin marks completed with matching score
    execute("UPDATE matches SET home_score = 1, away_score = 0 WHERE id = %s", (mid,))
    _login_admin(client, admin_user)
    resp = client.put(f"/api/admin/matches/{mid}/score",
                      json={"home_score": 1, "away_score": 0, "status": "completed"})
    _logout(client)
    assert resp.status_code == 200

    pred = query("SELECT points_earned FROM predictions WHERE user_id = %s AND match_id = %s", (uid, mid))
    assert pred[0]["points_earned"] == 3

    # cleanup
    execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))
    execute("UPDATE matches SET status = 'scheduled' WHERE id = %s", (mid,))


def test_list_sessions(client, admin_user):
    _login_admin(client, admin_user)
    resp = client.get("/api/admin/sessions")
    _logout(client)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_delete_sessions(client, admin_user, regular_user):
    create_session(regular_user, "_admin_target", False, None)
    _login_admin(client, admin_user)
    resp = client.delete(f"/api/admin/sessions/{regular_user}")
    _logout(client)
    assert resp.status_code == 200


def test_stats_returns_all_keys(client, admin_user):
    _login_admin(client, admin_user)
    resp = client.get("/api/admin/stats")
    _logout(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert "active_sessions" in data
    assert "total_users" in data
    assert "predictions_24h" in data
