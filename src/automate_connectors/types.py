from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionSpec:
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema
    output_schema: dict[str, Any] | None = None # JSON Schema
    side_effects: bool = False
    idempotent: bool = False

@dataclass(frozen=True)
class ConnectorResult:
    status: str = "success" # success, failed
    data: Any = None # Structured result
    meta: dict[str, Any] = field(default_factory=dict) # pagination tokens, usage info

@dataclass(frozen=True)
class ConnectorCapabilities:
    supports_webhooks: bool = False
    supports_polling: bool = False
    supports_batch: bool = False
    supports_idempotency_key: bool = False
    supports_oauth: bool = False
    supports_rate_limit_headers: bool = False
