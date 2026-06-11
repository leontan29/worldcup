import os
import re

import bcrypt
from flask import Blueprint, g, jsonify, make_response, request

from app.auth.middleware import require_auth
from app.auth.session import create_session, destroy_all_sessions
from app.db.connection import execute, query

bp = Blueprint("user", __name__)

SESSION_COOKIE = "session_id"
_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def _set_cookie(response, session_id: str):
    response.set_cookie(
        SESSION_COOKIE,
        session_id,
        httponly=True,
        samesite="Lax",
        secure=_SECURE,
        max_age=86400,
    )
    return response


@bp.get("/api/user/profile")
@require_auth
def get_profile():
    rows = query(
        "SELECT id, username, email, is_admin, favorite_team_id, created_at FROM users WHERE id = %s",
        (g.user["user_id"],),
    )
    if not rows:
        return jsonify({"error": "User not found"}), 404
    u = rows[0]
    u["created_at"] = u["created_at"].isoformat() if u["created_at"] else None
    u["is_admin"] = bool(u["is_admin"])
    return jsonify(u), 200


@bp.put("/api/user/profile")
@require_auth
def update_profile():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    if not email or not _EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400

    existing = query(
        "SELECT id FROM users WHERE email = %s AND id != %s",
        (email.lower(), g.user["user_id"]),
    )
    if existing:
        return jsonify({"error": "Email already in use"}), 409

    execute(
        "UPDATE users SET email = %s WHERE id = %s",
        (email.lower(), g.user["user_id"]),
    )
    return jsonify({"updated": True}), 200


@bp.put("/api/user/favorite-team")
@require_auth
def set_favorite_team():
    data = request.get_json(silent=True) or {}
    team_id = data.get("team_id")
    if team_id is None:
        return jsonify({"error": "team_id required"}), 400

    if not query("SELECT id FROM teams WHERE id = %s", (team_id,)):
        return jsonify({"error": "Team not found"}), 404

    execute(
        "UPDATE users SET favorite_team_id = %s WHERE id = %s",
        (team_id, g.user["user_id"]),
    )
    return jsonify({"updated": True}), 200


@bp.post("/api/user/change-password")
@require_auth
def change_password():
    data = request.get_json(silent=True) or {}
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")

    if not old_pw or not new_pw:
        return jsonify({"error": "old_password and new_password required"}), 400

    pw_errors = []
    if len(new_pw) < 8:
        pw_errors.append("Must be at least 8 characters")
    if not re.search(r"[A-Z]", new_pw):
        pw_errors.append("Must contain an uppercase letter")
    if not re.search(r"[0-9]", new_pw):
        pw_errors.append("Must contain a number")
    if not re.search(r"[^a-zA-Z0-9]", new_pw):
        pw_errors.append("Must contain a special character")
    if pw_errors:
        return jsonify({"error": "Validation failed", "details": {"new_password": pw_errors}}), 400

    rows = query("SELECT password_hash, username, is_admin, favorite_team_id FROM users WHERE id = %s", (g.user["user_id"],))
    if not rows:
        return jsonify({"error": "User not found"}), 404
    user = rows[0]

    if not bcrypt.checkpw(old_pw.encode(), user["password_hash"].encode()):
        return jsonify({"error": "Current password is incorrect"}), 401

    new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt(12)).decode()
    execute("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, g.user["user_id"]))

    destroy_all_sessions(g.user["user_id"])
    new_sid = create_session(
        g.user["user_id"],
        user["username"],
        bool(user["is_admin"]),
        user["favorite_team_id"],
    )
    resp = make_response(jsonify({"updated": True}), 200)
    return _set_cookie(resp, new_sid)


@bp.delete("/api/user/profile")
@require_auth
def delete_profile():
    execute("UPDATE users SET is_active = 0 WHERE id = %s", (g.user["user_id"],))
    destroy_all_sessions(g.user["user_id"])
    resp = make_response(jsonify({"deleted": True}), 200)
    resp.delete_cookie(SESSION_COOKIE)
    return resp
