"""STEP-15: Prediction Scoring — calculate_prediction_points stored procedure."""
import pytest
from app.db.connection import execute, query
from app.db.scoring import score_match


@pytest.fixture(scope="module")
def setup():
    """Create two test users, a scheduled match, and predictions."""
    # clean up any leftovers
    for uname in ("_score_u1", "_score_u2", "_score_u3"):
        rows = query("SELECT id FROM users WHERE username = %s", (uname,))
        if rows:
            uid = rows[0]["id"]
            execute("DELETE FROM predictions WHERE user_id = %s", (uid,))
            execute("DELETE FROM session_audit WHERE user_id = %s", (uid,))
            execute("DELETE FROM users WHERE id = %s", (uid,))

    u1, _ = execute("INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
                    ("_score_u1", "_score_u1@test.com", "x"))
    u2, _ = execute("INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
                    ("_score_u2", "_score_u2@test.com", "x"))
    u3, _ = execute("INSERT INTO users (username, email, password_hash) VALUES (%s,%s,%s)",
                    ("_score_u3", "_score_u3@test.com", "x"))

    # use match 1 as test match; force it scheduled with a known score
    execute("UPDATE matches SET status='scheduled', home_score=NULL, away_score=NULL WHERE id=1")

    # u1 predicts exact score: 2-1
    execute("INSERT INTO predictions (user_id, match_id, home_score, away_score) VALUES (%s,1,%s,%s)",
            (u1, 2, 1))
    # u2 predicts correct outcome (home win, different score): 3-0
    execute("INSERT INTO predictions (user_id, match_id, home_score, away_score) VALUES (%s,1,%s,%s)",
            (u2, 3, 0))
    # u3 predicts wrong: 0-1 (away win when actual is home win)
    execute("INSERT INTO predictions (user_id, match_id, home_score, away_score) VALUES (%s,1,%s,%s)",
            (u3, 0, 1))

    # mark match completed with actual score 2-1
    execute("UPDATE matches SET status='completed', home_score=2, away_score=1 WHERE id=1")

    yield {"u1": u1, "u2": u2, "u3": u3, "match_id": 1}

    # teardown
    execute("DELETE FROM predictions WHERE match_id=1 AND user_id IN (%s,%s,%s)", (u1, u2, u3))
    execute("DELETE FROM session_audit WHERE user_id IN (%s,%s,%s)", (u1, u2, u3))
    execute("DELETE FROM users WHERE id IN (%s,%s,%s)", (u1, u2, u3))
    # restore match to original completed state (QAT 0-2 ECU)
    execute("UPDATE matches SET home_score=0, away_score=2 WHERE id=1")


def test_score_match_runs(setup):
    score_match(setup["match_id"])


def test_exact_score_earns_3_points(setup):
    rows = query("SELECT points_earned FROM predictions WHERE user_id=%s AND match_id=1",
                 (setup["u1"],))
    assert rows[0]["points_earned"] == 3


def test_correct_outcome_earns_1_point(setup):
    rows = query("SELECT points_earned FROM predictions WHERE user_id=%s AND match_id=1",
                 (setup["u2"],))
    assert rows[0]["points_earned"] == 1


def test_wrong_prediction_earns_0_points(setup):
    rows = query("SELECT points_earned FROM predictions WHERE user_id=%s AND match_id=1",
                 (setup["u3"],))
    assert rows[0]["points_earned"] == 0
