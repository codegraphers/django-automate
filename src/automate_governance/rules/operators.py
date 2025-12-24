from __future__ import annotations
from typing import Any, Callable, Dict

OperatorFunc = Callable[[Any, Any], bool]

class OperatorRegistry:
    """
    Allowlist of safe operators for JSONLogic-like rules.
    Prevents arbitrary code execution by restricting available ops.
    """
    _ops: Dict[str, OperatorFunc] = {}

    @classmethod
    def register(cls, name: str, func: OperatorFunc) -> None:
        cls._ops[name] = func

    @classmethod
    def get(cls, name: str) -> OperatorFunc:
        return cls._ops.get(name)

# Default Safe Ops
def op_eq(a: Any, b: Any) -> bool: return a == b
def op_neq(a: Any, b: Any) -> bool: return a != b
def op_gt(a: Any, b: Any) -> bool: return float(a) > float(b)
def op_lt(a: Any, b: Any) -> bool: return float(a) < float(b)
def op_in(a: Any, b: Any) -> bool: return a in b
def op_contains(a: Any, b: Any) -> bool: return b in a

OperatorRegistry.register("==", op_eq)
OperatorRegistry.register("!=", op_neq)
OperatorRegistry.register(">", op_gt)
OperatorRegistry.register("<", op_lt)
OperatorRegistry.register("in", op_in)
OperatorRegistry.register("contains", op_contains)
