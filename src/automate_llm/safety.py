from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class HookResult:
    allowed: bool
    modified_payload: Any | None = None
    rejection_reason: str | None = None


class SafetyHook(ABC):
    @abstractmethod
    def run(self, ctx: dict[str, Any], payload: Any) -> HookResult:
        pass


class SafetyPipeline:
    def __init__(self, hooks: list[SafetyHook]) -> None:
        self.hooks = hooks

    def process(self, ctx: dict[str, Any], payload: Any) -> HookResult:
        current_payload = payload
        for hook in self.hooks:
            res = hook.run(ctx, current_payload)
            if not res.allowed:
                return res
            if res.modified_payload is not None:
                current_payload = res.modified_payload
        return HookResult(allowed=True, modified_payload=current_payload)
