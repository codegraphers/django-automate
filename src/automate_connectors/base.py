from abc import abstractmethod
from typing import Any

from pydantic import BaseModel

from automate_core.providers.base import BaseProvider, CapabilitySpec


class ActionSpec(BaseModel):
    name: str
    input_schema: dict[str, Any] | None = None # JSON Schema
    output_schema: dict[str, Any] | None = None
    idempotent: bool = False
    rate_limit_class: str | None = None

class TriggerSpec(BaseModel):
    name: str # e.g. "message_created"
    description: str = ""
    verification_method: str = "hmac" # hmac, basic, none
    payload_schema: dict[str, Any] | None = None

class Connector(BaseProvider):
    """
    Base class for all connectors.
    Extends BaseProvider to reuse registry and configuration logic.
    """

    @classmethod
    def capabilities(cls) -> list[CapabilitySpec]:
        # Connectors define capabilities via actions/triggers typically
        return [CapabilitySpec(name="connector", modalities={"action", "trigger"})]

    @classmethod
    @abstractmethod
    def actions(cls) -> list[ActionSpec]:
        """List of supported actions."""
        ...

    @classmethod
    @abstractmethod
    def triggers(cls) -> list[TriggerSpec]:
        """List of supported triggers/events."""
        ...

    @abstractmethod
    def execute_action(self, action: str, input_data: dict[str, Any]) -> Any:
        """Execute a named action."""
        ...

    @abstractmethod
    def verify_webhook(self, request_headers: dict[str, str], raw_body: bytes) -> bool:
        """Verify inbound webhook signature."""
        ...
