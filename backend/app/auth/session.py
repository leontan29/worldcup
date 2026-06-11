import json
import uuid

from app.db.connection import execute, query
from app.db.redis_client import get_redis

_TTL = 86400        # 24 hours
_MAX_SESSIONS = 5


def _redis():
    return get_redis()


def _session_key(session_id: str) -> str:
    return f"session:{session_id}"


def _user_sessions_key(user_id: int) -> str:
    return f"user_sessions:{user_id}"


def create_session(user_id: int, username: str, is_admin: bool, favorite_team: int | None) -> str:
    session_id = str(uuid.uuid4())
    data = json.dumps({
        "user_id": user_id,
        "username": username,
        "is_admin": is_admin,
        "favorite_team": favorite_team,
    })
    r = _redis()
    r.setex(_session_key(session_id), _TTL, data)

    user_key = _user_sessions_key(user_id)
    r.rpush(user_key, session_id)

    # Evict oldest sessions beyond the limit
    overflow = r.llen(user_key) - _MAX_SESSIONS
    for _ in range(overflow):
        old_id = r.lpop(user_key)
        if old_id:
            old_id = old_id.decode() if isinstance(old_id, bytes) else old_id
            r.delete(_session_key(old_id))

    execute(
        "INSERT INTO session_audit (user_id, session_id) VALUES (%s, %s)",
        (user_id, session_id),
    )
    return session_id


def get_session(session_id: str) -> dict | None:
    r = _redis()
    raw = r.get(_session_key(session_id))
    if raw is None:
        return None
    r.expire(_session_key(session_id), _TTL)
    return json.loads(raw)


def destroy_session(session_id: str) -> None:
    r = _redis()
    raw = r.get(_session_key(session_id))
    if raw is None:
        return
    data = json.loads(raw)
    r.delete(_session_key(session_id))
    r.lrem(_user_sessions_key(data["user_id"]), 0, session_id)
    execute(
        "UPDATE session_audit SET destroyed_at = NOW() WHERE session_id = %s AND destroyed_at IS NULL",
        (session_id,),
    )


def destroy_all_sessions(user_id: int) -> None:
    r = _redis()
    user_key = _user_sessions_key(user_id)
    session_ids = [
        sid.decode() if isinstance(sid, bytes) else sid
        for sid in r.lrange(user_key, 0, -1)
    ]
    for sid in session_ids:
        r.delete(_session_key(sid))
    r.delete(user_key)
    execute(
        "UPDATE session_audit SET destroyed_at = NOW() WHERE user_id = %s AND destroyed_at IS NULL",
        (user_id,),
    )
