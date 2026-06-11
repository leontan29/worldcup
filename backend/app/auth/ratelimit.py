from app.db.redis_client import get_redis


def check_rate_limit(key: str, limit: int, window: int) -> bool:
    """Returns True if the request is within the limit, False if exceeded.

    Uses a Redis counter with a TTL. The window starts on the first request.
    """
    r = get_redis()
    count = r.incr(key)
    if count == 1:
        r.expire(key, window)
    return count <= limit
