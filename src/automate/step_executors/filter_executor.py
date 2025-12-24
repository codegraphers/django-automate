"""
Filter/Condition Step Executor

Evaluates conditions using JSON Logic and determines if workflow should continue.
"""
import time
import logging
from typing import Dict, Any

from .base import BaseStepExecutor, StepContext, StepResult, register_step_executor

logger = logging.getLogger(__name__)


@register_step_executor("filter")
class FilterStepExecutor(BaseStepExecutor):
    """
    Evaluate a condition and decide whether to continue.
    
    Config:
        condition: dict - JSON Logic condition
        on_fail: str - "stop" (default), "continue", "branch_id"
        
    Example conditions (JSON Logic):
        {">=": [{"var": "event.payload.amount"}, 100]}
        {"and": [{"==": [{"var": "event.type"}, "order"]}, {">": [{"var": "event.payload.total"}, 50]}]}
    """
    
    def validate_config(self) -> bool:
        return "condition" in self.config
    
    def execute(self, context: StepContext) -> StepResult:
        start_time = time.time()
        
        try:
            condition = self.config.get("condition", {})
            on_fail = self.config.get("on_fail", "stop")
            
            # Build data context for JSON Logic
            data = {
                "event": {"payload": context.event_payload},
                "previous": context.previous_outputs,
            }
            
            # Evaluate using json_logic_lite (or fallback to simple eval)
            result = self._evaluate_condition(condition, data)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result:
                return StepResult(
                    success=True,
                    output={"passed": True, "condition_result": result},
                    duration_ms=duration_ms,
                    metadata={"on_fail": on_fail}
                )
            else:
                # Condition failed
                if on_fail == "stop":
                    return StepResult(
                        success=False,
                        output={"passed": False, "action": "stopped"},
                        error="Condition not met - workflow stopped",
                        duration_ms=duration_ms
                    )
                elif on_fail == "continue":
                    return StepResult(
                        success=True,
                        output={"passed": False, "action": "continued"},
                        duration_ms=duration_ms
                    )
                else:
                    # Branch to a specific step
                    return StepResult(
                        success=True,
                        output={"passed": False, "action": "branch", "branch_to": on_fail},
                        duration_ms=duration_ms
                    )
                    
        except Exception as e:
            logger.exception(f"Filter evaluation failed: {e}")
            return StepResult(
                success=False,
                output=None,
                error=str(e)
            )
    
    def _evaluate_condition(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Evaluate JSON Logic condition.
        
        Falls back to a simple implementation if json_logic is not installed.
        """
        try:
            # Try to use json_logic package
            from json_logic import jsonLogic
            return jsonLogic(condition, data)
        except ImportError:
            # Fallback to simple evaluation
            return self._simple_evaluate(condition, data)
    
    def _simple_evaluate(self, condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Simple JSON Logic evaluator for common operations."""
        if not condition:
            return True
            
        for op, args in condition.items():
            if op == "var":
                return self._get_var(args, data)
            elif op == "==":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return left == right
            elif op == "!=":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return left != right
            elif op == ">":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return float(left) > float(right)
            elif op == ">=":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return float(left) >= float(right)
            elif op == "<":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return float(left) < float(right)
            elif op == "<=":
                left = self._resolve_arg(args[0], data)
                right = self._resolve_arg(args[1], data)
                return float(left) <= float(right)
            elif op == "and":
                return all(self._simple_evaluate(arg, data) for arg in args)
            elif op == "or":
                return any(self._simple_evaluate(arg, data) for arg in args)
            elif op == "not":
                return not self._simple_evaluate(args[0], data)
            elif op == "in":
                needle = self._resolve_arg(args[0], data)
                haystack = self._resolve_arg(args[1], data)
                return needle in haystack
            else:
                logger.warning(f"Unknown JSON Logic operator: {op}")
                return False
        
        return False
    
    def _resolve_arg(self, arg: Any, data: Dict[str, Any]) -> Any:
        """Resolve an argument which could be a literal or a var reference."""
        if isinstance(arg, dict) and "var" in arg:
            return self._get_var(arg["var"], data)
        return arg
    
    def _get_var(self, path: str, data: Dict[str, Any]) -> Any:
        """Get a nested variable from data using dot notation."""
        parts = path.split(".")
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value
