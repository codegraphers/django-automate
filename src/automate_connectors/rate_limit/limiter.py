from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RateLimitState:
    is_allowed: bool
    retry_after_ms: int = 0
    remaining: int = 0

class RateLimiter(ABC):
    @abstractmethod
    def acquire(self, key: str, cost: int = 1) -> RateLimitState:
        """Atomic check-and-consume."""
        raise NotImplementedError

    @abstractmethod
    def release(self, key: str, cost: int = 1) -> None:
        """Optional rollback (e.g. on 429 when dynamic)."""
        pass

class InMemoryRateLimiter(RateLimiter):
    """
    Simple Token Bucket for local dev / testing.
    Not concurrency safe across multiple worker processes.
    """
    def __init__(self, rate_hertz: float = 1.0, burst: int = 1):
        self.rate = rate_hertz  # tokens per second
        self.burst = burst
        self._tokens = {} # key -> float
        self._last_update = {} # key -> timestamp

    def acquire(self, key: str, cost: int = 1) -> RateLimitState:
        now = time.time()
        tokens = self._tokens.get(key, self.burst)
        last_ts = self._last_update.get(key, now)

        # Refill
        delta = now - last_ts
        tokens = min(self.burst, tokens + delta * self.rate)

        if tokens >= cost:
            self._tokens[key] = tokens - cost
            self._last_update[key] = now
            return RateLimitState(is_allowed=True, remaining=int(tokens-cost))
        else:
            # Need (cost - tokens) more
            # Rate * wait = missing
            missing = cost - tokens
            wait_sec = missing / self.rate
            self._tokens[key] = tokens # don't check out
            self._last_update[key] = now
            return RateLimitState(is_allowed=False, retry_after_ms=int(wait_sec * 1000))
