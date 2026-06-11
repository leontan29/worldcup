from flask import Blueprint, jsonify, request

from app.db.connection import get_connection, _release, query

bp = Blueprint('standings', __name__)

_GROUPS = list("ABCDEFGH")


def _call_group_standings(group):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL get_group_standings(%s)", (group,))
            rows = list(cur.fetchall())
        return rows
    finally:
        _release(conn)


# ── STEP-12: Group Standings ──────────────────────────────────────────────────

@bp.get('/api/standings/group')
def group_standings():
    group = request.args.get('group', '').upper()
    if group:
        if group not in _GROUPS:
            return jsonify({"error": "invalid group"}), 400
        return jsonify({group: _call_group_standings(group)})

    result = {}
    for g in _GROUPS:
        result[g] = _call_group_standings(g)
    return jsonify(result)


# ── STEP-13: Knockout Bracket ─────────────────────────────────────────────────

_KNOCKOUT_STAGES = ['round_of_16', 'quarterfinal', 'semifinal', 'third_place', 'final']


@bp.get('/api/standings/knockout')
def knockout_bracket():
    rows = query(
        """
        SELECT m.id, m.stage, m.status, m.home_score, m.away_score,
               ht.id AS home_team_id, ht.name AS home_team, ht.country_code AS home_country_code,
               at.id AS away_team_id, at.name AS away_team, at.country_code AS away_country_code
        FROM matches m
        LEFT JOIN teams ht ON ht.id = m.home_team_id
        LEFT JOIN teams at ON at.id = m.away_team_id
        WHERE m.stage IN ('round_of_16','quarterfinal','semifinal','third_place','final')
        ORDER BY m.stage, m.id
        """
    )

    bracket = {s: [] for s in _KNOCKOUT_STAGES}
    for r in rows:
        bracket[r['stage']].append({
            "match_id": r["id"],
            "status": r["status"],
            "home_score": r["home_score"],
            "away_score": r["away_score"],
            "home_team": {"id": r["home_team_id"], "name": r["home_team"], "country_code": r["home_country_code"]},
            "away_team": {"id": r["away_team_id"], "name": r["away_team"], "country_code": r["away_country_code"]},
        })
    return jsonify(bracket)
