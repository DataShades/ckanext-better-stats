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
