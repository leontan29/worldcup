"""STEP-10: Venues API."""
import pytest
from app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_returns_8_venues(client):
    resp = client.get("/api/venues")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 8


def test_venue_shape(client):
    data = client.get("/api/venues").get_json()
    for v in data:
        assert "name" in v
        assert "city" in v
        assert "country" in v
        assert "capacity" in v
