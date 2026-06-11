import os
import signal
import subprocess
import time
import pytest
import requests

BACKEND = os.path.join(os.path.dirname(__file__), "..")


@pytest.fixture(scope="module")
def gunicorn_server():
    env = os.environ.copy()
    proc = subprocess.Popen(
        ["gunicorn", "wsgi:app", "--config", "gunicorn.conf.py", "--bind", "127.0.0.1:18080"],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for server to be ready
    for _ in range(20):
        try:
            requests.get("http://127.0.0.1:18080/api/teams", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    yield proc
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=10)


def test_gunicorn_starts(gunicorn_server):
    assert gunicorn_server.poll() is None  # still running


def test_api_teams_responds(gunicorn_server):
    r = requests.get("http://127.0.0.1:18080/api/teams", timeout=5)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 32


def test_spa_serves_index(gunicorn_server):
    dist = os.path.join(BACKEND, "../frontend/dist")
    if not os.path.isdir(dist):
        pytest.skip("frontend/dist not built")
    r = requests.get("http://127.0.0.1:18080/", timeout=5)
    assert r.status_code == 200
    assert "text/html" in r.headers.get("Content-Type", "")


def test_gunicorn_conf_exists():
    conf = os.path.join(BACKEND, "gunicorn.conf.py")
    assert os.path.isfile(conf)


def test_gunicorn_conf_has_workers():
    conf = os.path.join(BACKEND, "gunicorn.conf.py")
    content = open(conf).read()
    assert "workers" in content
    assert "timeout" in content
