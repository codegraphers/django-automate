from __future__ import annotations

import hashlib
import hmac
from typing import Any

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from automate_governance.secrets.resolver import SecretResolver

from .emit import emit_event
from .specs import TriggerSpec


class WebhookIngestor:
    def __init__(self, secret_resolver: SecretResolver):
        self.secret_resolver = secret_resolver

    def process_request(self, request: HttpRequest, trigger: TriggerSpec) -> Any:
        # 1. Verify Signature
        self._verify_signature(request, trigger)

        # 2. Extract Payload
        try:
            payload = request.JSON
        except Exception:
            payload = {}  # or raw body if spec indicates

        # 3. Emit Event
        event_type = trigger.config.get("event_type", "webhook.received")

        return emit_event(
            tenant_id=trigger.tenant_id,
            event_type=event_type,
            source="webhook",
            payload=payload,
            trigger_id=trigger.id,
            idempotency_key=request.headers.get("X-Idempotency-Key"),
        )

    def _verify_signature(self, request: HttpRequest, trigger: TriggerSpec) -> None:
        secret_ref_str = trigger.config.get("signing_secret_ref")
        if not secret_ref_str:
            return  # No signature enforcement configured

        secret = self.secret_resolver.resolve_value(secret_ref_str)
        if not secret:
            # Scale-safe fail closed if secret missing
            raise PermissionDenied("Signing secret not resolved")

        signature = request.headers.get("X-Signature")  # Simplified common case
        if not signature:
            raise PermissionDenied("Missing signature header")

        # Example HMAC-SHA256
        expected = hmac.new(secret.encode(), request.body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise PermissionDenied("Invalid signature")
