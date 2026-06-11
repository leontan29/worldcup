"""STEP-8: Teams API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_list_teams_returns_32(client):
    resp = client.get("/api/teams")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 32


def test_group_filter_returns_4(client):
    resp = client.get("/api/teams?group=A")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 4
    assert all(t["group_name"] == "A" for t in data)


def test_team_detail_has_players(client):
    teams = client.get("/api/teams").get_json()
    team_id = teams[0]["id"]
    resp = client.get(f"/api/teams/{team_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "players" in data
    assert len(data["players"]) > 0


def test_team_not_found(client):
    resp = client.get("/api/teams/99999")
    assert resp.status_code == 404
