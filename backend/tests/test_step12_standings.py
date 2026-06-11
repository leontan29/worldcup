"""STEP-12: Group Standings API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_all_8_groups_present(client):
    resp = client.get("/api/standings/group")
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(data.keys()) == set("ABCDEFGH")


def test_each_group_has_4_teams(client):
    data = client.get("/api/standings/group").get_json()
    for g, rows in data.items():
        assert len(rows) == 4, f"Group {g} has {len(rows)} teams"


def test_group_filter(client):
    resp = client.get("/api/standings/group?group=A")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "A" in data
    assert len(data["A"]) == 4


def test_group_a_top_two(client):
    data = client.get("/api/standings/group?group=A").get_json()
    top_two = {r["country_code"] for r in data["A"][:2]}
    assert top_two == {"NED", "SEN"}


def test_points_arithmetic(client):
    data = client.get("/api/standings/group").get_json()
    for g, rows in data.items():
        for r in rows:
            expected = int(r["wins"]) * 3 + int(r["draws"])
            assert int(r["points"]) == expected, f"Points mismatch for {r['name']}"


def test_invalid_group_returns_400(client):
    resp = client.get("/api/standings/group?group=Z")
    assert resp.status_code == 400
