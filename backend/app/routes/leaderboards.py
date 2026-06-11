from flask import Blueprint, jsonify

from app.db.connection import query

bp = Blueprint('leaderboards', __name__)

_PLAYER_COLS = """
    p.id, p.name, p.position, p.jersey_number, p.goals, p.assists,
    t.id AS team_id, t.name AS team_name, t.country_code
"""
_PLAYER_JOIN = "FROM players p JOIN teams t ON t.id = p.team_id"


@bp.get('/api/leaderboards/goals')
def top_goals():
    rows = query(
        f"SELECT {_PLAYER_COLS} {_PLAYER_JOIN} ORDER BY p.goals DESC, p.assists DESC LIMIT 10"
    )
    return jsonify(rows)


@bp.get('/api/leaderboards/assists')
def top_assists():
    rows = query(
        f"SELECT {_PLAYER_COLS} {_PLAYER_JOIN} ORDER BY p.assists DESC, p.goals DESC LIMIT 10"
    )
    return jsonify(rows)
