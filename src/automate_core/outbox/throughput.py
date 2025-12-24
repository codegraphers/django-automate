from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TenantHealth:
    is_paused: bool
    error_count: int


class ThroughputController:
    """
    Manages per-tenant rate limits and backpressure.
    Stub implementation for now; enforces Max Inflight only.
    """

    def __init__(self, max_inflight: int = 200, qps: int = 10):
        self.max_inflight = max_inflight
        self.qps = qps

    def can_claim(self, tenant_id: str, current_inflight_count: int) -> bool:
        if current_inflight_count >= self.max_inflight:
            return False

        # TODO: Check Token Bucket for QPS
        # TODO: Check Circuit Breaker (is_paused?)
        return True

    def record_success(self, tenant_id: str) -> None:
        pass

    def record_error(self, tenant_id: str) -> None:
        pass
