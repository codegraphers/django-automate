import hashlib
import hmac
import time
from typing import Any

from pydantic import BaseModel

from automate_connectors.base import ActionSpec, Connector, TriggerSpec
from automate_core.providers.base import ProviderContext
from automate_core.providers.errors import AutomateError, ErrorCodes
from automate_core.providers.schemas.base import SecretRef


class SlackConfig(BaseModel):
    bot_token: SecretRef
    signing_secret: SecretRef
    default_channel: str = "#general"

class SlackConnector(Connector):
    key = "slack"
    display_name = "Slack"

    def normalize_error(self, exc: Exception) -> Exception:
        # Simple mapping for now
        return AutomateError(ErrorCodes.INTERNAL, str(exc), provider=self.key, original_exception=exc)

    def __init__(self, config: dict[str, Any], *, ctx: ProviderContext):
        self.ctx = ctx
        self.cfg = SlackConfig(**config)

        # Resolve secrets
        self.token = self.cfg.bot_token.ref # mocked resolution
        if hasattr(self.ctx.secrets, 'resolve'):
             self.token = self.ctx.secrets.resolve(self.token)

        self.signing_secret = self.cfg.signing_secret.ref
        if hasattr(self.ctx.secrets, 'resolve'):
             self.signing_secret = self.ctx.secrets.resolve(self.signing_secret)

    @classmethod
    def config_schema(cls) -> type[BaseModel]:
        return SlackConfig

    @classmethod
    def actions(cls) -> list[ActionSpec]:
        return [
            ActionSpec(
                name="post_message",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "text": {"type": "string"},
                    },
                },
                idempotent=True
            )
        ]

    @classmethod
    def triggers(cls) -> list[TriggerSpec]:
        return [
            TriggerSpec(name="message_created", verification_method="hmac")
        ]

    def execute_action(self, action: str, input_data: dict[str, Any]) -> Any:
        if action == "post_message":
            return self._post_message(input_data)
        raise AutomateError(ErrorCodes.INVALID_ARGUMENT, f"Unknown action: {action}")

    def _post_message(self, data: dict[str, Any]):
        # Mock implementation of Slack API call
        # In real world: requests.post("https://slack.com/api/chat.postMessage", ...)
        channel = data.get("channel") or self.cfg.default_channel
        text = data.get("text")

        if not text:
            raise AutomateError(ErrorCodes.INVALID_ARGUMENT, "Text is required")

        # Simulating API call
        if self.token == "invalid":
            raise AutomateError(ErrorCodes.UNAUTHORIZED, "Invalid Slack Token")

        return {"ok": True, "channel": channel, "ts": "1234567890.123456"}

    def verify_webhook(self, headers: dict[str, str], raw_body: bytes) -> bool:
        # Slack signature verification
        timestamp = headers.get("X-Slack-Request-Timestamp")
        signature = headers.get("X-Slack-Signature")

        if not timestamp or not signature:
            return False

        # Check freshness (±5 min)
        if abs(time.time() - int(timestamp)) > 60 * 5:
            return False

        sig_basestring = f"v0:{timestamp}:{raw_body.decode('utf-8')}"

        my_signature = "v0=" + hmac.new(
            self.signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, signature)
