import jsonschema
from django.core.exceptions import ValidationError

from ..models import Event, TriggerSpec, TriggerTypeChoices


class TriggerMatchingService:
    """
    P0.4: Strict Trigger Matching Service.
    Eliminates accidental runs by enforcing strict type checks.
    """

    def validate_config(self, trigger: TriggerSpec):
        """
        P0.4: Validate TriggerSpec.config by JSONSchema.
        """
        if trigger.type == TriggerTypeChoices.MODEL_SIGNAL:
            schema = {
                "type": "object",
                "properties": {
                    "model": {"type": "string", "pattern": r"^\w+\.\w+$"},
                    "action": {"type": "string", "enum": ["created", "updated", "deleted"]},
                },
                "required": ["model"],
            }
            try:
                jsonschema.validate(instance=trigger.config, schema=schema)
            except jsonschema.ValidationError as e:
                raise ValidationError(f"Invalid config for model_signal: {e.message}")

        elif trigger.type == TriggerTypeChoices.WEBHOOK:
            # Basic webhook config might require a custom slug if we implement dedicated endpoints
            pass

    def matches(self, trigger: TriggerSpec, event: Event) -> bool:
        if trigger.type == TriggerTypeChoices.MODEL_SIGNAL:
            return self._match_model_signal(trigger, event)
        elif trigger.type == TriggerTypeChoices.WEBHOOK:
            return self._match_webhook(trigger, event)
        elif trigger.type == TriggerTypeChoices.MANUAL:
            return self._match_manual(trigger, event)
        elif trigger.type == TriggerTypeChoices.SCHEDULE:
            # Schedules are processed by celery beat, not event stream usually?
            # Or event stream "schedule.tick"?
            # For now, safe default is False or specific match if we have schedule events.
            return event.event_type == "schedule.tick"

        return False

    def _match_model_signal(self, trigger: TriggerSpec, event: Event) -> bool:
        # Event type: model.app.Model.action
        # Config: {"model": "app.Model", "action": "created|updated"}

        if not event.event_type.startswith("model."):
            return False

        parts = event.event_type.split(".")
        if len(parts) < 4:
            return False

        app_label = parts[1]
        model_name = parts[2]
        action = parts[3]
        model_full = f"{app_label}.{model_name}"

        conf = trigger.config

        # Strict validation: Model MUST match if configured (it should be configured)
        req_model = conf.get("model")
        if not req_model:
            # If config is empty, we shouldn't match anything for safety?
            # Or match all models? Safety says no.
            return False

        if req_model != model_full:
            return False

        # Action is optional, defaults to all actions for that model?
        # Or strict? "optional model label" in prompt implies model is optional?
        # No, "optional model label" means label is one of the matching criteria.
        # Let's support optional action filter.
        req_action = conf.get("action")
        return not (req_action and req_action != action)

    def _match_webhook(self, trigger: TriggerSpec, event: Event) -> bool:
        # Event type: webhook
        # TODO: Match specific webhook ID if we have multiple endpoints?
        # For now, strict type check.
        return event.event_type == "webhook"

    def _match_manual(self, trigger: TriggerSpec, event: Event) -> bool:
        # Event type: manual
        return event.event_type == "manual"
