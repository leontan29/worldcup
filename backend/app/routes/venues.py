from flask import Blueprint, jsonify

from app.db.connection import query

bp = Blueprint('venues', __name__)


@bp.get('/api/venues')
def list_venues():
    rows = query("SELECT id, name, city, country, capacity FROM venues ORDER BY name")
    return jsonify(rows)


@bp.get('/api/info')
def tournament_info():
    year_row = query("SELECT YEAR(MIN(match_date)) AS year FROM matches")
    year = year_row[0]['year'] if year_row else None
    country_rows = query("SELECT DISTINCT country FROM venues ORDER BY country")
    countries = [r['country'] for r in country_rows]
    return jsonify({'year': year, 'host': ' · '.join(countries)})
