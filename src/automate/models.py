import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone

class TriggerTypeChoices(models.TextChoices):
    MODEL_SIGNAL = "model_signal", _("Model Signal")
    SCHEDULE = "schedule", _("Schedule")
    WEBHOOK = "webhook", _("Webhook")
    MANUAL = "manual", _("Manual")

class EventStatusChoices(models.TextChoices):
    NEW = "new", _("New")
    DISPATCHED = "dispatched", _("Dispatched")
    PROCESSING = "processing", _("Processing")
    DONE = "done", _("Done")
    FAILED = "failed", _("Failed")

class Automation(models.Model):
    """
    Defines an automation process.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    
    enabled = models.BooleanField(default=True)
    
    # Environment scope (dev, prod, etc) - simple for now
    environment = models.CharField(max_length=50, default="default")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class TriggerSpec(models.Model):
    """
    Configuration for what triggers an automation.
    """
    automation = models.ForeignKey(Automation, related_name="triggers", on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TriggerTypeChoices.choices)
    
    # Config specific to the trigger type (e.g. model name, cron schedule, etc)
    config = models.JSONField(default=dict)
    
    enabled = models.BooleanField(default=True)
    
    def clean(self):
        from .services.trigger import TriggerMatchingService
        TriggerMatchingService().validate_config(self)
        super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.type} -> {self.automation.name}"

class Rule(models.Model):
    """
    Conditions that must be met for an automation to proceed.
    Uses generic JSON logic (e.g. { "==": [ { "var": "event.source" }, "webhook" ] })
    """
    automation = models.ForeignKey(Automation, related_name="rules", on_delete=models.CASCADE)
    priority = models.IntegerField(default=0)
    
    # Condition logic in JSON format
    conditions = models.JSONField(default=dict)
    
    enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Rule {self.id} for {self.automation.name}"

class Event(models.Model):
    """
    An immutable record of something happening.
    Events are ingested, persisted, and then processed.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # The type of event (e.g. 'order.created', 'manual.trigger')
    event_type = models.CharField(max_length=255, db_index=True)
    
    # Schema version for the payload
    schema_version = models.IntegerField(default=1)
    
    # Source of the event (e.g. 'system', 'webhook', 'user')
    source = models.CharField(max_length=255)
    
    # The actual data
    payload = models.JSONField(default=dict)
    
    # Idempotency key to prevent duplicate processing
    idempotency_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    
    # Metadata: who/what caused this
    actor_id = models.CharField(max_length=255, null=True, blank=True)
    
    status = models.CharField(
        max_length=20, 
        choices=EventStatusChoices.choices, 
        default=EventStatusChoices.NEW,
        db_index=True
    )
    
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["idempotency_key"], name="unique_event_idempotency"),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.id})"

class ExecutionStatusChoices(models.TextChoices):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"

class Execution(models.Model):
    """
    State of a single run of an automation.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, related_name="executions", on_delete=models.CASCADE)
    automation = models.ForeignKey(Automation, related_name="executions", on_delete=models.CASCADE)
    
    # Snapshot of the workflow version used
    workflow_version = models.IntegerField(default=1)
    
    status = models.CharField(
        max_length=20,
        choices=ExecutionStatusChoices.choices,
        default=ExecutionStatusChoices.QUEUED
    )
    
    attempts = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3) # configurable per automation later
    
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    error_summary = models.TextField(blank=True)
    
    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(fields=["event", "automation", "workflow_version"], name="unique_execution_dispatch")
        ]

class ExecutionStep(models.Model):
    """
    Log of a single step within an execution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(Execution, related_name="steps", on_delete=models.CASCADE)
    
    step_id = models.CharField(max_length=255) # Reference to node in graph
    step_name = models.CharField(max_length=255)
    connector_slug = models.CharField(max_length=255)
    
    input_data = models.JSONField(default=dict) # Redacted inputs
    output_data = models.JSONField(default=dict) # Redacted outputs
    
    status = models.CharField(max_length=20, choices=ExecutionStatusChoices.choices)
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(null=True, blank=True)
    
    error_message = models.TextField(blank=True)

class LLMProvider(models.Model):
    slug = models.SlugField(max_length=50, unique=True, primary_key=True)
    name = models.CharField(max_length=100)
    base_url = models.URLField(blank=True, null=True)
    api_key_env_var = models.CharField(max_length=100, default="OPENAI_API_KEY")
    
    def __str__(self):
        return self.name

class LLMModelConfig(models.Model):
    provider = models.ForeignKey(LLMProvider, on_delete=models.CASCADE)
    name = models.CharField(max_length=100) # e.g. gpt-4
    is_default = models.BooleanField(default=False, db_index=True)
    
    # Default params
    temperature = models.FloatField(default=0.7)
    max_tokens = models.IntegerField(default=1000)
    
    @classmethod
    def get_default(cls):
        """Returns the default model config, or the first one if none marked default."""
        return cls.objects.filter(is_default=True).first() or cls.objects.first()
    
    def __str__(self):
        default_marker = " (default)" if self.is_default else ""
        return f"{self.provider.slug}/{self.name}{default_marker}"

class Prompt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class PromptVersion(models.Model):
    prompt = models.ForeignKey(Prompt, related_name="versions", on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    
    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("archived", "Archived"),
        ],
        default="draft"
    )
    
    system_template = models.TextField(blank=True)
    user_template = models.TextField()
    
    input_schema = models.JSONField(default=dict, blank=True)
    output_schema = models.JSONField(default=dict, blank=True)
    
    # P0: First-class model config
    default_model_config = models.ForeignKey(LLMModelConfig, null=True, blank=True, on_delete=models.SET_NULL, help_text="Default model to use for this prompt version")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("prompt", "version")
        ordering = ["-version"]

class Workflow(models.Model):
    """
    Defines the steps of an automation as a graph.
    """
    automation = models.ForeignKey(Automation, related_name="workflows", on_delete=models.CASCADE)
    version = models.IntegerField(default=1)
    
    # Graph definition: nodes, edges
    # {
    #   "nodes": [ { "id": "step1", "type": "slack", "config": {...}, "next": ["step2"] } ],
    #   "edges": []
    # }
    graph = models.JSONField(default=dict)
    
    is_live = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("automation", "version")
        ordering = ["-version"]

from .outbox import Outbox, OutboxStatusChoices
from .dlq import DeadLetter

class ConnectionProfile(models.Model):
    """
    Stores credentials and config for a connector, scoped by environment.
    Track D Requirement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    connector_slug = models.CharField(max_length=255)
    
    # Environment Scope
    environment = models.CharField(max_length=50, default="prod") 
    
    # Non-secret config
    config = models.JSONField(default=dict, blank=True)
    
    # Secrets (Encrypted in real world, suppressed in logs)
    encrypted_secrets = models.JSONField(default=dict, blank=True)
    
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.connector_slug})"

class PromptStatusChoices(models.TextChoices):
    DRAFT = "draft", "Draft"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"
    ARCHIVED = "archived", "Archived"

class PromptRelease(models.Model):
    """
    Map a specific PromptVersion to an Environment.
    Track E Requirement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    prompt_version = models.ForeignKey("PromptVersion", on_delete=models.CASCADE)
    environment = models.CharField(max_length=50, choices=[("dev", "Dev"), ("staging", "Staging"), ("prod", "Prod")])
    
    # P0: Environment-specific model override
    model_config = models.ForeignKey(LLMModelConfig, null=True, blank=True, on_delete=models.SET_NULL, help_text="Override model for this environment")
    
    deployed_at = models.DateTimeField(auto_now_add=True)
    deployed_by = models.CharField(max_length=255, null=True) # User reference
    
    class Meta:
        unique_together = ["prompt_version", "environment"]

class BudgetPolicy(models.Model):
    """
    Quota enforcement for LLM usage.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    
    scope = models.CharField(max_length=50, default="global") # global, user, automation
    
    # Limits
    max_tokens_per_day = models.IntegerField(default=100000)
    max_cost_per_day_usd = models.DecimalField(max_digits=10, decimal_places=4, default=10.00)
    
    current_usage_tokens = models.IntegerField(default=0)
    current_usage_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    
    reset_at = models.DateTimeField(default=timezone.now) 
    
    def __str__(self):
        return f"{self.name} (Policy)"


class Template(models.Model):
    """
    Reusable templates for messages (Slack Blocks, Emails, etc).
    Track C Requirement.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=[
        ("slack_blocks", "Slack Blocks (JSON)"),
        ("jinja", "Jinja2 Text"),
        ("json", "JSON Payload")
    ])
    
    # The actual template content
    content = models.TextField(help_text="Jinja2 supported. Use {{ event.payload.id }} etc.")
    
    # Schema for variables expected in this template (optional, for validation)
    input_schema = models.JSONField(default=dict, blank=True)
    
    version = models.IntegerField(default=1)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


# ============================================================================
# MCP Server Integration
# ============================================================================

class MCPAuthTypeChoices(models.TextChoices):
    NONE = "none", _("No Authentication")
    BEARER = "bearer", _("Bearer Token")
    API_KEY = "api_key", _("API Key Header")


class MCPServer(models.Model):
    """
    External MCP (Model Context Protocol) server registration.
    
    MCP servers expose tools that can be discovered and invoked by the chat assistant.
    This model stores the server configuration and caches discovered tools.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Display name for this MCP server")
    slug = models.SlugField(unique=True, help_text="Unique identifier (e.g., 'shopify-mcp')")
    
    # Connection
    endpoint_url = models.URLField(help_text="Base URL of the MCP server (e.g., http://localhost:3000)")
    
    # Authentication
    auth_type = models.CharField(
        max_length=20, 
        choices=MCPAuthTypeChoices.choices, 
        default=MCPAuthTypeChoices.NONE,
        help_text="How to authenticate with this server"
    )
    auth_secret_ref = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Secret reference (e.g., 'env:MCP_SHOPIFY_TOKEN' or raw token)"
    )
    auth_header_name = models.CharField(
        max_length=100,
        default="Authorization",
        help_text="Header name for API key auth (e.g., 'X-API-Key')"
    )
    
    # Status
    enabled = models.BooleanField(default=True, db_index=True)
    last_synced = models.DateTimeField(null=True, blank=True, help_text="Last time tools were synced")
    last_error = models.TextField(blank=True, help_text="Last sync error if any")
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "MCP Server"
        verbose_name_plural = "MCP Servers"
        ordering = ["name"]
    
    def __str__(self):
        status = "✓" if self.enabled else "✗"
        return f"{status} {self.name} ({self.slug})"


class MCPTool(models.Model):
    """
    Discovered tool from an MCP server.
    
    Tools are cached locally after discovery to avoid repeated API calls.
    Each tool has a name, description, and input schema.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    server = models.ForeignKey(MCPServer, on_delete=models.CASCADE, related_name="tools")
    
    # Tool definition (from MCP discovery)
    name = models.CharField(max_length=100, help_text="Tool function name")
    description = models.TextField(help_text="What this tool does")
    input_schema = models.JSONField(default=dict, help_text="JSON Schema for tool parameters")
    
    # Control
    enabled = models.BooleanField(default=True, db_index=True, help_text="Can disable specific tools")
    
    # Stats
    call_count = models.IntegerField(default=0, help_text="Number of times this tool was called")
    last_called = models.DateTimeField(null=True, blank=True)
    
    # Cache
    discovered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "MCP Tool"
        verbose_name_plural = "MCP Tools"
        unique_together = [["server", "name"]]
        ordering = ["server", "name"]
    
    def __str__(self):
        return f"{self.server.slug}/{self.name}"

