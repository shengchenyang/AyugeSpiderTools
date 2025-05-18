from __future__ import annotations

from typing import cast

from ayugespidertools.exceptions import NotConfigured

try:
    import redis
except ImportError:
    raise NotConfigured(
        "missing redis library, please install it. "
        "install command: pip install ayugespidertools[database]"
    )


class Deduplicate:
    def __init__(self, name: str, redis_url: str | None = None):
        pool = redis.ConnectionPool.from_url(redis_url)
        self.redis_client = redis.Redis.from_pool(pool)
        self.name = name

    def add(self, key: str) -> int:
        return cast(int, self.redis_client.sadd(self.name, key))

    def get(self, key: str):
        return self.redis_client.sismember(self.name, key)

    def exists(self, key: str) -> int:
        lua_script = """
        if redis.call('SISMEMBER', KEYS[1], ARGV[1]) == 1 then
            return 1
        else
            redis.call('SADD', KEYS[1], ARGV[1])
            return 0
        end
        """
        return cast(int, self.redis_client.eval(lua_script, 1, self.name, key))
