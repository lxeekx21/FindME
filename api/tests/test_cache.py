import asyncio
import time

import pytest

from app.core.cache import ttl_cache, TTLCache, _global_cache


def test_ttl_cache_sync_caches_and_expires(monkeypatch):
    # Ensure we start with a clean cache
    _global_cache.clear()

    calls = {"count": 0}

    @ttl_cache(ttl_seconds=1)
    def compute(x):
        calls["count"] += 1
        return x * 2

    # First call computes
    assert compute(3) == 6
    assert calls["count"] == 1
    # Second call within TTL uses cache
    assert compute(3) == 6
    assert calls["count"] == 1

    # Different argument should bypass cache (different key)
    assert compute(4) == 8
    assert calls["count"] == 2

    # After TTL expires, it should recompute
    time.sleep(1.1)
    assert compute(3) == 6
    assert calls["count"] == 3


@pytest.mark.asyncio
async def test_ttl_cache_async_caches_and_expires():
    _global_cache.clear()

    calls = {"count": 0}

    @ttl_cache(ttl_seconds=1)
    async def acompute(x):
        calls["count"] += 1
        await asyncio.sleep(0)  # exercise async path
        return x + 5

    # First call computes
    assert await acompute(10) == 15
    assert calls["count"] == 1

    # Second call within TTL should use cache
    assert await acompute(10) == 15
    assert calls["count"] == 1

    # Wait for expiry and call again
    await asyncio.sleep(1.1)
    assert await acompute(10) == 15
    assert calls["count"] == 2
