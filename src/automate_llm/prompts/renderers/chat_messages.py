from __future__ import annotations
from typing import Any, Dict, List

from .base import PromptRenderer
from ...types import ChatMessage

class ChatMessagesRenderer(PromptRenderer):
    code = "chat_messages"

    def render(self, *, template: Any, inputs: Dict[str, Any]) -> Any:
        """
        template is expected to be a list of {role, content} with optional {{var}} expansions done earlier.
        For now, assume messages_json already resolved or contains minimal placeholders.
        """
        msgs: List[ChatMessage] = []
        for m in template or []:
            msgs.append(ChatMessage(role=m["role"], content=str(m.get("content", ""))))
        return msgs
