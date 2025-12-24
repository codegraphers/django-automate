from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PromptRenderer(ABC):
    code: str  # "chat_messages", "jinja", "python_renderer"

    @abstractmethod
    def render(self, *, template: Any, inputs: dict[str, Any]) -> Any:
        """
        Returns provider-neutral chat messages structure (later compiled into ChatRequest).
        """
        raise NotImplementedError
