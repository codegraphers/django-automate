from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings
from .ingestion import EventIngestionService

# We can allow users to configure WHICH models to watch via settings
# AUTOMATE_WATCHED_MODELS = ['app.ModelName', ...]

def get_watched_models():
    watched = getattr(settings, 'AUTOMATE_WATCHED_MODELS', [])
    for model_path in watched:
        try:
            yield apps.get_model(model_path)
        except LookupError:
            continue

def model_change_handler(sender, instance, created, **kwargs):
    # Retrieve watched models dynamically to avoid import-time side effects
    # For now, let's assume we watch everything registered explicitly? 
    # Or we can just have a decorator/mixin.
    # For MVP, let's just provide the handler and let user connect it manually 
    # OR connect to settings-defined models in AppConfig.ready()
    
    action = "created" if created else "updated"
    model_name = sender._meta.label
    
    payload = {
        "model": model_name,
        "pk": str(instance.pk),
        "action": action,
        # TODO: Serialize instance data (carefully)
        "data": str(instance) 
    }
    
    # P0.3: Deterministic Idempotency Key
    # Format: signal-{model}-{pk}-{action}
    # This ensures that for a given model instance and action, we only process it once.
    # Note: For 'updated', this means we process it ONCE per model instance update globally.
    # If users want to process updates repeatedly, they need a time-bucket or change-hash.
    # For now, strict global dedupe prevents event storms.
    
    idempotency_key = f"signal-{model_name}-{instance.pk}-{action}"
    
    EventIngestionService.ingest_event(
        event_type=f"model.{model_name}.{action}",
        source="django_signal",
        payload=payload,
        idempotency_key=idempotency_key
    )

# Note: Actual connection of this signal happens in apps.py based on settings
from django.utils import timezone
