from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

@dataclass
class StartResult:
    ok: bool
    execution_ref: Optional[str] = None
    error: Optional[str] = None
    meta: Dict[str, Any] = None

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
    def start_run(self, request: Dict[str, Any]) -> StartResult:
        """
        Start an execution.
        request must contain:
          - correlation_id
          - callback_url
          - payload
        """
        raise NotImplementedError

    @abstractmethod
    def verify_callback(self, request_payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Verify that a callback request genuinely came from this orchestrator.
        """
        raise NotImplementedError

    @abstractmethod
    def get_status(self, execution_ref: str) -> Dict[str, Any]:
        """
        Poll status if supported.
        """
        raise NotImplementedError
