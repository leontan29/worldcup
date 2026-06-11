from flask import Blueprint, g, jsonify

from app.auth.middleware import require_auth
from app.db.connection import execute, query

bp = Blueprint("activity", __name__)


def log_activity(user_id: int, action: str, ip_address: str) -> None:
    execute(
        "INSERT INTO user_activity (user_id, action, ip_address) VALUES (%s, %s, %s)",
        (user_id, action, ip_address),
    )


@bp.get("/api/user/activity")
@require_auth
def get_activity():
    uid = g.user["user_id"]
    execute(
        "DELETE FROM user_activity WHERE user_id = %s AND created_at < DATE_SUB(NOW(), INTERVAL 90 DAY)",
        (uid,),
    )
    rows = query(
        "SELECT id, action, ip_address, created_at FROM user_activity "
        "WHERE user_id = %s ORDER BY created_at DESC LIMIT 100",
        (uid,),
    )
    for r in rows:
        r["created_at"] = r["created_at"].isoformat() if r["created_at"] else None
    return jsonify(rows), 200
