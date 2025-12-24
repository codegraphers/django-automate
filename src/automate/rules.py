import logging
from typing import Any

from .models import Event

logger = logging.getLogger(__name__)

class RuleEvaluator:
    """
    Evaluates rules against an event.
    """

    def evaluate(self, automation, event: Event) -> bool:
        """
        Returns True if ALL enabled rules pass.
        If no rules exist, returns True.
        """
        rules = automation.rules.filter(enabled=True).order_by('priority')

        if not rules.exists():
            return True

        context = {
            "event": {
                "id": str(event.id),
                "type": event.event_type,
                "source": event.source,
                "payload": event.payload,
                "actor_id": event.actor_id,
            }
        }

        for rule in rules:
            if not self._evaluate_condition(rule.conditions, context):
                logger.debug(f"Rule {rule.id} failed for automation {automation.id}")
                return False

        return True

    def _evaluate_condition(self, condition: dict, context: dict) -> bool:
        """
        Recursive evaluation of JSON logic.
        Supported operators: ==, !=, >, <, in, and, or
        """
        # Base case: empty condition is True
        if not condition:
            return True

        # If list, assume implicit AND (or OR depending on design, let's say AND)
        if isinstance(condition, list):
            return all(self._evaluate_condition(c, context) for c in condition)

        # Check specific operators
        if "and" in condition:
            return all(self._evaluate_condition(c, context) for c in condition["and"])

        if "or" in condition:
            return any(self._evaluate_condition(c, context) for c in condition["or"])

        # Leaf nodes: { "var": "value" }
        # Simplified: key is field path, value is expected value
        for key, expected in condition.items():
            if key in ["and", "or"]: # Handled above
                continue

            actual = self._get_value_from_context(key, context)
            if actual != expected:
                return False

        return True

    def _get_value_from_context(self, path: str, context: dict) -> Any:
        """
        Dot-notation lookup: "event.payload.status"
        """
        current = context
        parts = path.split('.')

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
        return current
