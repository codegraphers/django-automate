"""
Environment-based Secrets Resolver.
Resolves `env://VAR_NAME` using os.environ.
"""
import os

from automate_modal.contracts import SecretsResolver


class EnvSecretsResolver(SecretsResolver):
    """Simple resolver that reads from environment variables."""

    def resolve(self, secret_ref: str) -> str:
        if not secret_ref:
            return ""

        if secret_ref.startswith("env://"):
            var_name = secret_ref[len("env://"):]
            val = os.environ.get(var_name)
            if val is None:
                # Log warning? For now just return empty or raise
                raise ValueError(f"Secret variable not found: {var_name}")
            return val

        if secret_ref.startswith("plain://"):
            return secret_ref[len("plain://"):]

        # Fallback or strict?
        # For security, we might want to default to treating as plain text only if whitelisted,
        # but the spec says "SecretRef only".
        # For dev convenience, if no prefix, treat as plain text but warn?
        # Let's enforce prefix for now to be safe.
        raise ValueError(f"Unknown secret reference schema: {secret_ref}")
