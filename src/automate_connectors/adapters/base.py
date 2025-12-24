from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from ..errors import ConnectorError
from ..types import ActionSpec, ConnectorCapabilities


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: list[str]


class ConnectorAdapter(ABC):
    """
    The Spine interface for all external integration connectors.
    Implementation must be stateless.
    """

    code: str  # e.g. "shopify", "slack"

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        raise NotImplementedError

    @property
    @abstractmethod
    def action_specs(self) -> dict[str, ActionSpec]:
        """Returns the schema definition for all supported actions."""
        raise NotImplementedError

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        """
        Validate that the provided configuration (non-secret + secret refs)
        has the necessary fields.
        """
        raise NotImplementedError

    @property
    def config_schema(self) -> dict[str, Any]:
        return {}

    @abstractmethod
    def execute(self, action: str, input: dict[str, Any], ctx: dict[str, Any]) -> Any:
        """
        Execute the action.
        Exceptions must be normalized to ConnectorError.
        """
        raise NotImplementedError

    @property
    def slug(self) -> str:
        return self.code

    def redact(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Redact sensitive keys from a dictionary.
        Default implementation: fuzzy match common secret keys.
        """
        redacted = data.copy()

        SENSITIVE_KEYS = {"token", "key", "secret", "password", "authorization", "auth"}

        for k, _v in redacted.items():
            if not isinstance(k, str):
                continue

            # 1. Exact or partial match on key
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                redacted[k] = "***REDACTED***"

        return redacted

    @abstractmethod
    def normalize_error(self, exc: Exception) -> ConnectorError:
        """
        Map upstream exceptions to standardized ConnectorError taxonomy.
        """
        raise NotImplementedError
