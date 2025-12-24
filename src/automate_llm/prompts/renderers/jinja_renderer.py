from __future__ import annotations
from typing import Any, Dict, List
from jinja2 import sandbox

from .base import PromptRenderer
from ...types import ChatMessage

class JinjaRenderer(PromptRenderer):
    code = "jinja"

    def render(self, *, template: Any, inputs: Dict[str, Any]) -> Any:
        # Basic Safe Jinja2 rendering stub
        env = sandbox.SandboxedEnvironment()
        if isinstance(template, str):
            rendered = env.from_string(template).render(**inputs)
            # Simplistic assumption: template makes user message
            return [ChatMessage(role="user", content=rendered)]
        raise NotImplementedError("Complex Jinja2 template handling not implemented")
