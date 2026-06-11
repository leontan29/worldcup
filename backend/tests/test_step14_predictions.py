"""STEP-14: Predictions API."""
import pytest
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
def user(app):
    # pre-clean any leftover from a previously failed run
    rows = query("SELECT id FROM users WHERE username = '_pred_user'")
    if rows:
        stale = rows[0]["id"]
        execute("DELETE FROM predictions WHERE user_id = %s", (stale,))
        execute("DELETE FROM session_audit WHERE user_id = %s", (stale,))
        execute("DELETE FROM users WHERE id = %s", (stale,))
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_pred_user", "_pred_user@test.com", "placeholder"),
    )
    yield uid
    execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


@pytest.fixture(scope="module")
def scheduled_match_id():
    rows = query("SELECT id FROM matches WHERE status = 'scheduled' LIMIT 1")
    if rows:
        yield rows[0]["id"]
        return
    execute("UPDATE matches SET status = 'scheduled' WHERE id = 1")
    yield 1
    execute("UPDATE matches SET status = 'completed' WHERE id = 1")


@pytest.fixture(scope="module")
def completed_match_id():
    rows = query("SELECT id FROM matches WHERE status = 'completed' LIMIT 1")
    return rows[0]["id"]


def _login(client, user_id):
    sid = create_session(user_id, "_pred_user", False, None)
    client.set_cookie("session_id", sid)
    return sid


def _logout(client):
    client.delete_cookie("session_id")


def test_predict_no_auth_returns_401(client, scheduled_match_id):
    resp = client.post(f"/api/predictions/{scheduled_match_id}",
                       json={"home_score": 1, "away_score": 0})
    assert resp.status_code == 401


def test_predict_on_completed_match_returns_400(client, user, completed_match_id):
    _login(client, user)
    resp = client.post(f"/api/predictions/{completed_match_id}",
                       json={"home_score": 1, "away_score": 0})
    _logout(client)
    assert resp.status_code == 400


def test_predict_on_scheduled_match_returns_201(client, user, scheduled_match_id):
    _login(client, user)
    resp = client.post(f"/api/predictions/{scheduled_match_id}",
                       json={"home_score": 2, "away_score": 1})
    _logout(client)
    assert resp.status_code == 201
    assert resp.get_json()["created"] is True


def test_update_prediction_returns_200(client, user, scheduled_match_id):
    _login(client, user)
    resp = client.post(f"/api/predictions/{scheduled_match_id}",
                       json={"home_score": 3, "away_score": 0})
    _logout(client)
    assert resp.status_code == 200
    assert resp.get_json()["updated"] is True


def test_my_predictions_returns_list(client, user):
    _login(client, user)
    resp = client.get("/api/user/predictions")
    _logout(client)
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_leaderboard_is_sorted(client):
    resp = client.get("/api/predictions/leaderboard")
    assert resp.status_code == 200
    data = resp.get_json()
    points = [r["total_points"] for r in data]
    assert points == sorted(points, reverse=True)
