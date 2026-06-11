"""STEP-21: Home Page."""
import os

PAGES = os.path.join(os.path.dirname(__file__), "../../frontend/src/pages")


def test_home_page_exists():
    path = os.path.join(PAGES, "Home.jsx")
    assert os.path.exists(path)


def test_home_fetches_matches():
    src = open(os.path.join(PAGES, "Home.jsx")).read()
    assert "/api/matches" in src


def test_home_has_quick_links():
    src = open(os.path.join(PAGES, "Home.jsx")).read()
    for route in ["/matches", "/standings", "/teams", "/leaderboard"]:
        assert route in src
