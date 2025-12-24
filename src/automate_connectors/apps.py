from django.apps import AppConfig


class AutomateConnectorsConfig(AppConfig):
    name = "automate_connectors"
    label = "automate_connectors"
    def ready(self):
        from automate.registry import registry as core_registry
        from .registry import register_connector
        
        from .adapters.slack import SlackAdapter
        from .adapters.logging import LoggingAdapter

        # Register in Core Registry (for Runtime)
        core_registry.register_connector(SlackAdapter.code, SlackAdapter)
        core_registry.register_connector(LoggingAdapter.code, LoggingAdapter)

        # Register in Local Registry (for Connectors App)
        register_connector(SlackAdapter)
        register_connector(LoggingAdapter)
