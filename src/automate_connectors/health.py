from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class HealthCheckResult:
    ok: bool
    latency_ms: float | None = None
    error: str | None = None
    meta: dict[str, Any] = None

class ConnectionHealthCheck(ABC):
    """
    Contract for probing the liveness/validity of a connection profile.
    """
    @abstractmethod
    def check(self, config: dict[str, Any], secrets: dict[str, Any]) -> HealthCheckResult:
        raise NotImplementedError
