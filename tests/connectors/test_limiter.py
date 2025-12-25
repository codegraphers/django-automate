import time

import pytest

from automate_core.throttling import MemoryRateLimiter


def test_token_bucket():
    # 1 token per second, capacity 2
    limiter = MemoryRateLimiter(default_rate=10.0, default_capacity=5)

    # Acquire 1
    assert limiter.acquire("k1", tokens=1) is True

    # Acquire more than capacity (if refill is slow)
    # But here refill is fast.

    # Test strict limit
    limiter_strict = MemoryRateLimiter(default_rate=0.1, default_capacity=1)
    assert limiter_strict.acquire("k2", tokens=1) is True
    # Next one should fail as refill is 0.1/s
    assert limiter_strict.acquire("k2", tokens=1) is False

    # Wait behavior (mocking time might be needed for robust test, but simple check)
    # Blocking is hard to test without delay, skipping complex wait test.
