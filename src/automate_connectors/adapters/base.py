from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List

from ..errors import ConnectorError
from ..types import ActionSpec, ConnectorCapabilities

@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: List[str]

class ConnectorAdapter(ABC):
    """
    The Spine interface for all external integration connectors.
    Implementation must be stateless.
    """
    code: str # e.g. "shopify", "slack"

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_specs(self) -> Dict[str, ActionSpec]:
        """Returns the schema definition for all supported actions."""
        raise NotImplementedError

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """
        Validate that the provided configuration (non-secret + secret refs) 
        has the necessary fields.
        """
        raise NotImplementedError

    @abstractmethod
    def execute(self, action: str, input: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
        """
        Execute the action. 
        Exceptions must be normalized to ConnectorError.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize_error(self, exc: Exception) -> ConnectorError:
        """
        Map upstream exceptions to standardized ConnectorError taxonomy.
        """
        raise NotImplementedError
