import hashlib
import json
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from automate_core.base.models import ValidatableMixin, SignalMixin


class Automation(ValidatableMixin, SignalMixin, models.Model):
    """
    Root entity for a defined automation process.
    Multi-tenant, versioned container.

    Inherits:
        ValidatableMixin: Provides validate_fields() hook
        SignalMixin: Provides pre_save_hook() and post_save_hook()

    Override Points:
        - validate_fields(): Add custom validation
        - pre_save_hook(): Run logic before save
        - post_save_hook(created): Run logic after save

    Configuration:
        Override class attributes to customize behavior.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.CharField(max_length=64, db_index=True)
    slug = models.SlugField(max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Configuration attributes (overrideable)
    slug_source_field = 'name'

    class Meta:
        unique_together = [("tenant_id", "slug")]
        indexes = [
            models.Index(fields=["tenant_id", "is_active"]),
        ]

    def __str__(self):
        return f"{self.slug} (v{self.workflows.count()})"

    def validate_fields(self):
        """Validate automation fields. Override to add custom validation."""
        errors = super().validate_fields()
        if self.name and len(self.name) < 2:
            errors['name'] = 'Name must be at least 2 characters'
        return errors

    def get_live_workflow(self):
        """Get the currently live workflow version."""
        return self.workflows.filter(is_live=True).first()

    def get_latest_workflow(self):
        """Get the latest workflow version."""
        return self.workflows.order_by('-version').first()


class Workflow(ValidatableMixin, models.Model):
    """
    Immutable version of an automation logic (DAG).

    Inherits:
        ValidatableMixin: Provides validate_fields() hook

    Override Points:
        - validate_graph(): Validate workflow graph structure
        - compute_hash(): Customize hash computation
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, related_name="workflows", on_delete=models.CASCADE)
    version = models.IntegerField(default=1)

    # Graphs
    graph = models.JSONField(default=dict)

    # Immutability
    hash = models.CharField(max_length=64, editable=False)

    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("automation", "version")
        ordering = ["-version"]

    def save(self, *args, **kwargs):
        if not self.hash:
            self.hash = self.compute_hash()
        super().save(*args, **kwargs)

    def compute_hash(self) -> str:
        """Compute deterministic hash of graph. Override to customize."""
        serialized = json.dumps(self.graph, sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()

    def validate_graph(self) -> dict:
        """Validate workflow graph structure. Override to customize."""
        errors = {}
        if not self.graph.get('nodes'):
            errors['graph'] = 'Graph must have at least one node'
        return errors

    def validate_fields(self):
        errors = super().validate_fields()
        errors.update(self.validate_graph())
        return errors

    def get_nodes(self) -> list:
        """Get workflow nodes."""
        return self.graph.get('nodes', [])

    def get_edges(self) -> list:
        """Get workflow edges."""
        return self.graph.get('edges', [])



class TriggerTypeChoices(models.TextChoices):
    MODEL_SIGNAL = "model_signal", _("Model Signal")
    WEBHOOK = "webhook", _("Webhook")
    SCHEDULE = "schedule", _("Schedule")
    MANUAL = "manual", _("Manual")
    EXTERNAL = "external", _("External")


class Trigger(ValidatableMixin, models.Model):
    """
    Configuration for what triggers an automation.
    Links an automation to event matching logic.

    Inherits:
        ValidatableMixin: Provides validate_fields() hook

    Override Points:
        - matches(event): Check if event matches this trigger
        - extract_payload(event): Extract payload from event
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    automation = models.ForeignKey(Automation, related_name="triggers", on_delete=models.CASCADE)

    type = models.CharField(max_length=50, choices=TriggerTypeChoices.choices, db_index=True)

    event_type = models.CharField(max_length=255, help_text="Event type pattern to match (e.g. order.*)")

    # Matching Logic
    filter_config = models.JSONField(default=dict, help_text="JSONLogic/filtering rules")

    priority = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["type", "event_type"]),
        ]

    def __str__(self):
        return f"{self.type}/{self.event_type} -> {self.automation.slug}"

    def matches(self, event) -> bool:
        """
        Check if event matches this trigger.
        Override to customize matching logic.
        """
        import fnmatch
        return fnmatch.fnmatch(event.event_type, self.event_type)

    def extract_payload(self, event) -> dict:
        """
        Extract payload from event for workflow execution.
        Override to customize payload extraction.
        """
        return event.payload
