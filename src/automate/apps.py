from django.apps import AppConfig


class AutomateConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "automate"
    verbose_name = "Django Automate"

    def ready(self):
        from django.apps import apps
        from django.conf import settings
        from django.db.models.signals import post_save

        from .signals import model_change_handler

        watched_models = getattr(settings, 'AUTOMATE_WATCHED_MODELS', [])
        for model_path in watched_models:
            try:
                model = apps.get_model(model_path)
                post_save.connect(model_change_handler, sender=model)
            except LookupError:
                pass

        # Connectors moved to automate_connectors
        pass

