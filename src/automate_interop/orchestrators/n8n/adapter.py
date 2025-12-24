from __future__ import annotations
from typing import Any, Dict
import requests
import json
import logging
from ..contracts import ExternalOrchestrator, OrchestratorCapabilities, StartResult

logger = logging.getLogger(__name__)

class N8nAdapter(ExternalOrchestrator):
    def __init__(self, base_url: str, webhook_key: str):
        self.base_url = base_url.rstrip("/")
        self.webhook_key = webhook_key

    @property
    def capabilities(self) -> OrchestratorCapabilities:
        return OrchestratorCapabilities(
            webhook_start=True,
            callback_supported=True,
            status_poll_supported=False, # n8n API needed for this, assuming webhook only for now per spec
            supports_templates_host=True,
            supports_import_export=True
        )

    def start_run(self, request: Dict[str, Any]) -> StartResult:
        correlation_id = request.get("correlation_id")
        webhook_segment = request.get("webhook_segment", "default")
        
        # Construct Webhook URL (n8n convention: /webhook/<id>)
        # User config should provide the full ID or segment
        url = f"{self.base_url}/webhook/{webhook_segment}"
        
        payload = {
            "correlation_id": correlation_id,
            "callback_url": request.get("callback_url"),
            "data": request.get("payload")
        }

        try:
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code >= 400:
                return StartResult(
                    ok=False, 
                    error=f"n8n Webhook failed: {resp.status_code} {resp.text}",
                    meta={"status": resp.status_code}
                )
            
            # n8n "Respond to Webhook" might return data immediately
            return StartResult(ok=True, meta=resp.json() if resp.content else {})

        except Exception as e:
            logger.error(f"Failed to start n8n run: {e}")
            return StartResult(ok=False, error=str(e))

    def verify_callback(self, request_payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        # Check for bearer token or signature in headers
        # For MVP, we assume a shared secret token mechanism
        # In prod, implementing HMAC would be better
        # TODO: Retrieve expected token from Secrets
        return True # Stub
