from __future__ import annotations

import json
from datetime import datetime
from typing import cast

import pytest

from ckan.lib.redis import connect_to_redis

from ckanext.better_stats import cache


@pytest.mark.usefixtures("clean_redis")
class TestCache:
    def test_cache_get_returns_deserialised(self) -> None:
        conn = connect_to_redis()
        conn.set("bs:test:get", json.dumps({"a": 1}))
        assert cache.cache_get("bs:test:get") == {"a": 1}

    def test_cache_get_returns_none_on_miss(self) -> None:
        assert cache.cache_get("bs:test:missing") is None

    def test_cache_set_serialises_and_expires(self) -> None:
        cache.cache_set("bs:test:set", {"a": 1, "b": [1, 2]}, ttl=300)

        conn = connect_to_redis()
        raw = cast(bytes, conn.get("bs:test:set"))
        assert raw is not None
        assert json.loads(raw) == {"a": 1, "b": [1, 2]}
        ttl = cast(int, conn.ttl("bs:test:set"))

        assert 0 < ttl <= 300

    def test_cache_set_rejects_non_json_value(self) -> None:
        with pytest.raises(TypeError):
            cache.cache_set("bs:test:dt", {"when": datetime(2026, 1, 1)}, ttl=60)

    def test_cache_delete(self) -> None:
        cache.cache_set("bs:test:delete", "x", ttl=60)
        assert cache.cache_get("bs:test:delete") == "x"

        cache.cache_delete("bs:test:delete")
        assert cache.cache_get("bs:test:delete") is None

    def test_cache_delete_pattern_removes_matching_keys(self) -> None:
        for i in range(3):
            cache.cache_set(f"bs:user:{i}:metric:foo", i, ttl=60)

        cache.cache_set("bs:other:keep", "stay", ttl=60)

        deleted = cache.cache_delete_pattern("bs:user:*:metric:foo")

        assert deleted == 3
        assert cache.cache_get("bs:other:keep") == "stay"

        for i in range(3):
            assert cache.cache_get(f"bs:user:{i}:metric:foo") is None

    def test_cache_delete_pattern_no_matches_returns_zero(self) -> None:
        assert cache.cache_delete_pattern("bs:nothing:matches:*") == 0
