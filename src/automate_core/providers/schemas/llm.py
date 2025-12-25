from typing import Any, Literal

from pydantic import BaseModel

# Minimal stable core for Chat

class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    name: str | None = None
    tool_calls: list[dict[str, Any]] | None = None # Keep flexible for now, or define strict ToolCall
    tool_call_id: str | None = None

class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float | None = 0.7
    max_output_tokens: int | None = None
    stop: list[str] | None = None
    stream: bool = False
    response_format: dict[str, Any] | None = None # e.g. {"type": "json_object"}
    tools: list[dict[str, Any]] | None = None

class ChatResponse(BaseModel):
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    usage: dict[str, int] | None = None # {prompt_tokens, completion_tokens}
    finish_reason: str | None = None
    model: str # The actual model used

class ChatStreamEvent(BaseModel):
    content_delta: str = ""
    tool_calls_delta: list[dict[str, Any]] | None = None
    finish_reason: str | None = None
