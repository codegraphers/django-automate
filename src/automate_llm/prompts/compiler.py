from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..registry import get_renderer_cls
from ..types import ChatRequest, CompiledPrompt, ToolSpec, ChatMessage
from ..errors import LLMError, LLMErrorCode

@dataclass(frozen=True)
class PromptVersionSnapshot:
    prompt_key: str
    version: str
    template_type: str
    messages_json: Optional[Any] = None
    template: Optional[str] = None
    input_schema_json: Optional[Dict[str, Any]] = None
    output_schema_json: Optional[Dict[str, Any]] = None
    default_params_json: Optional[Dict[str, Any]] = None
    tool_specs_json: Optional[List[Dict[str, Any]]] = None
    policy_hints_json: Optional[Dict[str, Any]] = None

class PromptCompiler:
    def __init__(self) -> None:
        pass

    def validate_inputs(self, schema: Optional[Dict[str, Any]], inputs: Dict[str, Any]) -> None:
        # TODO: JSON schema validation (fast + safe error messages)
        return

    def build_tools(self, tool_specs_json: Optional[List[Dict[str, Any]]]) -> List[ToolSpec]:
        tools: List[ToolSpec] = []
        for t in (tool_specs_json or []):
            tools.append(
                ToolSpec(
                    name=t["name"],
                    description=t.get("description", ""),
                    input_schema=t.get("input_schema", {}),
                )
            )
        return tools

    def compile(
        self,
        *,
        provider: str,
        model: str,
        prompt_ver: PromptVersionSnapshot,
        inputs: Dict[str, Any],
        timeout_s: int,
        trace_id: Optional[str],
    ) -> CompiledPrompt:
        self.validate_inputs(prompt_ver.input_schema_json, inputs)

        renderer_cls = get_renderer_cls(prompt_ver.template_type)
        renderer = renderer_cls()

        template_payload = prompt_ver.messages_json if prompt_ver.template_type == "chat_messages" else prompt_ver.template
        
        # Determine messages from renderer
        rendered_output = renderer.render(template=template_payload, inputs=inputs)
        
        # Ensure it's a list of ChatMessage
        messages: List[ChatMessage] = []
        if isinstance(rendered_output, list):
             messages = rendered_output # Assume type is correct for now
        else:
             # Basic handling for single string return
             messages = [ChatMessage(role="user", content=str(rendered_output))]

        tools = self.build_tools(prompt_ver.tool_specs_json)
        params = prompt_ver.default_params_json or {}

        req = ChatRequest(
            model=model,
            messages=messages,
            tools=tools,
            temperature=params.get("temperature"),
            top_p=params.get("top_p"),
            max_tokens=params.get("max_tokens"),
            timeout_s=timeout_s,
            metadata={
                "trace_id": trace_id,
                "prompt_key": prompt_ver.prompt_key,
                "prompt_version": prompt_ver.version,
                "provider": provider,
            },
        )
        return CompiledPrompt(request=req, warnings=[])
