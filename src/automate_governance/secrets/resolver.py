from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

from .interfaces import SecretsBackend
from .refs import SecretRef, parse_secretref
from .errors import SecretBackendNotConfigured, SecretsError


@dataclass
class ResolvedSecret:
    value: str
    expires_at: float  # epoch seconds


class SecretResolver:
    """
    Central service for resolving SecretRefs.
    Connectors/executors should depend on this service, not on env vars or backend SDKs.

    Caching:
    - Cache is in-process only (safe default).
    - TTL is backend-configured.
    """

    def __init__(self, backends: Dict[str, SecretsBackend], *, fail_closed: bool = True, default_ttl: int = 30):
        self._backends = backends
        self._fail_closed = fail_closed
        self._default_ttl = default_ttl
        self._cache: Dict[str, ResolvedSecret] = {}

    def resolve_value(self, ref_or_str: str | SecretRef, *, ttl_seconds: Optional[int] = None) -> str:
        ref = ref_or_str if isinstance(ref_or_str, SecretRef) else parse_secretref(ref_or_str)
        backend = self._backends.get(ref.backend)
        if not backend:
            raise SecretBackendNotConfigured(f"Secrets backend not configured: {ref.backend}")

        now = time.time()
        cached = self._cache.get(ref.key)
        if cached and cached.expires_at > now:
            return cached.value

        try:
            value = backend.resolve(ref)
        except SecretsError:
            # Fail-closed recommended; callers can decide to catch and treat as "no match" in rare cases.
            if self._fail_closed:
                raise
            return ""

        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        self._cache[ref.key] = ResolvedSecret(value=value, expires_at=now + ttl)
        return value
