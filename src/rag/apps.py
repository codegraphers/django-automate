from django.apps import AppConfig


class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag'
    verbose_name = 'RAG (Retrieval)'

    def ready(self):
        # Register providers on startup
        from rag.providers import registry
        registry.autodiscover()
