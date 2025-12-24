from __future__ import annotations

import logging
from typing import Any

import requests

from ..adapters.base import ConnectorAdapter, ValidationResult
from ..errors import ConnectorError, ConnectorErrorCode
from ..types import ActionSpec, ConnectorCapabilities, ConnectorResult

logger = logging.getLogger(__name__)


class SlackAdapter(ConnectorAdapter):
    code = "slack"
    name = "Slack"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(supports_rate_limit_headers=True)

    @property
    def action_specs(self) -> dict[str, ActionSpec]:
        return {
            "send_message": ActionSpec(
                name="send_message",
                input_schema={
                    "type": "object",
                    "properties": {
                        "channel": {"type": "string"},
                        "message": {"type": "string"},
                        "blocks": {"type": "array"},
                    },
                    "required": ["channel"],
                },
                output_schema={"type": "object"},
            )
        }

    def validate_config(self, config: dict[str, Any]) -> ValidationResult:
        # Check if secrets/token are conceptually present (though passed in execution ctx usually)
        # Here we just validate structure if needed
        return ValidationResult(ok=True, errors=[])

    def execute(self, action: str, input_args: dict[str, Any], ctx: dict[str, Any]) -> ConnectorResult:
        if action != "send_message":
            raise ConnectorError(ConnectorErrorCode.INVALID_INPUT, f"Unknown action: {action}")

        # Extract secrets from profile in context
        profile = ctx.get("profile", {})
        secrets = profile.get("encrypted_secrets", {})  # Decrypted by Executor before passing?
        # Note: Executor logic usually passes *resolved* secrets.
        # Let's assume Profile contains resolved secrets for now or ctx has them.

        # fallback for dev/legacy patterns:
        token = secrets.get("token") or input_args.get("token")

        if not token:
            raise ConnectorError(ConnectorErrorCode.AUTH_FAILED, "Missing Slack token in profile")

        channel = input_args.get("channel")
        text = input_args.get("message")
        blocks = input_args.get("blocks")

        payload = {"channel": channel}
        if blocks:
            payload["blocks"] = blocks
            payload["text"] = text or "Notification"
        else:
            payload["text"] = text or ""

        try:
            resp = requests.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {token}"},
                json=payload,
                timeout=10,
            )

            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", 1)) * 1000
                raise ConnectorError(
                    ConnectorErrorCode.RATE_LIMITED,
                    "Slack Rate Limit",
                    retryable=True,
                    details_safe={"retry_after_ms": retry_after},
                )

            resp.raise_for_status()
            data = resp.json()

            if not data.get("ok"):
                raise ConnectorError(ConnectorErrorCode.UPSTREAM_5XX, f"Slack Logic Error: {data.get('error')}")

            return ConnectorResult(data=data)

        except Exception as e:
            raise self.normalize_error(e)

    def normalize_error(self, exc: Exception) -> ConnectorError:
        if isinstance(exc, ConnectorError):
            return exc
        return ConnectorError(ConnectorErrorCode.INTERNAL_ERROR, str(exc))
