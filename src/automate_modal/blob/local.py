"""
Local Filesystem Blob Store.
Stores artifacts in MEDIA_ROOT/modal_artifacts/
"""

import uuid
from typing import Any

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from automate_modal.contracts import ArtifactRef, BlobStore


class LocalBlobStore(BlobStore):
    """Stores files locally using Django's default storage."""

    PREFIX = "blob://local/"

    def put_bytes(self, *, data: bytes, mime: str, filename: str, meta: dict) -> ArtifactRef:
        # Generate safe path
        # day paritioning: modal_artifacts/YYYY/MM/DD/uuid.ext
        # For simplicity: modal_artifacts/uuid/filename

        unique_id = uuid.uuid4()
        path = f"modal_artifacts/{unique_id}/{filename}"

        saved_path = default_storage.save(path, ContentFile(data))

        full_uri = f"{self.PREFIX}{saved_path}"

        return ArtifactRef(
            kind=meta.get("kind", "file"),
            uri=full_uri,
            mime=mime,
            size_bytes=len(data),
            sha256="",  # TODO: calculate
            meta=meta,
        )

    def open(self, uri: str) -> Any:
        if not uri.startswith(self.PREFIX):
            raise ValueError(f"Invalid URI scheme for LocalBlobStore: {uri}")

        path = uri[len(self.PREFIX) :]
        if not default_storage.exists(path):
            raise FileNotFoundError(f"Artifact not found: {path}")

        return default_storage.open(path)

    def generate_presigned_url(self, uri: str, expiration: int = 3600) -> str:
        # For local, we might return a simpler URL served by Django (if media served)
        # or just the path if internal.
        if not uri.startswith(self.PREFIX):
            raise ValueError(f"Invalid URI scheme: {uri}")

        path = uri[len(self.PREFIX) :]
        # Assuming MEDIA_URL is configured
        return f"{settings.MEDIA_URL}{path}"
