from __future__ import annotations

from typing import Any

from ...types import ChatMessage
from .base import PromptRenderer


class ChatMessagesRenderer(PromptRenderer):
    code = "chat_messages"

    def render(self, *, template: Any, inputs: dict[str, Any]) -> Any:
        """
        template is expected to be a list of {role, content} with optional {{var}} expansions done earlier.
        For now, assume messages_json already resolved or contains minimal placeholders.
        """
        msgs: list[ChatMessage] = []
        for m in template or []:
            msgs.append(ChatMessage(role=m["role"], content=str(m.get("content", ""))))
        return msgs
