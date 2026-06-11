"""STEP-19: React App Setup."""
import os
import subprocess

FRONTEND = os.path.join(os.path.dirname(__file__), "../../frontend")


def test_build_exits_0():
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=FRONTEND,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_proxy_config_present():
    config_path = os.path.join(FRONTEND, "vite.config.js")
    assert os.path.exists(config_path), "vite.config.js missing"
    content = open(config_path).read()
    assert "proxy" in content
    assert "/api" in content


def test_auth_context_exists():
    path = os.path.join(FRONTEND, "src/context/AuthContext.jsx")
    assert os.path.exists(path)
    content = open(path).read()
    assert "AuthContext" in content
    assert "login" in content
    assert "logout" in content


def test_protected_route_exists():
    path = os.path.join(FRONTEND, "src/components/ProtectedRoute.jsx")
    assert os.path.exists(path)
    content = open(path).read()
    assert "Navigate" in content


def test_navbar_exists():
    path = os.path.join(FRONTEND, "src/components/Navbar.jsx")
    assert os.path.exists(path)
    content = open(path).read()
    assert "Outlet" in content or "Link" in content
