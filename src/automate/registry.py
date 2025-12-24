import logging

logger = logging.getLogger(__name__)


class Registry:
    """
    Central registry for pluggable components (Connectors, Triggers, Providers).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.connectors = {}
            cls._instance.triggers = {}
            cls._instance.llm_providers = {}
        return cls._instance

    def register_connector(self, slug: str, connector_cls: type):
        """Register a connector class."""
        if slug in self.connectors:
            logger.warning(f"Connector {slug} already registered. Overwriting.")
        self.connectors[slug] = connector_cls
        logger.debug(f"Registered connector: {slug}")

    def get_connector(self, slug: str) -> type | None:
        return self.connectors.get(slug)

    def register_trigger(self, slug: str, trigger_handler):
        """Register a trigger handler."""
        self.triggers[slug] = trigger_handler

    def get_trigger(self, slug: str):
        return self.triggers.get(slug)

    def register_llm_provider(self, slug: str, provider_cls):
        self.llm_providers[slug] = provider_cls


# Global instance
registry = Registry()
