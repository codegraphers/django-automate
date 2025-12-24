from django.apps import AppConfig


class AutomateModalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automate_modal'
    verbose_name = 'Multi-Modal Gateway'

    def ready(self):
        # Autodiscover providers
        from .providers.echo import EchoProvider
        from .providers.llm_bridge import LLMBridgeProvider
        from .providers.openai_audio import OpenAIAudioProvider
        from .providers.video import VideoPipelineProvider
        from .registry import ProviderRegistry

        ProviderRegistry.register(EchoProvider)
        ProviderRegistry.register(LLMBridgeProvider)
        ProviderRegistry.register(OpenAIAudioProvider)
        ProviderRegistry.register(VideoPipelineProvider)

        # Register Workflow Step

