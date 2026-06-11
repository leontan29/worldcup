"""STEP-4: Database connection layer."""
import pytest
from app.db.connection import query, execute


def test_query_select_one():
    rows = query("SELECT 1 AS n")
    assert rows == [{"n": 1}]


def test_query_returns_list_of_dicts():
    rows = query("SELECT name, country_code FROM teams WHERE group_name = %s", ("A",))
    assert isinstance(rows, list)
    assert len(rows) == 4
    assert "name" in rows[0]
    assert "country_code" in rows[0]


def test_execute_insert_and_query_roundtrip():
    execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_test_db_user", "_test_db@example.com", "placeholder"),
    )
    rows = query("SELECT username FROM users WHERE username = %s", ("_test_db_user",))
    assert rows[0]["username"] == "_test_db_user"
    execute("DELETE FROM users WHERE username = %s", ("_test_db_user",))


def test_execute_returns_lastrowid():
    lastrowid, _ = execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_test_db_user2", "_test_db2@example.com", "placeholder"),
    )
    assert isinstance(lastrowid, int) and lastrowid > 0
    execute("DELETE FROM users WHERE username = %s", ("_test_db_user2",))


def test_execute_returns_rowcount():
    execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("_test_db_user3", "_test_db3@example.com", "placeholder"),
    )
    _, rowcount = execute("DELETE FROM users WHERE username = %s", ("_test_db_user3",))
    assert rowcount == 1


def test_parameterized_query_prevents_injection():
    # A raw injection string must not match any real team name
    rows = query("SELECT * FROM teams WHERE name = %s", ("' OR '1'='1",))
    assert rows == []


def test_pool_handles_concurrent_queries():
    import concurrent.futures

    def run(_):
        return query("SELECT COUNT(*) AS n FROM teams")[0]["n"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(run, range(20)))

    assert all(r == 32 for r in results)
