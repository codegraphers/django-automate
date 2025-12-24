from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

class RunStore(ABC):
    """
    Abstract storage so you can:
      - use Django ORM models by default
      - optionally swap to external stores in future
    """

    @abstractmethod
    def create_run(self, payload: Dict[str, Any], *, idempotency_key: Optional[str]) -> Dict[str, Any]:
        """Creates a run record in PENDING state"""
        raise NotImplementedError

    @abstractmethod
    def mark_running(self, run_id: int) -> None:
        """Transitions run to RUNNING state"""
        raise NotImplementedError

    @abstractmethod
    def mark_succeeded(self, run_id: int, result: Dict[str, Any]) -> None:
        """Transitions run to SUCCEEDED state and stores result"""
        raise NotImplementedError

    @abstractmethod
    def mark_failed(self, run_id: int, error: Dict[str, Any]) -> None:
        """Transitions run to FAILED state and stores error"""
        raise NotImplementedError

    @abstractmethod
    def get_run(self, run_id: int) -> Dict[str, Any]:
        """Retrieves run details"""
        raise NotImplementedError
