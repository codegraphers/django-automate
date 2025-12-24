from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RunStore(ABC):
    """
    Abstract storage so you can:
      - use Django ORM models by default
      - optionally swap to external stores in future
    """

    @abstractmethod
    def create_run(self, payload: dict[str, Any], *, idempotency_key: str | None) -> dict[str, Any]:
        """Creates a run record in PENDING state"""
        raise NotImplementedError

    @abstractmethod
    def mark_running(self, run_id: int) -> None:
        """Transitions run to RUNNING state"""
        raise NotImplementedError

    @abstractmethod
    def mark_succeeded(self, run_id: int, result: dict[str, Any]) -> None:
        """Transitions run to SUCCEEDED state and stores result"""
        raise NotImplementedError

    @abstractmethod
    def mark_failed(self, run_id: int, error: dict[str, Any]) -> None:
        """Transitions run to FAILED state and stores error"""
        raise NotImplementedError

    @abstractmethod
    def get_run(self, run_id: int) -> dict[str, Any]:
        """Retrieves run details"""
        raise NotImplementedError
