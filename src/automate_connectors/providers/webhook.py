import hashlib
import hmac
from typing import Any

from pydantic import BaseModel

from automate_connectors.base import ActionSpec, Connector, TriggerSpec
from automate_core.providers.base import ProviderContext
from automate_core.providers.errors import AutomateError, ErrorCodes
from automate_core.providers.schemas.base import SecretRef


class WebhookConfig(BaseModel):
    signing_secret: SecretRef | None = None
    verification_method: str = "hmac_sha256" # hmac_sha256, basic, none
    blacklist_hosts: list[str] = [] # SSRF

class WebhookConnector(Connector):
    key = "webhook"
    display_name = "Generic Webhook"

    def __init__(self, config: dict[str, Any], *, ctx: ProviderContext):
        self.ctx = ctx
        self.cfg = WebhookConfig(**config)

        self.secret = None
        if self.cfg.signing_secret:
            self.secret = self.cfg.signing_secret.ref
            if hasattr(self.ctx.secrets, 'resolve'):
                 self.secret = self.ctx.secrets.resolve(self.secret)

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return WebhookConfig

    @classmethod
    def capabilities(cls):
        # reuse base capability or define specific
        from automate_core.providers.base import CapabilitySpec
        return [CapabilitySpec(name="connector", modalities={"action", "trigger"})]

    @classmethod
    def actions(cls) -> list[ActionSpec]:
        return [
            ActionSpec(
                name="send",
                input_schema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "method": {"type": "string", "enum": ["POST", "GET", "PUT"]},
                        "payload": {"type": "object"},
                        "headers": {"type": "object"}
                    }
                },
                idempotent=False
            )
        ]

    @classmethod
    def triggers(cls) -> list[TriggerSpec]:
        return [TriggerSpec(name="generic_event", verification_method="dynamic")]

    def normalize_error(self, exc: Exception) -> Exception:
        return AutomateError(ErrorCodes.INTERNAL, str(exc), provider=self.key, original_exception=exc)

    def execute_action(self, action: str, input_data: dict[str, Any]) -> Any:
        if action == "send":
            return self._send_request(input_data)
        raise AutomateError(ErrorCodes.INVALID_ARGUMENT, f"Unknown action: {action}")

    def _send_request(self, data: dict[str, Any]):
        url = data.get("url")
        method = data.get("method", "POST")
        payload = data.get("payload")
        headers = data.get("headers", {})

        if not url:
            raise AutomateError(ErrorCodes.INVALID_ARGUMENT, "URL required")

        # Mock Outbound Request
        # In real impl, check SSRF against blacklist_hosts
        return {
            "status": 200,
            "body": "mocked_response",
            "sent_to": url
        }

    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> bool:
        method = self.cfg.verification_method

        if method == "none":
            return True

        if method == "hmac_sha256":
            if not self.secret:
                return False

            sig = headers.get("X-Signature") or headers.get("X-Hub-Signature-256")
            if not sig:
                return False

            expected = hmac.new(
                self.secret.encode('utf-8'),
                raw_body,
                hashlib.sha256
            ).hexdigest()

            # support "sha256=" prefix often used
            if sig.startswith("sha256="):
                expected = "sha256=" + expected

            return hmac.compare_digest(expected, sig)

        return False
