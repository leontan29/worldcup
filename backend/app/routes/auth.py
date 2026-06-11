import os
import re
from datetime import datetime

import bcrypt
from flask import Blueprint, jsonify, make_response, request

from app.auth.activity import log_activity
from app.auth.ratelimit import check_rate_limit
from app.auth.session import create_session, destroy_session
from app.db.connection import execute, query

bp = Blueprint("auth", __name__)

SESSION_COOKIE = "session_id"
_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,50}$")
_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def _validate_register(data: dict) -> dict:
    errors = {}

    username = data.get("username", "")
    if not _USERNAME_RE.match(username):
        errors["username"] = ["Must be 3–50 characters, letters/numbers/underscore only"]

    email = data.get("email", "")
    if not _EMAIL_RE.match(email):
        errors["email"] = ["Invalid email format"]

    pw = data.get("password", "")
    pw_errors = []
    if len(pw) < 8:
        pw_errors.append("Must be at least 8 characters")
    if not re.search(r"[A-Z]", pw):
        pw_errors.append("Must contain an uppercase letter")
    if not re.search(r"[0-9]", pw):
        pw_errors.append("Must contain a number")
    if not re.search(r"[^a-zA-Z0-9]", pw):
        pw_errors.append("Must contain a special character")
    if pw_errors:
        errors["password"] = pw_errors

    return errors


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


@bp.post("/api/auth/register")
def register():
    ip = request.remote_addr
    if not check_rate_limit(f"ratelimit:register:{ip}", 5, 3600):
        return jsonify({"error": "Rate limit exceeded"}), 429

    data = request.get_json(silent=True) or {}
    errors = _validate_register(data)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    username = data["username"]
    email = data["email"].lower()
    password = data["password"]

    if query("SELECT id FROM users WHERE username = %s", (username,)):
        return jsonify({"error": "Validation failed", "details": {"username": ["Username already taken"]}}), 409
    if query("SELECT id FROM users WHERE email = %s", (email,)):
        return jsonify({"error": "Validation failed", "details": {"email": ["Email already registered"]}}), 409

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
    uid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, password_hash),
    )

    session_id = create_session(uid, username, False, None)
    log_activity(uid, "register", request.remote_addr or "")
    resp = make_response(jsonify({"id": uid, "username": username, "is_admin": False}), 201)
    return _set_cookie(resp, session_id)


@bp.post("/api/auth/login")
def login():
    ip = request.remote_addr
    if not check_rate_limit(f"ratelimit:login:{ip}", 10, 60):
        return jsonify({"error": "Rate limit exceeded"}), 429

    data = request.get_json(silent=True) or {}
    identifier = data.get("username") or data.get("email", "")
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"error": "Username/email and password required"}), 400

    rows = query(
        "SELECT * FROM users WHERE (username = %s OR email = %s) AND is_active = 1",
        (identifier, identifier),
    )
    if not rows:
        return jsonify({"error": "Invalid credentials"}), 401

    user = rows[0]

    if user["locked_until"] and user["locked_until"] > datetime.now():
        return jsonify({"error": "Account locked. Try again later."}), 423

    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        new_count = user["failed_login_count"] + 1
        if new_count >= 10:
            execute(
                "UPDATE users SET failed_login_count = %s, "
                "locked_until = DATE_ADD(NOW(), INTERVAL 15 MINUTE) WHERE id = %s",
                (new_count, user["id"]),
            )
        else:
            execute("UPDATE users SET failed_login_count = %s WHERE id = %s", (new_count, user["id"]))
        return jsonify({"error": "Invalid credentials"}), 401

    execute("UPDATE users SET failed_login_count = 0, locked_until = NULL WHERE id = %s", (user["id"],))
    session_id = create_session(user["id"], user["username"], bool(user["is_admin"]), user["favorite_team_id"])
    log_activity(user["id"], "login", request.remote_addr or "")
    resp = make_response(jsonify({"id": user["id"], "username": user["username"], "is_admin": bool(user["is_admin"])}), 200)
    return _set_cookie(resp, session_id)


@bp.post("/api/auth/logout")
def logout():
    session_id = request.cookies.get(SESSION_COOKIE)
    if session_id:
        destroy_session(session_id)
    resp = make_response(jsonify({"message": "Logged out"}), 200)
    resp.delete_cookie(SESSION_COOKIE)
    return resp
