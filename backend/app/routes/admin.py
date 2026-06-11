from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.auth.middleware import require_admin
from app.auth.session import destroy_all_sessions
from app.db.connection import execute, query
from app.db.scoring import score_match
from app.db.redis_client import get_redis

bp = Blueprint("admin", __name__)


@bp.put("/api/admin/matches/<int:match_id>/score")
@require_admin
def update_match_score(match_id):
    rows = query("SELECT id, status FROM matches WHERE id = %s", (match_id,))
    if not rows:
        return jsonify({"error": "Match not found"}), 404

    data = request.get_json(silent=True) or {}
    home_score = data.get("home_score")
    away_score = data.get("away_score")
    status = data.get("status")

    valid_statuses = ("scheduled", "live", "completed", "cancelled")
    if status is not None and status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400

    fields, params = [], []
    if home_score is not None:
        fields.append("home_score = %s")
        params.append(home_score)
    if away_score is not None:
        fields.append("away_score = %s")
        params.append(away_score)
    if status is not None:
        fields.append("status = %s")
        params.append(status)

    if not fields:
        return jsonify({"error": "Nothing to update"}), 400

    params.append(match_id)
    execute(f"UPDATE matches SET {', '.join(fields)} WHERE id = %s", params)

    if status == "completed":
        score_match(match_id)

    return jsonify({"updated": True}), 200


@bp.get("/api/admin/users")
@require_admin
def list_users():
    rows = query(
        "SELECT id, username, email, is_admin, is_active, locked_until, created_at FROM users ORDER BY id"
    )
    for r in rows:
        r["is_admin"] = bool(r["is_admin"])
        r["is_active"] = bool(r["is_active"])
        r["locked_until"] = r["locked_until"].isoformat() if r["locked_until"] else None
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
    return jsonify(rows), 200


@bp.post("/api/admin/users/<int:user_id>/lock")
@require_admin
def lock_user(user_id):
    if not query("SELECT id FROM users WHERE id = %s", (user_id,)):
        return jsonify({"error": "User not found"}), 404
    far_future = datetime.now() + timedelta(days=36500)
    execute(
        "UPDATE users SET locked_until = %s WHERE id = %s",
        (far_future, user_id),
    )
    return jsonify({"locked": True}), 200


@bp.post("/api/admin/users/<int:user_id>/unlock")
@require_admin
def unlock_user(user_id):
    if not query("SELECT id FROM users WHERE id = %s", (user_id,)):
        return jsonify({"error": "User not found"}), 404
    execute(
        "UPDATE users SET locked_until = NULL, failed_login_count = 0 WHERE id = %s",
        (user_id,),
    )
    return jsonify({"unlocked": True}), 200


@bp.get("/api/admin/sessions")
@require_admin
def list_sessions():
    rows = query(
        "SELECT sa.user_id, u.username, sa.session_id, sa.created_at "
        "FROM session_audit sa JOIN users u ON u.id = sa.user_id "
        "WHERE sa.destroyed_at IS NULL ORDER BY sa.created_at DESC"
    )
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
    return jsonify(rows), 200


@bp.delete("/api/admin/sessions/<int:user_id>")
@require_admin
def delete_sessions(user_id):
    if not query("SELECT id FROM users WHERE id = %s", (user_id,)):
        return jsonify({"error": "User not found"}), 404
    destroy_all_sessions(user_id)
    return jsonify({"destroyed": True}), 200


@bp.get("/api/admin/stats")
@require_admin
def stats():
    active_sessions = query(
        "SELECT COUNT(*) AS cnt FROM session_audit WHERE destroyed_at IS NULL"
    )[0]["cnt"]
    total_users = query(
        "SELECT COUNT(*) AS cnt FROM users WHERE is_active = 1"
    )[0]["cnt"]
    predictions_24h = query(
        "SELECT COUNT(*) AS cnt FROM predictions WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)"
    )[0]["cnt"]
    return jsonify({
        "active_sessions": active_sessions,
        "total_users": total_users,
        "predictions_24h": predictions_24h,
    }), 200
