import os
import queue
import threading

import pymysql
from pymysql.cursors import DictCursor

_MAX_POOL = 20
_pool: queue.Queue = queue.Queue(maxsize=_MAX_POOL)
_pool_lock = threading.Lock()
_pool_size = 0


def _new_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        cursorclass=DictCursor,
        autocommit=True,
    )


def get_connection():
    global _pool_size
    try:
        return _pool.get_nowait()
    except queue.Empty:
        with _pool_lock:
            if _pool_size < _MAX_POOL:
                _pool_size += 1
                return _new_connection()
        return _pool.get(timeout=5)


def _release(conn):
    try:
        conn.ping(reconnect=True)
        _pool.put_nowait(conn)
    except Exception:
        _pool.put_nowait(_new_connection())


def query(sql, params=None):
    """Parameterized SELECT — returns list of dicts."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
    finally:
        _release(conn)


def execute(sql, params=None):
    """Parameterized INSERT/UPDATE/DELETE — returns (lastrowid, rowcount)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.lastrowid, cur.rowcount
    finally:
        _release(conn)
