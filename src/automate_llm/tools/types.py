from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

@dataclass(frozen=True)
class ToolDefinition:
    name: str
    func: Callable[..., Any]
    schema: Dict[str, Any]
    timeout_s: Optional[int] = None
