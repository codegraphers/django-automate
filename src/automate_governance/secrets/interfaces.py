from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping

from .refs import SecretRef


class SecretsBackend(ABC):
    """
    Pluggable secrets backend interface.

    IMPORTANT:
    - Backends may use network/IO; implement timeouts.
    - Backends must not log secret values.
    - Backends must raise typed SecretsError exceptions.
    """

    code: str  # e.g. "env", "encrypted_db", "vault", "cloudsecretmanager"

    @abstractmethod
    def resolve(self, ref: SecretRef) -> str:
        """Resolve the secret value for a SecretRef. Raises SecretsError on failure."""

    def healthcheck(self) -> Mapping[str, str]:
        """Optional diagnostics used by admin UI."""
        return {}

    def supports_versions(self) -> bool:
        """Whether backend can resolve explicit versions."""
        return False

    def rotate(self, namespace: str, name: str, *, new_value: str) -> str | None:
        """
        Optional rotation hook. Returns new version identifier if applicable.
        Most deployments will rotate via backend tooling; keep this optional.
        """
        return None
