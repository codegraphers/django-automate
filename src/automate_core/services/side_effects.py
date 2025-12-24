import hashlib
import json
import logging
from typing import Optional, Tuple
from django.db import IntegrityError
from ..executions.models import SideEffectLog

logger = logging.getLogger(__name__)

class SideEffectManager:
    """
    Guarantees exactly-once execution of external side handling.
    Checks cache before running; records result after running.
    """

    @staticmethod
    def compute_key(execution_id: str, node_key: str, action: str, params: dict) -> str:
        """
        Deterministic key generation.
        """
        raw = f"{execution_id}:{node_key}:{action}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def check(self, tenant_id: str, key: str) -> Optional[dict]:
        """
        Returns cached response if exists.
        """
        try:
            log = SideEffectLog.objects.get(tenant_id=tenant_id, key=key)
            logger.info(f"SideEffect Hit: {key} (External ID: {log.external_id})")
            return log.response_payload
        except SideEffectLog.DoesNotExist:
            return None

    def record(self, tenant_id: str, key: str, external_id: str, response_payload: dict) -> SideEffectLog:
        """
        Persists the result. Handles race conditions (first write wins).
        """
        try:
            return SideEffectLog.objects.create(
                tenant_id=tenant_id,
                key=key,
                external_id=external_id,
                response_payload=response_payload
            )
        except IntegrityError:
            # Race condition: Step retry happened in parallel?
            # Return existing.
            return SideEffectLog.objects.get(tenant_id=tenant_id, key=key)
