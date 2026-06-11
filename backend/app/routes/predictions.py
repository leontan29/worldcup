from flask import Blueprint, g, jsonify, request

from app.auth.middleware import require_auth
from app.db.connection import execute, query

bp = Blueprint('predictions', __name__)


@bp.post('/api/predictions/<int:match_id>')
@require_auth
def upsert_prediction(match_id):
    matches = query("SELECT id, status FROM matches WHERE id = %s", (match_id,))
    if not matches:
        return jsonify({"error": "match not found"}), 404
    if matches[0]["status"] != "scheduled":
        return jsonify({"error": "predictions only allowed for scheduled matches"}), 400

    body = request.get_json(silent=True) or {}
    home_score = body.get("home_score")
    away_score = body.get("away_score")
    if home_score is None or away_score is None:
        return jsonify({"error": "home_score and away_score required"}), 400

    existing = query(
        "SELECT id FROM predictions WHERE user_id = %s AND match_id = %s",
        (g.user["user_id"], match_id)
    )
    if existing:
        execute(
            "UPDATE predictions SET home_score = %s, away_score = %s WHERE id = %s",
            (home_score, away_score, existing[0]["id"])
        )
        return jsonify({"updated": True}), 200

    execute(
        "INSERT INTO predictions (user_id, match_id, home_score, away_score) VALUES (%s, %s, %s, %s)",
        (g.user["user_id"], match_id, home_score, away_score)
    )
    return jsonify({"created": True}), 201


@bp.get('/api/user/predictions')
@require_auth
def my_predictions():
    rows = query(
        """
        SELECT p.id, p.home_score AS predicted_home, p.away_score AS predicted_away,
               p.points_earned, p.created_at, p.updated_at,
               m.id AS match_id, m.match_date, m.stage, m.status,
               m.home_score AS actual_home, m.away_score AS actual_away,
               ht.name AS home_team, at.name AS away_team
        FROM predictions p
        JOIN matches m ON m.id = p.match_id
        LEFT JOIN teams ht ON ht.id = m.home_team_id
        LEFT JOIN teams at ON at.id = m.away_team_id
        WHERE p.user_id = %s
        ORDER BY m.match_date
        """,
        (g.user["user_id"],)
    )
    for r in rows:
        if r.get("match_date"):
            r["match_date"] = r["match_date"].isoformat()
        if r.get("created_at"):
            r["created_at"] = r["created_at"].isoformat()
        if r.get("updated_at"):
            r["updated_at"] = r["updated_at"].isoformat()
    return jsonify(rows)


@bp.get('/api/predictions/leaderboard')
def predictions_leaderboard():
    rows = query(
        """
        SELECT u.id, u.username,
               COALESCE(SUM(p.points_earned), 0) AS total_points,
               SUM(CASE WHEN p.points_earned = 3 THEN 1 ELSE 0 END) AS exact_count
        FROM users u
        JOIN predictions p ON p.user_id = u.id
        WHERE u.is_active = 1
        GROUP BY u.id, u.username
        ORDER BY total_points DESC, exact_count DESC
        LIMIT 50
        """
    )
    return jsonify(rows)
