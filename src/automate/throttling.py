import time

from django.core.cache import cache


class RateLimiter:
    """
    Token Bucket Rate Limiter backed by Redis (cache).
    Track D Requirement.
    """
    def __init__(self, key: str, limit: int, period: int):
        self.key = f"rl:{key}"
        self.limit = limit
        self.period = period

    def allow(self) -> bool:
        """
        Returns True if request should be allowed.
        """
        now = int(time.time())
        window = now // self.period
        cache_key = f"{self.key}:{window}"

        current = cache.get_or_set(cache_key, 0, timeout=self.period + 10)

        if current < self.limit:
            cache.incr(cache_key)
            return True
        return False

class CircuitBreaker:
    """
    Simple Circuit Breaker.
    """
    def __init__(self, key: str, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.key = f"cb:{key}"
        self.threshold = failure_threshold
        self.timeout = recovery_timeout

    def is_open(self) -> bool:
        """Returns True if circuit is broken (open)."""
        state = cache.get(self.key)
        return state == "OPEN"

    def record_failure(self):
        """Increments failure count, opens circuit if threshold met."""
        count_key = f"{self.key}:count"
        count = cache.incr(count_key) if cache.get(count_key) else cache.set(count_key, 1, timeout=self.timeout)

        # Need to re-fetch if incr returned None, but simple logic:
        # If incremented:
        if isinstance(count, int) and count >= self.threshold:
            cache.set(self.key, "OPEN", timeout=self.timeout)

    def record_success(self):
        """Resets failure count."""
        cache.delete(f"{self.key}:count")
