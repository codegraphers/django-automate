from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]

@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str
    name: str | None = None

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema

@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    id: str | None = None

@dataclass(frozen=True)
class CostEstimate:
    currency: str = "USD"
    estimated_cost: float = 0.0
    token_estimate_in: int | None = None
    token_estimate_out: int | None = None

@dataclass(frozen=True)
class Usage:
    tokens_in: int | None = None
    tokens_out: int | None = None
    total_tokens: int | None = None
    cost_usd: float | None = None
    provider_request_id: str | None = None

@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: Sequence[ChatMessage]
    tools: Sequence[ToolSpec] = field(default_factory=list)
    tool_choice: str | None = None  # e.g. "auto" / tool name
    temperature: float | None = None
    top_p: float | None = None
    max_tokens: int | None = None
    timeout_s: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)  # trace_id, prompt_version, etc.

@dataclass(frozen=True)
class ChatResponse:
    output_text: str
    usage: Usage = field(default_factory=Usage)
    tool_calls: Sequence[ToolCall] = field(default_factory=list)
    raw_provider_payload: dict[str, Any] | None = None  # stored only if policy allows

@dataclass(frozen=True)
class CompiledPrompt:
    request: ChatRequest
    warnings: list[str] = field(default_factory=list)
