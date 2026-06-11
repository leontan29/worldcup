from functools import wraps

from flask import g, jsonify, request

from app.auth.session import get_session

SESSION_COOKIE = "session_id"


def _load_user():
    """Validates session cookie and sets g.user. Returns error response or None."""
    session_id = request.cookies.get(SESSION_COOKIE)
    if not session_id:
        return jsonify({"error": "Authentication required"}), 401
    user = get_session(session_id)
    if not user:
        return jsonify({"error": "Session expired or invalid"}), 401
    g.user = user
    return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        err = _load_user()
        if err:
            return err
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        err = _load_user()
        if err:
            return err
        if not g.user.get("is_admin"):
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated
