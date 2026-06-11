from flask import Blueprint, jsonify, request

from app.db.connection import query

bp = Blueprint('matches', __name__)

_MATCH_COLS = """
    m.id, m.match_date, m.stage, m.status,
    m.home_score, m.away_score, m.group_name,
    ht.id AS home_team_id, ht.name AS home_team, ht.country_code AS home_country_code,
    at.id AS away_team_id, at.name AS away_team, at.country_code AS away_country_code,
    v.id AS venue_id, v.name AS venue_name, v.city AS venue_city
"""

_MATCH_JOINS = """
    FROM matches m
    LEFT JOIN teams ht ON ht.id = m.home_team_id
    LEFT JOIN teams at ON at.id = m.away_team_id
    JOIN venues v ON v.id = m.venue_id
"""


def _build_match(row):
    return {
        "id": row["id"],
        "match_date": row["match_date"].isoformat() if row["match_date"] else None,
        "stage": row["stage"],
        "status": row["status"],
        "group_name": row["group_name"],
        "home_score": row["home_score"],
        "away_score": row["away_score"],
        "home_team": {"id": row["home_team_id"], "name": row["home_team"], "country_code": row["home_country_code"]},
        "away_team": {"id": row["away_team_id"], "name": row["away_team"], "country_code": row["away_country_code"]},
        "venue": {"id": row["venue_id"], "name": row["venue_name"], "city": row["venue_city"]},
    }


@bp.get('/api/matches')
def list_matches():
    conditions = []
    params = []

    date = request.args.get('date')
    if date:
        conditions.append("DATE(m.match_date) = %s")
        params.append(date)

    stage = request.args.get('stage')
    if stage:
        conditions.append("m.stage = %s")
        params.append(stage)

    team_id = request.args.get('team_id')
    if team_id:
        conditions.append("(m.home_team_id = %s OR m.away_team_id = %s)")
        params.extend([team_id, team_id])

    venue_id = request.args.get('venue_id')
    if venue_id:
        conditions.append("m.venue_id = %s")
        params.append(venue_id)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT {_MATCH_COLS} {_MATCH_JOINS} {where} ORDER BY m.match_date"
    rows = query(sql, params or None)
    return jsonify([_build_match(r) for r in rows])


@bp.get('/api/matches/<int:match_id>')
def get_match(match_id):
    rows = query(
        f"SELECT {_MATCH_COLS} {_MATCH_JOINS} WHERE m.id = %s",
        (match_id,)
    )
    if not rows:
        return jsonify({"error": "not found"}), 404

    match = _build_match(rows[0])
    match['events'] = query(
        """
        SELECT e.id, e.event_type, e.minute,
               p.id AS player_id, p.name AS player_name, p.team_id
        FROM match_events e
        JOIN players p ON p.id = e.player_id
        WHERE e.match_id = %s
        ORDER BY e.minute
        """,
        (match_id,)
    )
    return jsonify(match)
