from __future__ import annotations

import os

from ..errors import SecretNotFound, SecretPermissionDenied
from ..interfaces import SecretsBackend
from ..refs import SecretRef


class EnvBackend(SecretsBackend):
    code = "env"

    def __init__(self, prefix: str = "AUTOMATE_SECRET__"):
        self._prefix = prefix

    def resolve(self, ref: SecretRef) -> str:
        # Example mapping: secretref://env/stripe/prod/api_key -> AUTOMATE_SECRET__stripe__prod__api_key
        key = self._prefix + ref.namespace.replace("/", "__") + "__" + ref.name
        val = os.environ.get(key)
        if val is None:
            raise SecretNotFound(f"Env secret not found: {key}")

        # Optional: add policy constraints here (e.g., namespace allowlist)
        if len(val) == 0:
            raise SecretPermissionDenied("Empty secret value is not allowed.")
        return val
