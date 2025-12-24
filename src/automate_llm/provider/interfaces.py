from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class CompletionRequest:
    model: str
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}]
    temperature: float = 0.7
    max_tokens: int = 1000
    stop: Optional[List[str]] = None
    stream: bool = False

@dataclass
class CompletionResponse:
    content: str
    usage: Dict[str, int]  # {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    model_used: str
    raw_response: Dict[str, Any]

class LLMProvider(ABC):
    """
    Abstract interface for LLM backends.
    """
    
    @abstractmethod
    def chat_complete(self, request: CompletionRequest) -> CompletionResponse:
        """
        Synchronous chat completion.
        Should handle retries internally or raise typed exceptions.
        """
        raise NotImplementedError

    @abstractmethod
    def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count for governance checks.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError
