from __future__ import annotations

from automate_governance.common.errors import AutomateGovernanceError


class SecretsError(AutomateGovernanceError):
    pass


class SecretRefParseError(SecretsError):
    pass


class SecretBackendNotConfigured(SecretsError):
    pass


class SecretNotFound(SecretsError):
    pass


class SecretPermissionDenied(SecretsError):
    pass


class SecretBackendUnavailable(SecretsError):
    pass


class SecretDecryptionError(SecretsError):
    pass
