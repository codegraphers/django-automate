from __future__ import annotations

from ..interfaces import SecretsBackend
from ..refs import SecretRef
from ..errors import SecretBackendUnavailable, SecretNotFound


class VaultBackend(SecretsBackend):
    code = "vault"

    def __init__(self, url: str, token: str, timeout_seconds: int = 5):
        self._url = url
        self._token = token
        self._timeout = timeout_seconds

    def resolve(self, ref: SecretRef) -> str:
        """
        Skeleton: integrate with hvac or raw HTTP.
        Must implement:
        - strict timeouts
        - retries for transient errors (bounded)
        - typed exceptions
        """
        # TODO: call Vault API
        raise SecretBackendUnavailable("Vault backend not implemented yet.")

    def healthcheck(self):
        return {"url": self._url}
