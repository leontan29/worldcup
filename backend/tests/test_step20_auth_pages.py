"""STEP-20: Auth Pages."""
import os

PAGES = os.path.join(os.path.dirname(__file__), "../../frontend/src/pages")


def test_login_page_exists():
    path = os.path.join(PAGES, "Login.jsx")
    assert os.path.exists(path)
    src = open(path).read()
    assert "/api/auth/login" in src
    assert "navigate" in src


def test_register_page_exists():
    path = os.path.join(PAGES, "Register.jsx")
    assert os.path.exists(path)
    src = open(path).read()
    assert "/api/auth/register" in src
    assert "strength" in src.lower()


def test_auth_context_restores_session():
    path = os.path.join(os.path.dirname(__file__), "../../frontend/src/context/AuthContext.jsx")
    src = open(path).read()
    assert "/api/user/profile" in src
    assert "useEffect" in src


def test_build_succeeds():
    import subprocess
    frontend = os.path.join(os.path.dirname(__file__), "../../frontend")
    r = subprocess.run(["npm", "run", "build"], cwd=frontend, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
