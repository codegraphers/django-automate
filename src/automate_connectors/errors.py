from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ConnectorErrorCode(str, Enum):
    AUTH_FAILED = "AUTH_FAILED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    TIMEOUT = "TIMEOUT"
    UPSTREAM_5XX = "UPSTREAM_5XX"
    INVALID_INPUT = "INVALID_INPUT"
    CONFIG_INVALID = "CONFIG_INVALID"
    TRANSIENT_NETWORK = "TRANSIENT_NETWORK"
    INTERNAL_ERROR = "INTERNAL_ERROR"

@dataclass
class ConnectorError(Exception):
    code: ConnectorErrorCode
    message_safe: str
    retryable: bool = False
    details_safe: dict[str, Any] | None = None
    connector_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message_safe,
            "retryable": self.retryable,
            "details": self.details_safe or {},
            "connector": self.connector_code
        }
