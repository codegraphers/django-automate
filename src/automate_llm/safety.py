from __future__ import annotations
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class HookResult:
    allowed: bool
    modified_payload: Optional[Any] = None
    rejection_reason: Optional[str] = None

class SafetyHook(ABC):
    @abstractmethod
    def run(self, ctx: Dict[str, Any], payload: Any) -> HookResult:
        pass

class SafetyPipeline:
    def __init__(self, hooks: List[SafetyHook]) -> None:
        self.hooks = hooks

    def process(self, ctx: Dict[str, Any], payload: Any) -> HookResult:
        current_payload = payload
        for hook in self.hooks:
            res = hook.run(ctx, current_payload)
            if not res.allowed:
                return res
            if res.modified_payload is not None:
                current_payload = res.modified_payload
        return HookResult(allowed=True, modified_payload=current_payload)
