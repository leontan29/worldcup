"""STEP-3: Seed data — correct row counts and basic data integrity."""
import pytest


def test_team_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM teams")
        assert cur.fetchone()["n"] == 32


def test_venue_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM venues")
        assert cur.fetchone()["n"] == 8


def test_player_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM players")
        assert cur.fetchone()["n"] >= 32 * 23


def test_match_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM matches")
        assert cur.fetchone()["n"] == 64


def test_group_stage_match_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM matches WHERE stage='group'")
        assert cur.fetchone()["n"] == 48


def test_knockout_match_count(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM matches WHERE stage != 'group'")
        assert cur.fetchone()["n"] == 16


def test_each_group_has_four_teams(db):
    with db.cursor() as cur:
        cur.execute("SELECT group_name, COUNT(*) AS n FROM teams GROUP BY group_name")
        for row in cur.fetchall():
            assert row["n"] == 4, f"Group {row['group_name']} has {row['n']} teams"


def test_each_group_has_six_matches(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT group_name, COUNT(*) AS n FROM matches "
            "WHERE stage='group' GROUP BY group_name"
        )
        for row in cur.fetchall():
            assert row["n"] == 6, f"Group {row['group_name']} has {row['n']} matches"


def test_all_matches_completed(db):
    with db.cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM matches WHERE status != 'completed'")
        assert cur.fetchone()["n"] == 0


def test_all_completed_matches_have_scores(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM matches "
            "WHERE status='completed' AND (home_score IS NULL OR away_score IS NULL)"
        )
        assert cur.fetchone()["n"] == 0


def test_argentina_beat_france_in_final(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT m.home_score, m.away_score FROM matches m "
            "JOIN teams h ON m.home_team_id = h.id "
            "JOIN teams a ON m.away_team_id = a.id "
            "WHERE m.stage='final' AND h.name='Argentina' AND a.name='France'"
        )
        row = cur.fetchone()
        assert row is not None
        assert row["home_score"] == 3 and row["away_score"] == 3


def test_player_jersey_numbers_unique_per_team(db):
    with db.cursor() as cur:
        cur.execute(
            "SELECT team_id, jersey_number, COUNT(*) AS n FROM players "
            "GROUP BY team_id, jersey_number HAVING n > 1"
        )
        dupes = cur.fetchall()
    assert len(dupes) == 0, f"Duplicate jersey numbers: {dupes}"
