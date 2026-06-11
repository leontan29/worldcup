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


def test_app_handles_unknown_route():
    from app import create_app
    import os
    client = create_app().test_client()
    resp = client.get("/no-such-route")
    # SPA: serves index.html (200) when dist exists; 404 otherwise
    dist = os.path.join(os.path.dirname(__file__), "../../frontend/dist")
    if os.path.isdir(dist):
        assert resp.status_code == 200
    else:
        assert resp.status_code == 404
