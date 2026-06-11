import os
import pymysql
import redis
import pytest
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))


@pytest.fixture(scope="session")
def db():
    conn = pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=pymysql.cursors.DictCursor,
    )
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def redis_client():
    return redis.from_url(os.environ["REDIS_URL"])


@pytest.fixture(scope="session", autouse=True)
def clear_rate_limits():
    r = redis.from_url(os.environ["REDIS_URL"])
    for key in r.scan_iter("ratelimit:*"):
        r.delete(key)
