"""STEP-13: Knockout Bracket API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_all_round_keys_present(client):
    resp = client.get("/api/standings/knockout")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == {"round_of_16", "quarterfinal", "semifinal", "third_place", "final"}


def test_round_of_16_has_8_matches(client):
    data = client.get("/api/standings/knockout").get_json()
    assert len(data["round_of_16"]) == 8


def test_final_shows_argentina_vs_france(client):
    data = client.get("/api/standings/knockout").get_json()
    final = data["final"]
    assert len(final) == 1
    slot = final[0]
    codes = {slot["home_team"]["country_code"], slot["away_team"]["country_code"]}
    assert codes == {"ARG", "FRA"}


def test_final_score_3_3(client):
    data = client.get("/api/standings/knockout").get_json()
    slot = data["final"][0]
    assert slot["home_score"] == 3
    assert slot["away_score"] == 3


def test_match_shape(client):
    data = client.get("/api/standings/knockout").get_json()
    slot = data["final"][0]
    assert "match_id" in slot
    assert "status" in slot
    assert "home_team" in slot
    assert "away_team" in slot
