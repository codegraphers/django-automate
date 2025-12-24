from django.apps import AppConfig


class AutomateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automate"
    verbose_name = "Django Automate"

    def ready(self):
        from django.apps import apps  # noqa: PLC0415
        from django.conf import settings  # noqa: PLC0415
        from django.db.models.signals import post_save  # noqa: PLC0415

        from .signals import model_change_handler  # noqa: PLC0415

        watched_models = getattr(settings, "AUTOMATE_WATCHED_MODELS", [])
        for model_path in watched_models:
            try:
                model = apps.get_model(model_path)
                post_save.connect(model_change_handler, sender=model)
            except LookupError:
                pass

        # Connectors moved to automate_connectors
        pass
