import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# =============================================================================
# CORE SHIM LAYER (Area C Refactor)
# =============================================================================
# These models are now canonical in `src/automate_core`.
# We import them here to maintain backward compatibility for imports,
# but the database tables are now owned by `automate_core`.

from automate_core.models import (
    Automation,
    Workflow,
    Trigger,
    Trigger as TriggerSpec, # Alias
    TriggerTypeChoices,     # Enum
    RuleSpec as Rule,        # Alias
    Event,
    OutboxItem as Outbox,    # Alias
    Execution,
    StepRun as ExecutionStep,
    Artifact,
    Policy,
    # Enums
    ExecutionStatusChoices,
    OutboxStatusChoices
)

# Re-export choices if needed for compat (though explicit import is better)
# EventStatusChoices = Event.Status # If we implemented it that way
# For now, relying on consumers to update or use string values which match.

# =============================================================================
# LEGACY / FEATURE MODELS (To be moved to respective packages)
# =============================================================================

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

# Workflow moved to automate_core
# from automate_core.models import Workflow (already imported above)


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

