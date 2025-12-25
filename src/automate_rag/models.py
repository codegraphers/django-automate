import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Corpus(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Policy / Config placeholders
    default_rag_policy_id = models.CharField(max_length=64, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Corpora"
        unique_together = [("tenant_id", "name")]

    def __str__(self):
        return f"{self.name} ({self.tenant_id})"

class SourceType(models.TextChoices):
    LOCAL_UPLOAD = "local_upload", _("Local Upload")
    ARTIFACT = "artifact", _("Artifact")
    URL = "url", _("URL Scrape")
    MICROSERVICE = "microservice", _("Microservice (BYO)")

class KnowledgeSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name="sources")

    type = models.CharField(max_length=50, choices=SourceType.choices)
    name = models.CharField(max_length=255)

    # Validated config schema (Pydantic based validation in service layer)
    config = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class DocumentStatus(models.TextChoices):
    NEW = "new", _("New")
    PARSED = "parsed", _("Parsed")
    CHUNKED = "chunked", _("Chunked")
    EMBEDDED = "embedded", _("Embedded")
    INDEXED = "indexed", _("Indexed")
    FAILED = "failed", _("Failed")

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name="documents")
    source = models.ForeignKey(KnowledgeSource, on_delete=models.SET_NULL, null=True, related_name="documents")

    external_ref = models.CharField(max_length=1024, blank=True, help_text="URL, File Path, ID")
    content_artifact_id = models.CharField(
        max_length=255, blank=True, help_text="Pointer to raw content in Artifact Store"
    )
    content_hash = models.CharField(max_length=64, blank=True, db_index=True)
    mime_type = models.CharField(max_length=100, blank=True)

    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.NEW
    )
    version = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant_id", "corpus", "status"]),
        ]

    def __str__(self):
        return f"Doc {self.id} ({self.status})"

class Chunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    corpus = models.ForeignKey(Corpus, on_delete=models.CASCADE, related_name="chunks")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")

    chunk_index = models.PositiveIntegerField()

    # Pointer to text content
    text_artifact_id = models.CharField(max_length=255, blank=True)

    # Redacted preview for admin UI/Debugging (not full content if sensitive)
    text_preview = models.CharField(max_length=512, blank=True)

    token_count = models.IntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True) # Page #, timestamps

    # If using DB-based vector storage (pgvector) in same DB
    # embedding = VectorField(dimensions=1536) # placeholder

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("document", "chunk_index")]
        ordering = ["chunk_index"]
