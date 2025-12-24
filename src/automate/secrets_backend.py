import os
from abc import ABC, abstractmethod


class SecretsBackend(ABC):
    """
    Interface for resolving secrets securely.
    """
    @abstractmethod
    def resolve(self, key: str) -> str | None:
        pass

class EnvSecretsBackend(SecretsBackend):
    """
    Resolves secrets from Environment Variables.
    Format: env://VAR_NAME
    """
    def resolve(self, key: str) -> str | None:
        if not key:
            return None

        if key.startswith("env://"):
            var_name = key[6:]
            return os.environ.get(var_name)

        # P0.5: If strictly safe, we might reject raw values here too?
        # Or we assume ConnectionProfile content is trusted source, but we want indirection.
        # If key doesn't start with env://, treat as raw secret?
        # Requirement: "make it the only way to resolve secrets".
        # If we allow raw strings, it's fallback.
        # "Slack token must come from ConnectionProfile + backend resolution"
        # If ConnectionProfile holds "xoxb-123", we return "xoxb-123".
        # The insecurity comes from passing it in *Execution Inputs*.
        return key

class SecretsManager:
    _backend = EnvSecretsBackend()

    @classmethod
    def get_backend(cls) -> SecretsBackend:
        return cls._backend

    @classmethod
    def resolve(cls, value: str) -> str | None:
        return cls.get_backend().resolve(value)
