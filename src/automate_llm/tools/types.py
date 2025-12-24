from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    func: Callable[..., Any]
    schema: dict[str, Any]
    timeout_s: int | None = None
