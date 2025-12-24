from __future__ import annotations

from abc import ABC, abstractmethod


class KMS(ABC):
    """
    Minimal KMS interface for encrypted_db backend.

    DB-agnostic: ciphertext storage is bytes; encryption method is pluggable.
    """

    @abstractmethod
    def encrypt(self, plaintext: bytes) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes:
        raise NotImplementedError
