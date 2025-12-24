from __future__ import annotations
from typing import Any, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class HealthCheckResult:
    ok: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = None

class ConnectionHealthCheck(ABC):
    """
    Contract for probing the liveness/validity of a connection profile.
    """
    @abstractmethod
    def check(self, config: Dict[str, Any], secrets: Dict[str, Any]) -> HealthCheckResult:
        raise NotImplementedError
