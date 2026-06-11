"""STEP-9: Matches API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_no_filter_returns_64(client):
    resp = client.get("/api/matches")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 64


def test_stage_group_returns_48(client):
    resp = client.get("/api/matches?stage=group")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 48
    assert all(m["stage"] == "group" for m in data)


def test_team_id_filter(client):
    resp = client.get("/api/matches?team_id=1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) > 0
    for m in data:
        assert m["home_team"]["id"] == 1 or m["away_team"]["id"] == 1


def test_match_detail_shape(client):
    resp = client.get("/api/matches/1")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "home_team" in data
    assert "away_team" in data
    assert "venue" in data
    assert "events" in data
    assert isinstance(data["events"], list)


def test_match_not_found(client):
    resp = client.get("/api/matches/99999")
    assert resp.status_code == 404
