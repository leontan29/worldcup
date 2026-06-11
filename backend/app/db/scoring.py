from app.db.connection import get_connection, _release


def score_match(match_id):
    """Call calculate_prediction_points stored procedure for a completed match."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("CALL calculate_prediction_points(%s)", (match_id,))
    finally:
        _release(conn)
