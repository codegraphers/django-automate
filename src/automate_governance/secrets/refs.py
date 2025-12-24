from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, parse_qs

from .errors import SecretRefParseError


@dataclass(frozen=True)
class SecretRef:
    """
    SecretRef is the ONLY allowed way to reference secrets in workflow definitions,
    ConnectionProfiles, step configs, etc.

    Format:
        secretref://<backend>/<namespace>/<name>[?version=<v>]

    Examples:
        secretref://env/stripe/prod/api_key
        secretref://encrypted_db/openai/prod/key?version=3
    """
    backend: str
    namespace: str
    name: str
    version: Optional[str] = None

    @property
    def key(self) -> str:
        """Canonical key for caching (version-aware)."""
        return f"{self.backend}:{self.namespace}:{self.name}:{self.version or 'current'}"


def parse_secretref(value: str) -> SecretRef:
    if not isinstance(value, str) or not value:
        raise SecretRefParseError("SecretRef must be a non-empty string.")

    u = urlparse(value)
    if u.scheme != "secretref":
        raise SecretRefParseError(f"Invalid SecretRef scheme: {u.scheme!r}")

    backend = (u.netloc or "").strip()
    if not backend:
        raise SecretRefParseError("SecretRef missing backend (netloc).")

    parts = [p for p in u.path.split("/") if p]
    if len(parts) < 2:
        raise SecretRefParseError("SecretRef path must be /<namespace>/<name>.")

    namespace = "/".join(parts[:-1])
    name = parts[-1]

    qs = parse_qs(u.query or "")
    version = None
    if "version" in qs and qs["version"]:
        version = qs["version"][0]

    # Basic hardening (avoid weird traversal patterns)
    for seg in namespace.split("/") + [name]:
        if seg.startswith("__") or seg in (".", "..") or "\x00" in seg:
            raise SecretRefParseError("SecretRef contains disallowed path segments.")

    return SecretRef(backend=backend, namespace=namespace, name=name, version=version)
