import logging
import random
import time

from django.conf import settings

logger = logging.getLogger(__name__)

class ChaosModule:
    """
    SRE Failure Injection Module.
    Enabled via settings.AUTOMATE_CHAOS_ENABLED = True
    Configuration: settings.AUTOMATE_CHAOS_CONFIG
    """

    @staticmethod
    def is_enabled():
        return getattr(settings, "AUTOMATE_CHAOS_ENABLED", False)

    @classmethod
    def check_and_raise(cls, point: str, context: dict = None):
        """
        Hook to potentially trigger a failure at a specific execution point.
        Points: 'step:pre', 'step:post', 'db:commit', 'provider:call'
        """
        if not cls.is_enabled():
            return

        config = getattr(settings, "AUTOMATE_CHAOS_CONFIG", {})
        rules = config.get("rules", [])

        for rule in rules:
            if rule.get("point") == point:
                # Filter match?
                if context and rule.get("filter"):
                    # Simple key-value match
                    match = True
                    for k, v in rule["filter"].items():
                        if context.get(k) != v:
                            match = False
                            break
                    if not match:
                        continue

                # Probability check
                rate = rule.get("rate", 0.0)
                if random.random() < rate:
                    action = rule.get("action", "crash")
                    cls._trigger_failure(request_action=action, rule=rule)

    @classmethod
    def _trigger_failure(cls, request_action: str, rule: dict):
        logger.warning(f"CHAOS INJECTION TRIGGERED: {request_action} (Rule: {rule})")

        if request_action == "crash":
            raise SystemExit("CHAOS: Simulated Worker Crash")
        elif request_action == "exception":
            raise RuntimeError("CHAOS: Simulated Runtime Exception")
        elif request_action == "latency":
            duration = rule.get("duration_ms", 1000) / 1000.0
            time.sleep(duration)
