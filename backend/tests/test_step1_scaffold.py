"""STEP-1: Project scaffolding — Flask app starts and all blueprints load."""
import importlib
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_app_creates_without_error():
    from app import create_app
    app = create_app()
    assert app is not None


def test_all_blueprints_registered():
    from app import create_app
    app = create_app()
    names = {bp for bp in app.blueprints}
    expected = {"auth", "teams", "matches", "venues", "leaderboards",
                "standings", "predictions", "user", "admin", "activity"}
    assert expected == names


def test_app_returns_404_on_unknown_route():
    from app import create_app
    client = create_app().test_client()
    resp = client.get("/no-such-route")
    assert resp.status_code == 404
