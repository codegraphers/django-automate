from __future__ import annotations
from django.db import transaction

from ..interfaces import SecretsBackend
from ..refs import SecretRef
from ..errors import SecretNotFound
from ..kms.interfaces import KMS
from ..models import StoredSecret


class EncryptedDBBackend(SecretsBackend):
    code = "encrypted_db"

    def __init__(self, kms: KMS):
        self._kms = kms

    def supports_versions(self) -> bool:
        return True

    def resolve(self, ref: SecretRef) -> str:
        """
        DB-agnostic implementation:
        - Use normal queries.
        - Avoid assuming partial unique indexes.
        - Select current version unless explicit version provided.
        """
        qs = StoredSecret.objects.filter(namespace=ref.namespace, name=ref.name)
        if ref.version:
            qs = qs.filter(version=int(ref.version))
        else:
            qs = qs.filter(is_current=True)
        row = qs.first()

        if row is None:
            raise SecretNotFound(f"Stored secret not found: {ref.namespace}/{ref.name}")

        plaintext = self._kms.decrypt(row.ciphertext)
        return plaintext.decode("utf-8")

    def rotate(self, namespace: str, name: str, *, new_value: str) -> str:
        """
        Portable rotation approach:
        - Insert new version row
        - Flip is_current on previous rows inside a transaction
        - DB-specific partial unique index is an optimization only
        """
        with transaction.atomic():
            prev = StoredSecret.objects.filter(namespace=namespace, name=name, is_current=True)
            prev.update(is_current=False)
            
            # Simple max version check
            # In real concurrent system, might need better locking or retry, but this suffices for now
            max_ver_qs = StoredSecret.objects.filter(namespace=namespace, name=name).order_by("-version")
            last = max_ver_qs.first()
            new_ver = (last.version + 1) if last else 1
            
            ciphertext = self._kms.encrypt(new_value.encode("utf-8"))
            StoredSecret.objects.create(
                namespace=namespace, 
                name=name, 
                ciphertext=ciphertext, 
                version=new_ver, 
                is_current=True
            )
            return str(new_ver)
