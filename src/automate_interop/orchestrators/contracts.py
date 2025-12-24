from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class StartResult:
    ok: bool
    execution_ref: str | None = None
    error: str | None = None
    meta: dict[str, Any] = None


@dataclass
class OrchestratorCapabilities:
    webhook_start: bool = False
    callback_supported: bool = False
    status_poll_supported: bool = False
    supports_templates_host: bool = False
    supports_import_export: bool = False


class ExternalOrchestrator(ABC):
    """
    Contract for interacting with external execution planes like n8n or Zapier.
    """

    @property
    @abstractmethod
    def capabilities(self) -> OrchestratorCapabilities:
        raise NotImplementedError

    @abstractmethod
    def start_run(self, request: dict[str, Any]) -> StartResult:
        """
        Start an execution.
        request must contain:
          - correlation_id
          - callback_url
          - payload
        """
        raise NotImplementedError

    @abstractmethod
    def verify_callback(self, request_payload: dict[str, Any], headers: dict[str, str]) -> bool:
        """
        Verify that a callback request genuinely came from this orchestrator.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self, execution_ref: str) -> dict[str, Any]:
        """
        Poll status if supported.
        """
        raise NotImplementedError
