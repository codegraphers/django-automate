from __future__ import annotations
from typing import Any, Dict, List, Union

from .operators import OperatorRegistry

RuleNode = Union[Dict[str, Any], List[Any], str, int, float, bool]

class RuleEngine:
    """
    Safe evaluation of JSON rules against a context.
    Supported structure: { "operator": [arg1, arg2] } or { "var": "path.to.val" }
    """
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth

    def evaluate(self, rule: RuleNode, context: Dict[str, Any]) -> Any:
        return self._eval(rule, context, 0)

    def _eval(self, node: RuleNode, context: Dict[str, Any], depth: int) -> Any:
        if depth > self.max_depth:
            raise RecursionError("Rule depth limit exceeded")

        # 1. Literal
        if not isinstance(node, dict):
            return node

        # 2. Variable Access
        if "var" in node:
            path = node["var"]
            return self._resolve_path(path, context)

        # 3. Operator
        # Expect exactly one key which is the operator
        keys = list(node.keys())
        if len(keys) != 1:
             # Fallback: treat as literal dict if not recognized operator pattern
             return node
             
        op_name = keys[0]
        args = node[op_name]
        
        op_func = OperatorRegistry.get(op_name)
        if not op_func:
            return node # Treat as literal? Or raise error? Strict mode -> Error.
            
        if not isinstance(args, list):
            args = [args]
            
        evaluated_args = [self._eval(arg, context, depth + 1) for arg in args]
        
        try:
            return op_func(*evaluated_args)
        except Exception:
            return False

    def _resolve_path(self, path: str, context: Dict[str, Any]) -> Any:
        """
        Safe dot-notation access. 
        Only allow access to 'event.*' and 'ctx.*' as per requirements.
        """
        parts = path.split(".")
        root = parts[0]
        if root not in ["event", "ctx"]:
             return None # Restricted access
             
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
