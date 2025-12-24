from django.apps import AppConfig


class AutomateLLMConfig(AppConfig):
    name = "automate_llm"  # Matching the actual package name in src
    label = "automate_llm"
    verbose_name = "Automate LLM"

    def ready(self) -> None:
        # Load adapter/tool/prompt renderer plugins via entry_points
        from .registry import load_entrypoint_plugins

        load_entrypoint_plugins()
