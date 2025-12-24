from typing import Any, Dict
from django.db.models.signals import post_save
from django.db import models

from .emit import emit_event

# Function to be connected to post_save signals for monitored models
def model_signal_handler(sender: Any, instance: models.Model, created: bool, **kwargs: Any) -> None:
    # Need to determine tenant context. 
    # Usually signals are global, so filtering/context extraction is needed.
    # For now, we assume models have tenant_id.
    
    tenant_id = getattr(instance, "tenant_id", "default")
    
    # Check if a Trigger exists for this model signal (Optimization: cache this check)
    # from .specs import TriggerSpec
    # if not TriggerSpec.objects.filter(kind="SIGNAL", config__model=sender._meta.label).exists():
    #     return

    event_type = f"{sender._meta.label_lower}.{'created' if created else 'updated'}"
    
    payload = {}
    try:
        # Simple serialization
        for field in instance._meta.fields:
            if field.name not in ["password", "secret"]:
                val = getattr(instance, field.name)
                payload[field.name] = str(val) # simplify
    except Exception:
        pass

    emit_event(
        tenant_id=tenant_id,
        event_type=event_type,
        source="signal",
        payload=payload
    )
