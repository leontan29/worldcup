from flask import Blueprint, jsonify

from app.db.connection import query

bp = Blueprint('venues', __name__)


@bp.get('/api/venues')
def list_venues():
    rows = query("SELECT id, name, city, country, capacity FROM venues ORDER BY name")
    return jsonify(rows)
