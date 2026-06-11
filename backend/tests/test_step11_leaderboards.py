"""STEP-11: Player Leaderboards API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_goals_returns_10(client):
    resp = client.get("/api/leaderboards/goals")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 10


def test_assists_returns_10(client):
    resp = client.get("/api/leaderboards/assists")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 10


def test_goals_sorted_desc(client):
    data = client.get("/api/leaderboards/goals").get_json()
    goals = [r["goals"] for r in data]
    assert goals == sorted(goals, reverse=True)


def test_assists_sorted_desc(client):
    data = client.get("/api/leaderboards/assists").get_json()
    assists = [r["assists"] for r in data]
    assert assists == sorted(assists, reverse=True)


def test_goals_leader_is_mbappe(client):
    data = client.get("/api/leaderboards/goals").get_json()
    assert data[0]["name"] == "Kylian Mbappe"
    assert data[0]["goals"] == 8


def test_goals_second_is_messi(client):
    data = client.get("/api/leaderboards/goals").get_json()
    assert data[1]["name"] == "Lionel Messi"
    assert data[1]["goals"] == 7


def test_leaderboard_includes_team(client):
    data = client.get("/api/leaderboards/goals").get_json()
    for r in data:
        assert "team_name" in r
        assert "country_code" in r
