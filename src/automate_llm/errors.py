from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

class LLMErrorCode(str, Enum):
    POLICY_VIOLATION = "LLM_POLICY_VIOLATION"
    RATE_LIMITED = "LLM_RATE_LIMITED"
    TIMEOUT = "LLM_TIMEOUT"
    PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
    BAD_REQUEST = "LLM_BAD_REQUEST"
    OUTPUT_INVALID = "LLM_OUTPUT_INVALID"
    CANCELLED = "LLM_CANCELLED"
    INTERNAL_ERROR = "LLM_INTERNAL_ERROR"

@dataclass
class LLMError(Exception):
    code: LLMErrorCode
    message_safe: str
    retryable: bool = False
    details_safe: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None

    def to_error_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message_safe,
            "retryable": self.retryable,
            "details": self.details_safe or {},
            "provider": self.provider,
        }
