from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional, Sequence, List

Role = Literal["system", "user", "assistant", "tool"]

@dataclass(frozen=True)
class ChatMessage:
    role: Role
    content: str
    name: Optional[str] = None

@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]  # JSON Schema

@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None

@dataclass(frozen=True)
class CostEstimate:
    currency: str = "USD"
    estimated_cost: float = 0.0
    token_estimate_in: Optional[int] = None
    token_estimate_out: Optional[int] = None

@dataclass(frozen=True)
class Usage:
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    total_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    provider_request_id: Optional[str] = None

@dataclass(frozen=True)
class ChatRequest:
    model: str
    messages: Sequence[ChatMessage]
    tools: Sequence[ToolSpec] = field(default_factory=list)
    tool_choice: Optional[str] = None  # e.g. "auto" / tool name
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout_s: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)  # trace_id, prompt_version, etc.

@dataclass(frozen=True)
class ChatResponse:
    output_text: str
    usage: Usage = field(default_factory=Usage)
    tool_calls: Sequence[ToolCall] = field(default_factory=list)
    raw_provider_payload: Optional[Dict[str, Any]] = None  # stored only if policy allows

@dataclass(frozen=True)
class CompiledPrompt:
    request: ChatRequest
    warnings: List[str] = field(default_factory=list)
