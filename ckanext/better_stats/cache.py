from __future__ import annotations

import json
from typing import Any

from ckan.lib.redis import connect_to_redis


def cache_get(key: str) -> Any | None:
    """Return the deserialised value for *key*, or ``None`` on a cache miss."""
    raw = connect_to_redis().get(key)
    return json.loads(raw) if raw is not None else None  # type: ignore


def cache_set(key: str, value: Any, ttl: int) -> None:
    """Serialise *value* and store it under *key* with a TTL of *ttl* seconds."""
    connect_to_redis().setex(key, ttl, json.dumps(value, default=str))


def cache_delete(key: str) -> None:
    """Remove *key* from the cache."""
    connect_to_redis().delete(key)


def cache_delete_pattern(pattern: str) -> int:
    """Remove all keys matching *pattern* (glob-style) from the cache.

    Uses ``SCAN`` to avoid blocking Redis on large keyspaces.
    Returns the number of keys deleted.
    """
    client = connect_to_redis()
    deleted = 0
    cursor = 0

    while True:
        cursor, keys = client.scan(cursor, match=pattern, count=100)  # type: ignore

        if keys:
            deleted += client.delete(*keys)  # type: ignore

        if cursor == 0:
            break

    return deleted
