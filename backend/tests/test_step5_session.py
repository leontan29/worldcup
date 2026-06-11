"""STEP-5: Redis session layer."""
import time
import pytest
from app.auth.session import create_session, get_session, destroy_session, destroy_all_sessions
from app.db.connection import query, execute

@pytest.fixture(scope="module")
def test_user():
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_session_test_user", "_session_test@example.com", "placeholder"),
    )
    yield uid
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
    execute("DELETE FROM users WHERE id = %s", (uid,))


@pytest.fixture(autouse=True)
def cleanup(redis_client, test_user):
    yield
    uid = test_user
    for key in redis_client.scan_iter(b"session:*"):
        raw = redis_client.get(key)
        if raw and f'"user_id": {uid}'.encode() in raw:
            redis_client.delete(key)
    redis_client.delete(f"user_sessions:{uid}")
    execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))


def test_create_returns_uuid_string(test_user):
    sid = create_session(test_user, "testuser", False, None)
    assert isinstance(sid, str) and len(sid) == 36


def test_get_session_returns_correct_data(test_user):
    sid = create_session(test_user, "testuser", True, 5)
    data = get_session(sid)
    assert data["user_id"] == test_user
    assert data["username"] == "testuser"
    assert data["is_admin"] is True
    assert data["favorite_team"] == 5


def test_get_session_missing_returns_none():
    assert get_session("00000000-0000-0000-0000-000000000000") is None


def test_destroy_session_removes_from_redis(redis_client, test_user):
    sid = create_session(test_user, "testuser", False, None)
    destroy_session(sid)
    assert get_session(sid) is None
    assert redis_client.lpos(f"user_sessions:{test_user}", sid) is None


def test_destroy_session_marks_audit_record(test_user):
    sid = create_session(test_user, "testuser", False, None)
    destroy_session(sid)
    rows = query(
        "SELECT destroyed_at FROM session_audit WHERE session_id = %s", (sid,)
    )
    assert rows and rows[0]["destroyed_at"] is not None


def test_get_session_refreshes_ttl(redis_client, test_user):
    sid = create_session(test_user, "testuser", False, None)
    key = f"session:{sid}"
    redis_client.expire(key, 100)
    get_session(sid)
    ttl = redis_client.ttl(key)
    assert ttl > 100


def test_sixth_session_evicts_oldest(redis_client, test_user):
    sids = [create_session(test_user, "testuser", False, None) for _ in range(6)]
    assert get_session(sids[0]) is None
    for sid in sids[1:]:
        assert get_session(sid) is not None


def test_user_sessions_capped_at_five(redis_client, test_user):
    for _ in range(7):
        create_session(test_user, "testuser", False, None)
    count = redis_client.llen(f"user_sessions:{test_user}")
    assert count == 5


def test_destroy_all_sessions(redis_client, test_user):
    sids = [create_session(test_user, "testuser", False, None) for _ in range(3)]
    destroy_all_sessions(test_user)
    for sid in sids:
        assert get_session(sid) is None
    assert redis_client.llen(f"user_sessions:{test_user}") == 0


def test_destroy_all_sessions_marks_all_audit_records(test_user):
    sids = [create_session(test_user, "testuser", False, None) for _ in range(3)]
    destroy_all_sessions(test_user)
    rows = query(
        "SELECT COUNT(*) AS n FROM session_audit "
        "WHERE user_id = %s AND destroyed_at IS NOT NULL",
        (test_user,),
    )
    assert rows[0]["n"] == 3
