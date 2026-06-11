from flask import Blueprint, jsonify, request

from app.db.connection import query

bp = Blueprint('teams', __name__)


@bp.get('/api/teams')
def list_teams():
    group = request.args.get('group', '').upper()
    if group:
        rows = query(
            "SELECT id, name, country_code, group_name, fifa_ranking, coach "
            "FROM teams WHERE group_name = %s ORDER BY name",
            (group,)
        )
    else:
        rows = query(
            "SELECT id, name, country_code, group_name, fifa_ranking, coach "
            "FROM teams ORDER BY group_name, name"
        )
    return jsonify(rows)


@bp.get('/api/teams/<int:team_id>')
def get_team(team_id):
    teams = query(
        "SELECT id, name, country_code, group_name, fifa_ranking, coach "
        "FROM teams WHERE id = %s",
        (team_id,)
    )
    if not teams:
        return jsonify({"error": "not found"}), 404

    team = teams[0]
    team['players'] = query(
        "SELECT id, name, position, jersey_number, goals, assists "
        "FROM players WHERE team_id = %s ORDER BY jersey_number",
        (team_id,)
    )
    return jsonify(team)
