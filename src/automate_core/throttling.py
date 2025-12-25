import time
from dataclasses import dataclass
from typing import Protocol


class RateLimiter(Protocol):
    def acquire(self, key: str, *, tokens: int = 1, wait: bool = False, timeout_s: int = 0) -> bool:
        """
        Acquire tokens from the rate limiter.
        If wait is True, block until tokens are available or timeout.
        """
        ...

@dataclass
class TokenBucket:
    capacity: int
    tokens: float
    fill_rate: float
    last_update: float

class MemoryRateLimiter:
    """
    Simple in-memory token bucket rate limiter.
    Not thread-safe or process-safe. Use Redis implementation for production.
    """
    def __init__(self, default_rate: float = 1.0, default_capacity: int = 10):
        # default_rate: tokens per second
        self.buckets: dict[str, TokenBucket] = {}
        self.default_rate = default_rate
        self.default_capacity = default_capacity

    def _get_bucket(self, key: str) -> TokenBucket:
        if key not in self.buckets:
            self.buckets[key] = TokenBucket(
                capacity=self.default_capacity,
                tokens=float(self.default_capacity),
                fill_rate=self.default_rate,
                last_update=time.time()
            )
        return self.buckets[key]

    def _refill(self, bucket: TokenBucket):
        now = time.time()
        delta = now - bucket.last_update
        added = delta * bucket.fill_rate
        bucket.tokens = min(bucket.capacity, bucket.tokens + added)
        bucket.last_update = now

    def acquire(self, key: str, *, tokens: int = 1, wait: bool = False, timeout_s: int = 0) -> bool:
        start_time = time.time()

        while True:
            bucket = self._get_bucket(key)
            self._refill(bucket)

            if bucket.tokens >= tokens:
                bucket.tokens -= tokens
                return True

            if not wait:
                return False

            elapsed = time.time() - start_time
            if timeout_s > 0 and elapsed > timeout_s:
                return False

            # Sleep a bit and retry (naive busy wait for V1)
            time.sleep(0.1)
