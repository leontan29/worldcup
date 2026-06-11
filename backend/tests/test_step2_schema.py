"""STEP-2: MySQL schema — all tables, indexes, procedures, and trigger exist."""
import pytest


EXPECTED_TABLES = {
    "users", "teams", "players", "venues", "matches",
    "match_events", "predictions", "user_activity", "session_audit",
}


def test_all_tables_exist(db):
    with db.cursor() as cur:
        cur.execute("SHOW TABLES")
        tables = {list(row.values())[0] for row in cur.fetchall()}
    assert EXPECTED_TABLES == tables


def test_stored_procedure_calculate_prediction_points(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM information_schema.ROUTINES "
            "WHERE ROUTINE_SCHEMA=%s AND ROUTINE_NAME=%s AND ROUTINE_TYPE='PROCEDURE'",
            (db.db.decode(), "calculate_prediction_points"),
        )
        assert cur.fetchone()["n"] == 1


def test_stored_procedure_get_group_standings(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM information_schema.ROUTINES "
            "WHERE ROUTINE_SCHEMA=%s AND ROUTINE_NAME=%s AND ROUTINE_TYPE='PROCEDURE'",
            (db.db.decode(), "get_group_standings"),
        )
        assert cur.fetchone()["n"] == 1


def test_trigger_update_player_stats(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM information_schema.TRIGGERS "
            "WHERE TRIGGER_SCHEMA=%s AND TRIGGER_NAME=%s",
            (db.db.decode(), "update_player_stats"),
        )
        assert cur.fetchone()["n"] == 1


def test_required_indexes_exist(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT INDEX_NAME FROM information_schema.STATISTICS "
            "WHERE TABLE_SCHEMA=%s",
            (db.db.decode(),),
        )
        indexes = {row["INDEX_NAME"] for row in cur.fetchall()}
    required = {
        "idx_matches_date", "idx_teams_group",
        "idx_predictions_user", "idx_predictions_match",
    }
    assert required <= indexes


def test_unique_constraints_on_users(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='users' AND CONSTRAINT_TYPE='UNIQUE'",
            (db.db.decode(),),
        )
        constraints = {row["CONSTRAINT_NAME"] for row in cur.fetchall()}
    assert {"uq_users_username", "uq_users_email"} <= constraints
