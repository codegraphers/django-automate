from __future__ import annotations

import base64
from django.core import signing

from .interfaces import KMS
from ..errors import SecretDecryptionError


class DjangoSigningKMS(KMS):
    """
    Simple KMS-like wrapper using Django signing.
    Use a dedicated key (AUTOMATE_KMS_KEY) and rotate with care.

    NOTE: This is not a replacement for HSM/KMS, but is a reasonable
    "for now" default for encrypted_db backend in many internal systems.
    """

    def __init__(self, secret: str, salt: str = "automate.secrets"):
        self._secret = secret
        self._salt = salt

    def encrypt(self, plaintext: bytes) -> bytes:
        token = signing.dumps(
            base64.b64encode(plaintext).decode("ascii"),
            key=self._secret,
            salt=self._salt,
        )
        return token.encode("utf-8")

    def decrypt(self, ciphertext: bytes) -> bytes:
        try:
            token = ciphertext.decode("utf-8")
            decoded = signing.loads(token, key=self._secret, salt=self._salt)
            return base64.b64decode(decoded.encode("ascii"))
        except Exception as e:
            raise SecretDecryptionError("Failed to decrypt secret.") from e
